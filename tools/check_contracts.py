"""Проверяет общие размеры мира, события и маршруты без генерации файлов."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:(ROOT/p).read_text()
config=json.loads(read('data/world/config.json'))
assert int(re.search(r'const WorldSize\s*=\s*(\d+)',read('backend/internal/domain/world/wrap.go'))[1])==config['size_tiles']
assert int(re.search(r'const ChunkSize\s*=\s*(\d+)',read('backend/internal/domain/world/coord.go'))[1])==config['chunk_size']
router=read('backend/internal/adapter/http/router.go')
routes={(m.lower(),p) for m,p in re.findall(r'mux.Handle(?:Func)?\("([A-Z]+) /api/v1([^" ]+)"',router) if p!='/realtime'}
spec=json.loads(read('backend/docs/swagger/openapi.json'))
documented={(m,p) for p,ops in spec['paths'].items() for m in ops if m in ['get','post','patch','delete','put']}
assert routes==documented, f'OpenAPI/routes differ: missing={routes-documented}, obsolete={documented-routes}'
assert 'AllianceEventType' in read('shared/events/world.ts') and 'ChatEventType' in read('shared/events/world.ts')
public=read('backend/internal/domain/player/profile.go').split('type PublicProfile struct',1)[1]
go_fields=set(re.findall(r'json:"([^",]+)',public))
ts=read('shared/player/profile.ts')
ts_fields=set(re.findall(r'^ (\w+)\??:',ts,re.M))
assert go_fields==ts_fields, f'Public profile fields differ: Go={go_fields}, TS={ts_fields}'
print(f'Contracts: {len(routes)} API operations; world dimensions and event unions agree')
