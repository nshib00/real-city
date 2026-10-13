#!/usr/bin/env python3
"""CLI orchestrator for spec-driven Real City Blender asset generation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TMP_DIR = Path("/tmp/real-city-blender-assets")
DEFAULT_BLENDER = "/mnt/d/programs/Blender/5.2/blender.exe"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.assets.blender.real_city import export
from tools.assets.blender.real_city.orchestrator import make_execution_brief
from tools.assets.blender.real_city.spec import AssetSpec, load_asset_spec
from tools.assets.update_asset_generation_status import update_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", help="Asset id, spec path, or docs/assets/specs-relative path")
    parser.add_argument("--mode", choices=("dry-run", "preview", "full", "repair"), default="preview")
    parser.add_argument("--levels", help="Comma-separated level list. Defaults to mode policy.")
    parser.add_argument("--states", help="Comma-separated state list. Defaults to mode policy.")
    parser.add_argument("--repair-target", action="append", choices=("png", "lod", "manifest", "report", "contact-sheet"))
    parser.add_argument("--force-full", action="store_true", help="Allow full generation without a passed preview report.")
    parser.add_argument("--blender", default=os.environ.get("BLENDER_BIN", DEFAULT_BLENDER), help="Blender executable")
    parser.add_argument("--no-status-update", action="store_true", help="Do not update docs/assets/asset-generation-status.md")
    parser.add_argument("--print-brief", action="store_true", help="Print the compact production brief")
    args = parser.parse_args()

    spec_path = resolve_spec(args.asset)
    spec = load_asset_spec(spec_path)
    mode = "dry-run" if args.mode == "dry-run" else args.mode
    levels = parse_csv_ints(args.levels)
    states = parse_csv(args.states)
    repair_targets = tuple(args.repair_target or ())

    plan = build_plan(spec, spec_path, mode=mode, levels=levels, states=states, repair_targets=repair_targets)
    if args.print_brief or mode == "dry-run":
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        print("\n--- production brief ---")
        print(make_execution_brief(spec, read_files=tuple(plan["read_files"]), skill_files=tuple(plan["skill_files"])))
    if mode == "dry-run":
        return 0

    if mode == "full" and not args.force_full:
        assert_preview_gate(spec)

    config_path, script_path = write_temp_files(plan)
    command = [args.blender, "--background", "--python", str(script_path)]
    print("RUN", " ".join(command))
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        return completed.returncode

    output_dir = ROOT / "frontend" / "public" / "assets" / "buildings" / spec.category / spec.asset_id
    report_path = output_dir / "orchestrator-report.json"
    if not report_path.exists():
        print(f"Missing orchestrator report: {report_path}", file=sys.stderr)
        return 1

    make_contact_sheet_if_needed(spec, mode, report_path)
    if not args.no_status_update:
        update_status(report_path)
    print(f"COMPLETE {report_path}")
    return 0


def resolve_spec(value: str) -> Path:
    raw = Path(value)
    candidates = []
    if raw.suffix:
        candidates.extend([raw, ROOT / raw])
    else:
        candidates.extend(sorted((ROOT / "docs" / "assets" / "specs").glob(f"**/{value}.yaml")))
        candidates.extend(sorted((ROOT / "docs" / "assets" / "specs").glob(f"**/{value}.yml")))
        candidates.extend(sorted((ROOT / "docs" / "assets" / "specs").glob(f"**/{value}.json")))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise SystemExit(f"Spec not found for asset: {value}")


def build_plan(
    spec: AssetSpec,
    spec_path: Path,
    *,
    mode: str,
    levels: tuple[int, ...] | None,
    states: tuple[str, ...] | None,
    repair_targets: tuple[str, ...],
) -> dict[str, Any]:
    selected_levels = levels or select_levels_for_mode(spec, mode)
    selected_states = states or tuple(spec.states)
    output_dir = ROOT / "frontend" / "public" / "assets" / "buildings" / spec.category / spec.asset_id
    touched = [
        str(spec_path.relative_to(ROOT)),
        str(output_dir.relative_to(ROOT) / "manifest.json"),
        str(output_dir.relative_to(ROOT) / "orchestrator-report.json"),
        str(output_dir.relative_to(ROOT) / f"{spec.asset_id}_{mode}_contact_sheet.png"),
        "docs/assets/asset-generation-status.md",
    ]
    for level in selected_levels:
        for state in selected_states:
            stem = f"{spec.asset_id}_l{level:02d}_{state}"
            touched.append(str(output_dir.relative_to(ROOT) / f"{stem}.png"))
            for lod in spec.lod_policy.get("chain", []):
                touched.append(str(output_dir.relative_to(ROOT) / f"{stem}_{lod.get('name')}.glb"))
    read_files = tuple(_existing_rel(path) for path in _spec_reference_paths(spec, spec_path))
    skill_files = tuple(f"skills/blender-skills/{name}/SKILL.md" for group in spec.skill_profile.values() for name in group)
    return {
        "asset_id": spec.asset_id,
        "spec_path": str(spec_path),
        "mode": mode,
        "levels": list(selected_levels),
        "states": list(selected_states),
        "repair_targets": list(repair_targets),
        "output_dir": str(output_dir.relative_to(ROOT)),
        "touched_files": touched,
        "read_files": list(read_files),
        "skill_files": list(skill_files),
    }


def write_temp_files(plan: dict[str, Any]) -> tuple[Path, Path]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    safe = f"{plan['asset_id']}_{plan['mode']}"
    config_path = TMP_DIR / f"{safe}.json"
    script_path = TMP_DIR / f"{safe}.py"
    config_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    script_path.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "import sys",
                f"ROOT = Path({str(ROOT)!r})",
                "sys.path.insert(0, str(ROOT))",
                "from tools.assets.blender.real_city.orchestrator import run_from_json",
                f"run_from_json({str(config_path)!r})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path, script_path


def make_contact_sheet_if_needed(spec: AssetSpec, mode: str, report_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    policy = spec.png_policy.get("contact_sheet") or {}
    if policy.get("enabled") is False:
        return
    output_dir = report_path.parent
    pngs = [ROOT / item["png"] for item in report.get("items", []) if item.get("png")]
    if not pngs:
        return
    sheet = output_dir / f"{spec.asset_id}_{mode}_contact_sheet.png"
    export.make_contact_sheet(pngs, sheet, columns=int(policy.get("columns", 4)))
    report.setdefault("outputs", {})["contact_sheet"] = str(sheet.relative_to(ROOT))
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def assert_preview_gate(spec: AssetSpec) -> None:
    report = ROOT / "frontend" / "public" / "assets" / "buildings" / spec.category / spec.asset_id / "orchestrator-report.json"
    if not report.exists():
        raise SystemExit("Full generation requires a passed preview first, or --force-full.")
    data = json.loads(report.read_text(encoding="utf-8"))
    if data.get("mode") != "preview" or data.get("preview_status") != "passed":
        raise SystemExit("Full generation requires last orchestrator report to be a passed preview, or --force-full.")


def select_levels_for_mode(spec: AssetSpec, mode: str) -> tuple[int, ...]:
    if mode == "preview":
        numbers = spec.level_numbers
        return tuple(dict.fromkeys((numbers[0], numbers[len(numbers) // 2], numbers[-1])))
    return spec.level_numbers


def parse_csv(value: str | None) -> tuple[str, ...] | None:
    if not value:
        return None
    return tuple(item.strip() for item in value.split(",") if item.strip())


def parse_csv_ints(value: str | None) -> tuple[int, ...] | None:
    parsed = parse_csv(value)
    return tuple(int(item) for item in parsed) if parsed else None


def _spec_reference_paths(spec: AssetSpec, spec_path: Path) -> list[Path]:
    paths = [spec_path]
    references = spec.references
    for key in ("docs", "art_guide", "existing_generators", "existing_assets"):
        values = references.get(key, [])
        if isinstance(values, str):
            values = [values]
        paths.extend(ROOT / value for value in values)
    return paths


def _existing_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except FileNotFoundError:
        return str(path)
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())

