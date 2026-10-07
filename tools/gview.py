"""Render a sliced plate from above out of the G-code itself (later layers paint over earlier ones)."""
import sys, re, zipfile
from PIL import Image, ImageDraw
def render(path, out, cols, box, scale=5, plate=1, flipy=True, layers=None):
    g=zipfile.ZipFile(path).read(f'Metadata/plate_{plate}.gcode').decode(errors='ignore')
    body=g[g.find('; CHANGE_LAYER'):]
    x0,y0,x1,y1=box; W=int((x1-x0)*scale); H=int((y1-y0)*scale)
    im=Image.new('RGB',(W,H),(235,235,235)); d=ImageDraw.Draw(im)
    tool=0; x=y=0.0; absE=True; layer=0
    for ln in body.split('\n'):
        if ln.startswith('; CHANGE_LAYER'): layer+=1
        if layers and layer not in layers: continue
        if not ln or ln[0]==';': continue
        c=ln.split(';')[0].split()
        if not c: continue
        if re.fullmatch(r'T\d+',c[0]):
            t=int(c[0][1:]); 
            if t<8: tool=t
            continue
        if c[0] in('G1','G0'):
            a={p[0]:p[1:] for p in c[1:] if len(p)>1}
            nx=float(a.get('X',x)); ny=float(a.get('Y',y))
            if c[0]=='G1' and 'E' in a and float(a['E'])>0 and 'X' in a and 'Y' in a and x0<=nx<=x1 and y0<=ny<=y1 and x0<=x<=x1 and y0<=y<=y1:
                p=lambda X,Y:((X-x0)*scale,(y1-Y)*scale)
                d.line([p(x,y),p(nx,ny)],fill=cols[tool],width=max(1,int(0.42*scale)))
            x,y=nx,ny
    im.save(out)
if __name__=='__main__':
    pass
