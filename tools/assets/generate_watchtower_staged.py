#!/usr/bin/env python3
"""Generate one watchtower state per Blender process to limit peak RAM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.assets.blender.real_city import export
from tools.assets.blender.real_city.spec import load_asset_spec
from tools.assets.generate_blender_asset import build_plan, write_temp_files


SPEC = ROOT / "docs/assets/specs/defense/tower.json"
ASSETS = ROOT / "frontend/public/assets/buildings/defense/tower"
STAGING = Path("/tmp/real-city-watchtower-staged")
STATES = ("construction", "active", "damaged", "ruined")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", default="/usr/bin/blender")
    parser.add_argument("--levels", default="1,2,3,4,5,6", help="Levels to generate or resume")
    parser.add_argument("--states", default=",".join(STATES), help="States to generate or resume")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds per variant")
    parser.add_argument("--dry-run", action="store_true", help="Print planned variants without Blender")
    parser.add_argument("--force", action="store_true", help="Rebuild even a complete matching stage")
    parser.add_argument("--min-available-mib", type=int, default=1536)
    parser.add_argument("--min-swap-free-mib", type=int, default=2048)
    args = parser.parse_args()
    spec = load_asset_spec(SPEC)
    requested = tuple(int(value) for value in args.levels.split(","))
    requested_states = tuple(args.states.split(","))
    if not requested or any(value not in range(1, 7) for value in requested):
        parser.error("levels must be in 1–6")
    if not requested_states or any(value not in STATES for value in requested_states):
        parser.error("states must be construction,active,damaged,ruined")
    if args.dry_run:
        for level in requested:
            for state in requested_states:
                print(f"tower_l{level:02d}_{state}")
        return 0
    STAGING.mkdir(parents=True, exist_ok=True)
    fingerprint = source_fingerprint(spec)

    for level in requested:
        for state in requested_states:
            stem = f"tower_l{level:02d}_{state}"
            if not args.force and stage_is_complete(stem, fingerprint):
                print(f"{stem}: already complete, skipped", flush=True)
                continue
            available, swap_free = memory_headroom_mib()
            if available < args.min_available_mib or swap_free < args.min_swap_free_mib:
                print(f"stopped before {stem}: available={available} MiB, swap_free={swap_free} MiB", flush=True)
                return 0
            plan = build_plan(spec, SPEC, mode="full", levels=(level,), states=(state,), repair_targets=())
            _, script = write_temp_files(plan)
            log_path = STAGING / f"{stem}.log"
            previous_manifest = (ASSETS / "manifest.json").read_bytes()
            previous_report = (ASSETS / "orchestrator-report.json").read_bytes()
            try:
                with log_path.open("w", encoding="utf-8") as log:
                    process = subprocess.Popen(
                        [args.blender, "--background", "--python", str(script)],
                        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    )
                    deadline = time.monotonic() + args.timeout
                    marker = "REAL_CITY_ASSET_ORCHESTRATOR_COMPLETE"
                    done = False
                    try:
                        while time.monotonic() < deadline:
                            if marker in log_path.read_text(encoding="utf-8", errors="replace"):
                                done = True
                                break
                            if process.poll() is not None:
                                break
                            time.sleep(1)
                    finally:
                        if process.poll() is None:
                            os.killpg(process.pid, signal.SIGTERM)
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                process.wait()
                    if not done:
                        raise RuntimeError(f"{stem} did not complete; inspect {log_path}")
                manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
                report = json.loads((ASSETS / "orchestrator-report.json").read_text(encoding="utf-8"))
                if [item["id"] for item in manifest.get("items", [])] != [stem]:
                    raise RuntimeError(f"{stem} manifest incomplete; inspect {log_path}")
                if [item["id"] for item in report.get("items", [])] != [stem]:
                    raise RuntimeError(f"{stem} report incomplete; inspect {log_path}")
                shutil.copy2(ASSETS / "tower_levels.blend", ASSETS / f"{stem}.blend")
                shutil.copy2(ASSETS / "tower_levels.glb", ASSETS / f"{stem}.glb")
                manifest["_watchtower_source_hash"] = fingerprint
                (STAGING / f"manifest_{stem}.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                (STAGING / f"report_{stem}.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                available, swap_free = memory_headroom_mib()
                print(f"{stem}: generated; available={available} MiB, swap_free={swap_free} MiB", flush=True)
            finally:
                (ASSETS / "manifest.json").write_bytes(previous_manifest)
                (ASSETS / "orchestrator-report.json").write_bytes(previous_report)

    stems = [f"tower_l{level:02d}_{state}" for level in range(1, 7) for state in STATES]
    missing = [stem for stem in stems if not stage_is_complete(stem, fingerprint)]
    if missing:
        print(f"Stages saved. Remaining variants: {missing}")
        return 0

    manifests = [json.loads((STAGING / f"manifest_{stem}.json").read_text(encoding="utf-8")) for stem in stems]
    reports = [json.loads((STAGING / f"report_{stem}.json").read_text(encoding="utf-8")) for stem in stems]
    manifest = manifests[0]
    manifest.pop("_watchtower_source_hash", None)
    manifest["levels"] = list(range(1, 7))
    manifest["states"] = list(STATES)
    manifest["items"] = [item for batch in manifests for item in batch["items"]]
    manifest["source_blend"] = None
    manifest["combined_glb"] = None
    manifest["source_blends"] = [f"frontend/public/assets/buildings/defense/tower/{stem}.blend" for stem in stems]
    manifest["combined_glbs"] = [f"frontend/public/assets/buildings/defense/tower/{stem}.glb" for stem in stems]
    report = reports[0]
    report["levels"] = list(range(1, 7))
    report["states"] = list(STATES)
    report["items"] = [item for batch in reports for item in batch["items"]]
    report["outputs"]["blend"] = None
    report["outputs"]["combined_glb"] = None
    report["outputs"]["source_blends"] = manifest["source_blends"]
    report["outputs"]["combined_glbs"] = manifest["combined_glbs"]
    pngs = [ROOT / item["png"] for item in manifest["items"]]
    sheet = ASSETS / "tower_full_contact_sheet.png"
    export.make_contact_sheet(pngs, sheet, columns=4)
    report["outputs"]["contact_sheet"] = str(sheet.relative_to(ROOT))
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ASSETS / "orchestrator-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ASSETS / "tower_levels.blend").unlink(missing_ok=True)
    (ASSETS / "tower_levels.glb").unlink(missing_ok=True)
    (ASSETS / "tower_levels.blend1").unlink(missing_ok=True)
    print("complete: 6 levels × 4 states, 24 PNG, 72 LOD GLB, 24 source blends")
    return 0


def stage_is_complete(stem: str, fingerprint: str) -> bool:
    manifest_path = STAGING / f"manifest_{stem}.json"
    report_path = STAGING / f"report_{stem}.json"
    if not manifest_path.is_file() or not report_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if manifest.get("_watchtower_source_hash") != fingerprint:
            return False
        if [item["id"] for item in manifest.get("items", [])] != [stem]:
            return False
        if [item["id"] for item in report.get("items", [])] != [stem]:
            return False
        item = manifest["items"][0]
        paths = [ASSETS / f"{stem}.blend", ASSETS / f"{stem}.glb", ROOT / item["png"]]
        paths.extend(ROOT / record["glb"] for record in item.get("lods", []))
        return len(item.get("lods", [])) == 3 and all(path.is_file() and path.stat().st_size > 1024 for path in paths)
    except (KeyError, ValueError, OSError):
        return False


def memory_headroom_mib() -> tuple[int, int]:
    lines = Path("/proc/meminfo").read_text(encoding="ascii").splitlines()
    values = {line.split(":", 1)[0]: int(line.split()[1]) // 1024 for line in lines}
    return values["MemAvailable"], values["SwapFree"]


def source_fingerprint(spec) -> str:
    # Narrative notes can change after export without changing model geometry.
    geometry_keys = ("asset_id", "category", "levels", "states", "footprint", "material_map", "lod_policy", "png_policy", "output")
    geometry_spec = {key: spec.raw.get(key) for key in geometry_keys}
    payload = json.dumps(geometry_spec, ensure_ascii=False, sort_keys=True).encode("utf-8")
    payload += (ROOT / "tools/assets/blender/real_city/components/watchtower.py").read_bytes()
    return hashlib.sha256(payload).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
