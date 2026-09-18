"""Validate terrain GLBs, sprite registration, and build visual QA sheets."""
import json
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw

from validate_early_housing import glb_document

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'frontend/public/assets/terrain/tiles'
NAMES=('grass','forest','forest_thinned','forest_sparse','water','mountain','road','oil_well','ruins')


def validate():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert set(manifest['tiles'])==set(NAMES)
    assert manifest['size']==[512,512] and manifest['anchor']==[256,320]
    assert manifest['footprint_pixels']==480
    sheet=Image.new('RGB',(768,840),'#25372f')
    draw=ImageDraw.Draw(sheet)
    results=[]
    with tarfile.open('/tmp/real-city-terrain-before.tar') as backup:
        for i,name in enumerate(NAMES):
            path=OUT/(name+'.png')
            if name not in ('road','forest_thinned','forest_sparse'):
                assert backup.extractfile(str(path.relative_to(ROOT))).read()!=path.read_bytes(),name
            with Image.open(path) as im:
                assert im.mode=='RGBA' and im.size==(512,512),name
                box=im.getchannel('A').getbbox()
                assert box and box[0]>0 and box[1]>0 and box[2]<512 and box[3]<512,(name,box)
                assert im.getpixel((256,320))[3]>240,name
                assert abs(box[0]-16)<=2 and abs(box[2]-496)<=2,(name,box)
                thumb=im.resize((256,256),Image.Resampling.LANCZOS)
                sheet.paste(thumb,((i%3)*256,(i//3)*280),thumb)
                draw.text(((i%3)*256+12,(i//3)*280+258),name,fill='white')
            doc=glb_document(OUT/(name+'.glb'))
            assert len(doc['scenes'])==1,name
            tris=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
            assert tris==manifest['tiles'][name]['triangles'] and tris<8000,name
            for node in doc['nodes']:
                assert node.get('translation',[0,0,0])==[0,0,0],name
                assert node.get('scale',[1,1,1])==[1,1,1],name
            results.append({'terrain':name,'triangles':tris,'alpha_bounds':box})
    assert (OUT/'terrain_tiles.blend').stat().st_size>1000
    roundtrip=json.loads((OUT/'roundtrip-validation.json').read_text())
    assert {entry['terrain'] for entry in roundtrip}==set(NAMES)
    assert all(entry['nonmanifold_edges']==0 for entry in roundtrip)
    sheet.save(OUT/'terrain_tiles_contact_sheet.png')
    (OUT/'validation.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'validated':len(results),'models':results}))


if __name__=='__main__':
    validate()
