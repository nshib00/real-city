"""Validate the nine late wooden-house variants and preserve early levels."""

import json
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw

from validate_early_housing import glb_document

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT/'frontend/src/assets/buildings/housing/wood_house'
SPRITES = ROOT/'frontend/public/assets/buildings/housing/wood_house'


def validate():
    report=json.loads((MODELS/'state-revision-report.json').read_text())
    sheet=Image.new('RGB',(768,642),'#24342c')
    draw=ImageDraw.Draw(sheet)
    results=[]
    with tarfile.open('/tmp/real-city-wood456-before.tar') as backup:
        for level in range(1,7):
            for col,state in enumerate(('active','construction','damaged')):
                name=f'wood_house_l{level:02d}_{state}'
                for path in (MODELS/(name+'.glb'),SPRITES/(name+'.png')):
                    old=backup.extractfile(str(path.relative_to(ROOT))).read()
                    assert (old==path.read_bytes()) == (level<=3),path
                if level<=3:
                    continue
                doc=glb_document(MODELS/(name+'.glb'))
                assert len(doc['scenes'])==1,name
                tris=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
                assert tris==report[name]['triangles'],name
                assert 1000<tris<13000,(name,tris)
                assert all(abs(v)<=1.8001 for corner in report[name]['bounds'] for v in corner[:2]),name
                for node in doc['nodes']:
                    assert node.get('translation',[0,0,0])==[0,0,0],name
                    assert node.get('scale',[1,1,1])==[1,1,1],name
                with Image.open(SPRITES/(name+'.png')) as image:
                    assert image.mode=='RGBA' and image.size==(512,384),name
                    box=image.getchannel('A').getbbox()
                    assert box and box[0]>0 and box[1]>0 and box[2]<512 and box[3]<384,(name,box)
                    thumb=image.resize((256,192),Image.Resampling.LANCZOS)
                    sheet.paste(thumb,(col*256,(level-4)*214),thumb)
                    draw.text((col*256+12,(level-4)*214+194),name,fill='white')
                results.append({'name':name,'triangles':tris,'alpha_bounds':box})
    sheet.save(SPRITES/'levels-456-review.png')
    (SPRITES/'levels-456-validation.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'validated':len(results),'preserved_early_files':18,'models':results}))


if __name__=='__main__':
    validate()
