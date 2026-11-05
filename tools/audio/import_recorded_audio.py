"""Импорт записанных CC0 звуков из .cache/audio-sources в игровой каталог."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / '.cache/audio-sources'
EXTRACTED = SOURCES / 'extracted'
PUBLIC = ROOT / 'frontend/public/assets/audio'
MASTERS = ROOT / 'tools/audio/master'
MANIFEST = ROOT / 'frontend/src/audio/soundManifest.ts'
SOURCE_OVERRIDES = ROOT / 'tools/audio/source-overrides.json'
FFMPEG = ROOT / '.cache/audio-deps/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'


def files(directory: str, pattern: str) -> list[Path]:
    result = sorted((EXTRACTED / directory).glob(pattern))
    if not result:
        raise FileNotFoundError(f'{directory}/{pattern}')
    return result


POOLS = {
    'click': files('more', 'Paper & Stationery/Stationery_1[679].wav') + files('more', 'Paper & Stationery/Stationery_23.wav'),
    'paper': files('owlish', 'Paper/page*.wav') + files('more', 'Paper & Stationery/Stationery_0[1345].wav'),
    'cloth': files('more', 'Cloth/*.wav') + files('owlish', 'Cloth, Rustle/*movement*.wav'),
    'coin': files('more', 'Money/Money_0[2589].wav') + files('more', 'Money/Money_1[45].wav') + files('more', 'Money/Money_2[579].wav'),
    'bell': files('rubberduck', 'bell_*.ogg') + files('workshop', 'workshop/*ping*.wav'),
    'wood': files('workshop', 'workshop/*wood clap*.wav') + files('workshop', 'workshop/*wood on wood*.wav') + files('rubberduck', 'wooden_*.ogg'),
    'stone': files('workshop', 'workshop/*wood on concrete.wav') + files('rubberduck', 'hit_*.ogg'),
    'metal': files('workshop', 'workshop/*clink*.wav') + files('workshop', 'workshop/*metal tapping.wav') + files('rubberduck', 'metal_*.ogg'),
    'heavy': files('workshop', 'workshop/*thuds.wav') + files('workshop', 'workshop/*metal drop*.wav') + files('owlish', 'Impacts/clamour*.wav'),
    'tool': files('workshop', 'workshop/*hammering*.wav') + files('workshop', 'workshop/*ratchet*.wav'),
    'glass': files('rubberduck', 'glass_*.ogg') + files('workshop', 'workshop/*dull ping*.wav'),
    'soft': files('owlish', 'Impacts/fruit*.wav') + files('owlish', 'Impacts/djembe*.wav'),
    'breath': files('owlish', 'Human/breath*.wav') + files('owlish', 'Human/gasp*.wav') + files('owlish', 'Human/freakedbreath.wav'),
    'step': files('owlish', 'Footsteps/g*footstep*.wav') + files('owlish', 'Footsteps/hard-footstep*.wav'),
    'water': files('owlish', 'Water/tap-water*.wav') + files('rubberduck', 'splash_*.ogg'),
    'machine': files('workshop', 'workshop/*machine.wav') + files('workshop', 'workshop/*drill short*.wav'),
}


def pool_for(sound_id: str) -> str:
    if sound_id.startswith('ui.'):
        if any(x in sound_id for x in ('confirm', 'toast.info')): return 'bell'
        if any(x in sound_id for x in ('warning', 'error', 'invalid', 'insufficient')): return 'metal'
        if any(x in sound_id for x in ('panel', 'dialog', 'cancel')): return 'paper'
        if 'building' in sound_id: return 'wood'
        if 'monster' in sound_id: return 'soft'
        return 'click'
    if sound_id.startswith('economy.'):
        if any(x in sound_id for x in ('coin', 'market', 'treasury')): return 'coin'
        if any(x in sound_id for x in ('rare', 'crystal', 'level.up')): return 'glass'
        if any(x in sound_id for x in ('ready', 'respawned', 'claimed')): return 'bell'
        if any(x in sound_id for x in ('wood', 'resin')): return 'wood'
        if any(x in sound_id for x in ('ore', 'stone')): return 'metal'
        if any(x in sound_id for x in ('oil', 'clay', 'sand', 'mushroom')): return 'soft'
        if any(x in sound_id for x in ('storage', 'production.started')): return 'tool'
        return 'cloth'
    if sound_id.startswith('build.'):
        if any(x in sound_id for x in ('completed', 'repaired')): return 'bell'
        if any(x in sound_id for x in ('damaged', 'demolished')): return 'heavy'
        if 'wall' in sound_id: return 'stone'
        if any(x in sound_id for x in ('repair', 'upgrade', 'rushed')): return 'tool'
        return 'wood'
    if sound_id.startswith('world.'):
        if 'forest.cut' in sound_id: return 'wood'
        if 'forest.explore' in sound_id: return 'cloth'
        if any(x in sound_id for x in ('discovered', 'captured', 'claimed')): return 'bell'
        return 'stone'
    if sound_id.startswith('social.'):
        if any(x in sound_id for x in ('accepted', 'mention')): return 'bell'
        if 'treasury' in sound_id: return 'coin'
        return 'paper'
    if sound_id.startswith('combat.'):
        if 'step' in sound_id: return 'step'
        if any(x in sound_id for x in ('aggro', 'idle', 'retreat')): return 'breath'
        if any(x in sound_id for x in ('storm_coil', 'ember_wisp')): return 'glass'
        if any(x in sound_id for x in ('cannon', 'colossus', 'brute', 'heavy', 'building_attack')): return 'heavy'
        if any(x in sound_id for x in ('wood', 'stakes', 'bolt_thrower')): return 'wood'
        if any(x in sound_id for x in ('stone', 'guardian', 'tower', 'automaton')): return 'metal'
        if any(x in sound_id for x in ('loot', 'victory')): return 'coin'
        if any(x in sound_id for x in ('flesh', 'hit', 'death', 'spore')): return 'soft'
        return 'tool'
    raise ValueError(sound_id)


def render(source: Path, output: Path, *, seconds: float, offset: float = 0, ambient: bool = False) -> None:
    fade = 0.35 if ambient else 0.025
    filters = []
    if not ambient:
        filters.append('silenceremove=start_periods=1:start_duration=0:start_threshold=-48dB')
    filters += [f'atrim=start=0:duration={seconds}', 'asetpts=PTS-STARTPTS',
                f'afade=t=in:st=0:d={0.12 if ambient else 0.005}',
                f'afade=t=out:st={max(0, seconds-fade)}:d={fade}',
                'highpass=f=35', 'loudnorm=I=-25:TP=-3:LRA=9', 'alimiter=limit=0.70:level=0']
    command = [str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y']
    if offset: command += ['-ss', str(offset)]
    command += ['-i', str(source), '-af', ','.join(filters), '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(output)]
    subprocess.run(command, check=True)


def main() -> None:
    from validate_audio import validate_wav
    manifest = json.loads(MANIFEST.read_text().split('// DATA:', 1)[1].splitlines()[0])
    overrides = json.loads(SOURCE_OVERRIDES.read_text())['sounds'] if SOURCE_OVERRIDES.exists() else {}
    provenance = {}
    ambience = {
        'grass': ('park-wind.wav', 8), 'forest': ('park-birds.wav', 12),
        'river': ('park-river.wav', 9), 'mountain': ('park-wind.wav', 33),
        'ruins': ('park-wind.wav', 51), 'town': ('park-birds.wav', 41),
        'workshop': (None, 0), 'field': ('park-birds.wav', 69),
        'oil_well': (None, 0),
    }
    for sound_id, variants in manifest.items():
        family = sound_id.split('.')[0]
        provenance[sound_id] = []
        for index in range(len(variants)):
            override = overrides.get(sound_id)
            if override:
                selection = override[index % len(override)]
                source = ROOT / 'tools/audio/sources' / selection['source']
                offset = float(selection.get('offset', 0))
                seconds = float(selection.get('duration', 1.35 if family == 'combat' else 0.95))
                ambient = False
            elif family == 'ambience':
                name, offset = ambience[sound_id.split('.')[1]]
                source = SOURCES / name if name else POOLS['machine'][index % len(POOLS['machine'])]
                seconds = 6 if name is None else 8
                ambient = True
            else:
                pool = POOLS[pool_for(sound_id)]
                position = int(hashlib.sha256(sound_id.encode()).hexdigest()[:8], 16) % len(pool)
                source = pool[(position + index) % len(pool)]
                seconds = 1.35 if family == 'combat' else 0.95 if family in ('build', 'world') else 0.7
                offset = 0
                ambient = False
            master = MASTERS / f'{sound_id}.{index}.wav'
            target = PUBLIC / family / f'{sound_id}.{index}.mp3'
            render(source, master, seconds=seconds, offset=offset, ambient=ambient)
            validate_wav(master, maximum=10 if ambient else 2)
            subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(master),
                            '-ar', '48000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '48k' if ambient else '64k', str(target)], check=True)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()[:12]
            variants[index] = f'/assets/audio/{family}/{target.name}?v={digest}'
            provenance[sound_id].append(str(source.relative_to(ROOT)))
    data = json.dumps(dict(sorted(manifest.items())), ensure_ascii=False, separators=(',', ':'))
    MANIFEST.write_text("import type { SoundId } from './soundEvents'\n\n/** Записанные источники: tools/audio/recorded-sources.json. */\n"
                        f'// DATA:{data}\nexport const soundManifest: Partial<Record<SoundId, readonly string[]>> = {data}\n')
    (ROOT / 'tools/audio/recorded-sources.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    music_dir = PUBLIC / 'music'
    music_dir.mkdir(exist_ok=True)
    subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(SOURCES / 'sunset-walk.ogg'),
                    '-c:a', 'libmp3lame', '-b:a', '96k', str(music_dir / 'sunset-walk.mp3')], check=True)
    print(f'Импортировано {len(manifest)} событий, {sum(map(len, manifest.values()))} вариантов и музыка.')


if __name__ == '__main__': main()
