"""Обновляет snapshot и runtime OpenAPI по реальным маршрутам; требует gofmt."""
import json
import re
import subprocess
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
router=(ROOT/'backend/internal/adapter/http/router.go').read_text()
path=ROOT/'backend/docs/swagger/openapi.json'
spec=json.loads(path.read_text())
routes={(m.lower(),p) for m,p in re.findall(r'mux.Handle(?:Func)?\("([A-Z]+) /api/v1([^" ]+)"',router) if p!='/realtime'}
paths={}
for method,p in sorted(routes):
    paths.setdefault(p,{})[method]=spec['paths'].get(p,{}).get(method,{'summary':method.upper()+' '+p})
spec['paths']=paths
path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
risky={('/buildings','post'),('/buildings/{id}/weapons','post'),('/combat/monsters','post'),('/alliances/invites','post'),('/market/orders','post'),('/alliances/treasury/spend','post')}
lines=['"paths": map[string]any{']
for p,ops in paths.items():
    operations=[]
    for method,op in ops.items():
        helper='idempotentOperation' if (p,method) in risky else 'operation'
        operations.append(json.dumps(method)+':'+helper+'('+json.dumps(op['summary'],ensure_ascii=False)+')')
    lines.append(json.dumps(p)+':map[string]any{'+','.join(operations)+'},')
lines+=['},']
go=ROOT/'backend/internal/adapter/http/openapi.go'
source=go.read_text();start=source.index('"paths": map[string]any{') if '"paths": map[string]any{' in source else source.index('"paths":')
end=source.index('"components":',start)
go.write_text(source[:start]+'\n'.join(lines)+'\n'+source[end:])
if shutil.which('gofmt'):
    subprocess.run(['gofmt','-w',str(go)],check=True)
elif shutil.which('swag'):
    formatted = subprocess.run(['swag','fmt','--pipe'], input=go.read_text(), text=True, capture_output=True, check=True)
    go.write_text(formatted.stdout)
else:
    raise SystemExit('Install gofmt or swag to format generated Go code')
