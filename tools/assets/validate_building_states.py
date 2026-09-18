"""Check every revised building state against exported geometry and its backup."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw

from validate_early_housing import glb_document

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = {
    "dugout": ("housing/dugout",5,False),
    "wood_house": ("housing/wood_house",6,False),
    "town_hall": ("center/town_hall",10,False),
    "lumber_yard": ("industry/lumber_yard",13,True),
}


def validate(backup=None):
    archive=tarfile.open(backup) if backup else None
    results=[]; retained=0
    output=ROOT/'frontend/public/assets/buildings'
    for kind,(folder,count,public) in FAMILIES.items():
        model_dir=ROOT/('frontend/public/assets/buildings' if public else 'frontend/src/assets/buildings')/folder
        report_name='generation-report.json' if kind=='lumber_yard' else 'state-revision-report.json'
        report=json.loads((model_dir/report_name).read_text())
        expected=count*3 if kind=='lumber_yard' else count*2+(4 if kind=='dugout' else 0)
        assert len(report)==expected,(kind,len(report))
        sheet=Image.new('RGB',(768,count*214),'#24342c')
        draw=ImageDraw.Draw(sheet)
        for level in range(1,count+1):
            for col,state in enumerate(('active','construction','damaged')):
                name=f'{kind}_l{level:02d}_{state}'
                png=output/folder/(name+'.png')
                glb=model_dir/(name+'.glb')
                changed=state!='active' or (kind=='dugout' and level>=2)
                with Image.open(png) as image:
                    assert image.mode=='RGBA' and image.size==(512,384),name
                    box=image.getchannel('A').getbbox()
                    assert box,name
                    if changed:
                        assert box[0]>0 and box[1]>0 and box[2]<512 and box[3]<384,(name,box)
                    thumb=image.resize((256,192),Image.Resampling.LANCZOS)
                    sheet.paste(thumb,(col*256,(level-1)*214),thumb)
                    draw.text((col*256+12,(level-1)*214+194),name,fill='white')
                if changed:
                    doc=glb_document(glb)
                    assert len(doc['scenes'])==1,name
                    tris=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
                    assert tris==report[name]['triangles'],(name,tris,report[name]['triangles'])
                    assert tris>100,name
                    for node in doc['nodes']:
                        assert node.get('translation',[0,0,0])==[0,0,0],name
                        assert node.get('scale',[1,1,1])==[1,1,1],name
                    if state!='active':
                        assert report[name]['structural_edits']>4,name
                    results.append({'name':name,'triangles':tris,'alpha_bounds':box})
                if archive:
                    for path in (png,glb):
                        old=archive.extractfile(str(path.relative_to(ROOT))).read()
                        same=hashlib.sha256(old).digest()==hashlib.sha256(path.read_bytes()).digest()
                        assert same != changed,(name,path,'unexpected preservation/change')
                        retained+=int(same)
        sheet.save(output/folder/'state-review.png')
        source=model_dir/(kind+'_levels.blend')
        assert source.stat().st_size>1000
        glb_document(model_dir/(kind+'_levels.glb'))
    if archive: archive.close()
    assert len(results)==48,len(results)
    summary={'revised_models':len(results),'unchanged_active_files':retained if backup else None,'models':results}
    (output/'state-validation.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({'revised_models':len(results),'unchanged_active_files':retained if backup else None}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--backup',type=Path)
    validate(parser.parse_args().backup)
