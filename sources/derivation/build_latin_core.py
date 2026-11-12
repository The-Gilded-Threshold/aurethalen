"""Build the unpublished Aetheris Display Latin Core release candidate."""
from pathlib import Path
import sys,copy,json,math,unicodedata as ud,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools_lib'));sys.path.insert(0,str(ROOT/'release_tools'))
import numpy as np
import cv2
import pathops
from ufoLib2 import Font
from ufoLib2.objects import Anchor
from fontTools.svgLib.path import parse_path
from fontTools.pens.recordingPen import RecordingPen,DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.basePen import BasePen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.filterPen import FilterPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont,newTable
from fontTools.ufoLib import UFOWriter
from fontTools.agl import UV2AGL
from ufo2ft import compileTTF

OUT=ROOT/'release-candidate-1';INPUT=ROOT
if (ROOT/'inputs').exists():OUT=ROOT.parent;INPUT=ROOT/'inputs'
(OUT/'qa').mkdir(parents=True,exist_ok=True)
ufo=Font.open(INPUT/'punctuation-v0.3/AetherisDisplay.ufo')
oldfont=TTFont(INPUT/'punctuation-v0.3/AetherisDisplay-Regular.ttf')
cmap=dict(oldfont.getBestCmap());oldnames=sorted(ufo.keys());oldwidths={n:ufo[n].width for n in oldnames}
core=set(int(l.split()[0],16) for l in (OUT/'sources/GF_Latin_Core.nam').read_text().splitlines() if l.startswith('0x'))
recipes={};first={n:n for n in oldnames};last=first.copy();carets={};marks={};case_marks={}
meta=json.loads((INPUT/'refined-v0.2/outline-metadata.json').read_text())
bodymeta={r['character']:r for r in meta['records']}
def gname(cp):return cmap.get(cp,UV2AGL.get(cp,f'uni{cp:04X}'))
def bounds(name):
    pen=BoundsPen(ufo);ufo[name].draw(pen);return pen.bounds or (0,0,0,0)
def recording(name):
    p=DecomposingRecordingPen(ufo);ufo[name].draw(p);return cleaned(p)
def native(rec):
    out=RecordingPen()
    for op,args in rec.value:
        if op in ('moveTo','lineTo','curveTo','qCurveTo'):
            args=tuple(tuple(float(v) for v in p) if p is not None else None for p in args)
        getattr(out,op)(*args)
    return out
def cleaned(rec):
    path=pathops.Path();rec.replay(path.getPen());path.simplify(fix_winding=True,clockwise=True)
    out=RecordingPen();path.draw(out);return native(out)
def add(name,width,rec=None,codepoint=None,components=None,inherit=None,clean=True):
    if name in ufo:del ufo[name]
    g=ufo.newGlyph(name);g.width=float(width)
    if codepoint is not None:g.unicodes=[codepoint];cmap[codepoint]=name
    if rec is not None:(cleaned(rec) if clean else native(rec)).replay(g.getPen())
    if components:
        pen=g.getPointPen()
        for base,matrix in components:pen.addComponent(base,tuple(float(v) for v in matrix))
    if inherit:
        first[name]=first.get(inherit[0],inherit[0]);last[name]=last.get(inherit[-1],inherit[-1])
    recipes[name]=dict(codepoint=f'U+{codepoint:04X}' if codepoint is not None else None,width=width,components=components,inherit=inherit)
    return g
class FlatPen(BasePen):
    def __init__(self):super().__init__(None);self.points=[]
    def _moveTo(self,p):self.points=[tuple(p)]
    def _lineTo(self,p):
        a=np.array(self.points[-1]);b=np.array(p);n=max(1,math.ceil(np.linalg.norm(b-a)/8))
        self.points.extend(tuple(a+(b-a)*t) for t in np.linspace(0,1,n+1)[1:])
    def _curveToOne(self,b,c,d):
        a=np.array(self.points[-1]);b,c,d=map(np.array,[b,c,d])
        self.points.extend(tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d) for t in np.linspace(0,1,35)[1:])
    def _closePath(self):pass
def path(d):
    p=RecordingPen();parse_path(d,p);parts=[];part=[]
    for item in p.value:
        part.append(item)
        if item[0]=='closePath':parts.append(part);part=[]
    arrays=[]
    for part in parts:
        r=RecordingPen();r.value=part;fp=FlatPen();r.replay(fp);arrays.append(np.array(fp.points,dtype='float32'))
    out=RecordingPen()
    for i,(part,pts) in enumerate(zip(parts,arrays)):
        depth=sum(cv2.pointPolygonTest(other,tuple(map(float,pts[0])),False)>0 for j,other in enumerate(arrays) if j!=i)
        signed=float(np.sum(pts[:,0]*np.roll(pts[:,1],-1)-pts[:,1]*np.roll(pts[:,0],-1)))
        r=RecordingPen();r.value=part;r.replay(out if (signed<0)==(depth%2==0) else ReverseContourPen(out))
    return out
def merged(parts):
    p=RecordingPen()
    for name,matrix in parts:recording(name).replay(TransformPen(p,matrix))
    return p
def poly(points):return 'M'+' L'.join(f'{x},{y}' for x,y in points)+' Z'
def rect(x0,y0,x1,y1):return poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
def dia(x,y,s):return poly([(x,y+s/2),(x+s/2,y),(x,y-s/2),(x-s/2,y)])
def ellipse(cx,cy,rx,ry):
    k=.5522847498
    return f'M{cx+rx},{cy} C{cx+rx},{cy+k*ry} {cx+k*rx},{cy+ry} {cx},{cy+ry} C{cx-k*rx},{cy+ry} {cx-rx},{cy+k*ry} {cx-rx},{cy} C{cx-rx},{cy-k*ry} {cx-k*rx},{cy-ry} {cx},{cy-ry} C{cx+k*rx},{cy-ry} {cx+rx},{cy-k*ry} {cx+rx},{cy} Z'
def componentchar(c,transform=(1,0,0,1,0,0)):return (cmap[ord(c)],transform)
I=(1,0,0,1,0,0)
def boundary_points(name):
    points=[];part=[]
    for item in recording(name).value:
        part.append(item)
        if item[0]=='closePath':
            r=RecordingPen();r.value=part;fp=FlatPen();r.replay(fp);points.extend(fp.points);part=[]
    return np.array(points)

# Soft-dotted alternatives retain the exact original stem and serif contours.
for c,cp in [('i',0x131),('j',0x237)]:
    src=recording(cmap[ord(c)]);pieces=[];piece=[]
    for item in src.value:
        piece.append(item)
        if item[0]=='closePath':pieces.append(piece);piece=[]
    out=RecordingPen()
    for piece in pieces:
        r=RecordingPen();r.value=piece;bp=BoundsPen(None);r.replay(bp)
        if bp.bounds[1]<450:r.replay(out)
    add(gname(cp),ufo[cmap[ord(c)]].width,out,cp,inherit=[cmap[ord(c)]],clean=False)

# Diacritics have a separate, slightly wider/flatter capital treatment.
accentpaths={
0x300:poly([(-97,151),(-35,157),(60,20),(37,3)]),
0x301:poly([(-65,16),(25,157),(91,151),(-39,2)]),
0x302:poly([(-132,9),(-20,151),(20,151),(132,9),(105,-2),(0,105),(-105,-2)]),
0x303:'M-147,22 C-104,104 -46,111 18,72 C74,38 107,39 143,90 L156,79 C115,0 58,-7 -8,32 C-67,66 -101,62 -134,12 Z',
0x304:poly([(-139,31),(128,31),(144,61),(-125,61)]),
0x306:'M-132,135 C-103,63 -65,29 0,29 C65,29 103,63 132,135 L113,144 C74,87 44,72 0,72 C-44,72 -74,87 -113,144 Z',
0x307:dia(0,68,66),
0x308:dia(-79,68,61)+' '+dia(79,68,61),
0x30A:ellipse(0,84,77,77)+' '+ellipse(0,84,43,49),
0x30B:poly([(-133,11),(-57,151),(-5,151),(-111,0)])+' '+poly([(-12,11),(64,151),(116,151),(10,0)]),
0x30C:poly([(-132,143),(-105,155),(0,48),(105,155),(132,143),(20,1),(-20,1)]),
0x326:'M-14,-45 C24,-40 48,-66 35,-100 C27,-126 1,-148 -35,-167 L-43,-155 C-19,-133 -8,-117 -8,-99 C-39,-100 -49,-78 -39,-60 C-34,-51 -25,-46 -14,-45 Z',
0x327:'M-8,7 L24,4 L-1,-45 C79,-42 108,-86 82,-130 C62,-167 4,-175 -61,-147 L-53,-128 C-12,-144 21,-136 32,-116 C46,-91 21,-69 -37,-77 L-49,-64 Z',
0x328:'M-10,9 L27,4 C-58,-50 -76,-108 -28,-130 C-4,-142 24,-136 48,-119 L60,-139 C23,-172 -32,-176 -66,-145 C-111,-100 -70,-33 -10,9 Z',
}
marknames={0x300:'gravecomb',0x301:'acutecomb',0x302:'circumflexcomb',0x303:'tildecomb',0x304:'macroncomb',0x306:'brevecomb',0x307:'dotaccentcomb',0x308:'dieresiscomb',0x30A:'ringcomb',0x30B:'hungarumlautcomb',0x30C:'caroncomb',0x326:'commaaccentcomb',0x327:'cedillacomb',0x328:'ogonekcomb'}
for cp,d in accentpaths.items():
    name=marknames[cp];g=add(name,0,path(d),cp)
    anchor='ogonek' if cp==0x328 else 'bottom' if cp in (0x326,0x327) else 'top'
    bb=bounds(name);g.anchors=[Anchor(0,0,'_'+anchor),Anchor(0,float(bb[3]+45) if anchor=='top' else float(bb[1]-35),anchor)]
    marks[cp]=name
    if anchor=='top':
        r=RecordingPen();recording(name).replay(TransformPen(r,(1.08,0,0,.78,0,0)))
        cg=add(name+'.case',0,r);cg.anchors=[Anchor(0,0,'_top'),Anchor(0,float(bounds(name+'.case')[3]+40),'top')];case_marks[cp]=name+'.case'
add('caroncomb.alt',0,path(poly([(0,0),(22,140),(66,144),(30,-7)])))
ufo['caroncomb.alt'].anchors=[Anchor(0,0,'_side')]
r=RecordingPen();recording(marks[0x326]).replay(TransformPen(r,(1,0,0,-1,0,0)))
g=add('commaaccentcomb.above',0,r);g.anchors=[Anchor(0,0,'_top')]

# Standalone accents use the same drawings with nonzero advance widths.
spacing={0xA8:0x308,0xAF:0x304,0xB4:0x301,0xB8:0x327,0x2C6:0x302,0x2C7:0x30C,0x2D8:0x306,0x2D9:0x307,0x2DA:0x30A,0x2DB:0x328,0x2DC:0x303,0x2DD:0x30B}
for cp,markcp in spacing.items():
    if cp in cmap:continue
    add(gname(cp),390,codepoint=cp,components=[(marks[markcp],(1,0,0,1,195,0 if markcp in (0x327,0x328) else 570))])

# Script-specific letters derived from the source forms, not substitute fonts.
special={0xC6:('A','E',.64,.9,535,1050),0xE6:('a','e',.9,.93,315,710),0x152:('O','E',.82,.9,505,1035),0x153:('o','e',.87,.95,303,710)}
for cp,(a,b,sx,tx,shift,width) in special.items():
    add(gname(cp),width,merged([componentchar(a,(sx,0,0,1,0,0)),componentchar(b,(tx,0,0,1,shift,0))]),cp,inherit=[cmap[ord(a)],cmap[ord(b)]])
for c,cp in [('O',0xD8),('o',0xF8)]:
    base=cmap[ord(c)];bb=bounds(base);r=merged([(base,I)])
    lo,bot,hi,top=bb;x1=lo+20;x2=hi-20;y1=bot-35;y2=top+35
    path(poly([(x1-15,y1),(x1+16,y1),(x2+15,y2),(x2-16,y2)])).replay(r)
    add(gname(cp),ufo[base].width,r,cp,inherit=[base])
for c,cp,y in [('D',0xD0,352),('D',0x110,352),('d',0x111,505),('H',0x126,520),('h',0x127,515),('L',0x141,340),('l',0x142,350)]:
    base=cmap[ord(c)];r=merged([(base,I)]);bb=bounds(base)
    if c in 'Ll':d=poly([(-5,y-70),(min(ufo[base].width,350),y+85),(min(ufo[base].width,350),y+116),(-5,y-39)])
    else:d=rect(-10,y,min(ufo[base].width,470),y+26)
    path(d).replay(r);add(gname(cp),ufo[base].width,r,cp,inherit=[base])
# Thorn combines the established long stem and bowl at a lowered height.
for cp,cap in [(0xDE,True),(0xFE,False)]:
    stem=cmap[ord('I' if cap else 'l')];bowl=cmap[ord('P' if cap else 'p')]
    r=merged([(stem,I),(bowl,(.92 if cap else 1,0,0,.72 if cap else 1,0,40 if cap else 0))])
    add(gname(cp),max(ufo[bowl].width,440),r,cp,inherit=[bowl])
# Eth has an o-shaped bowl, angled ascender and a fine crossing stroke.
r=merged([componentchar('o')]);path('M155,590 C253,638 369,621 426,531 C487,435 489,291 451,171 L398,174 C432,303 424,452 366,536 C323,600 244,614 164,576 Z '+poly([(168,486),(433,614),(449,587),(184,458)])).replay(r)
add(gname(0xF0),510,r,0xF0,inherit=[cmap[ord('d')]])
# A long-stemmed sharp s and its capital companion share the font's bowl contrast.
sharp='M62,0 L62,493 C62,641 135,716 261,716 C365,716 423,661 417,581 C413,526 379,490 329,466 C423,431 477,362 475,260 C472,103 383,-6 229,-6 L216,26 C328,37 390,112 391,248 C392,365 340,434 249,447 L249,476 C307,487 339,527 340,582 C341,649 308,687 257,687 C186,687 148,626 148,505 L148,0 Z'
add(gname(0xDF),530,path(sharp),0xDF,inherit=[cmap[ord('f')],cmap[ord('s')]])
r=RecordingPen();recording(gname(0xDF)).replay(TransformPen(r,(1.12,0,0,1,5,0)))
add(gname(0x1E9E),610,r,0x1E9E,inherit=[cmap[ord('B')]])
for cp,c in [(0xAA,'a'),(0xBA,'o')]:
    add(gname(cp),320,codepoint=cp,components=[componentchar(c,(.63,0,0,.63,30,395))])

# Anchors are centered on letter bodies, excluding long swash overhangs.
def base_anchor(c,name):
    x0,y0,x1,y1=bounds(name)
    if c in bodymeta:
        m=bodymeta[c];sx=m['scale_units_per_pixel'];left,right=m['body_source_x'];sourceleft=m['source_window_px'][0]
        center=((left+right)/2-sourceleft)*sx-m['font_x_origin'];edge=(right-sourceleft)*sx-m['font_x_origin']
    else:center=ufo[name].width/2;edge=min(x1,ufo[name].width-20)
    # Use the core at center to keep accents above a W's body, not its high exit.
    rec=recording(name);points=[p for op,args in rec.value for p in args if isinstance(p,tuple) and len(p)==2]
    local=[p[1] for p in points if abs(p[0]-center)<170 and p[1]>250]
    top=max(local) if local else y1
    top=max(440 if c.islower() else 700,top)+48
    return float(center),float(top),float(edge-32)
anchors={}
for cp,name in list(cmap.items()):
    c=chr(cp)
    if ud.category(c).startswith('L'):
        ref=gname(0x131) if c=='i' else gname(0x237) if c=='j' else name
        x,y,ogonek=base_anchor(c,ref)
        topbb=bounds(name);sideX=max((p[0] for op,args in recording(name).value for p in args if isinstance(p,tuple) and len(p)==2 and p[1]>topbb[3]-150),default=topbb[2])+30
        # Snap the attached ogonek to the actual foot outline, rather than
        # leaving its hook floating next to an upturned swash terminal.
        foot=boundary_points(name);foot=foot[(foot[:,1]>-65)&(foot[:,1]<70)]
        if len(foot):
            target=foot[np.argmin(((foot[:,0]-ogonek)/100)**2+(foot[:,1]/45)**2)]
            ogonek_anchor=(float(target[0]+10),float(target[1]-4))
        else:ogonek_anchor=(ogonek,0)
        anchors[name]=dict(top=(x,y),bottom=(x,0),ogonek=ogonek_anchor,side=(float(sideX),float(topbb[3]-140)))
        ufo[name].anchors=[Anchor(float(v[0]),float(v[1]),k) for k,v in anchors[name].items()]

compositions=[]
for cp in sorted(core):
    if cp in cmap:continue
    c=chr(cp);decomp=ud.decomposition(c).split()
    if len(decomp)!=2 or decomp[0].startswith('<'):raise RuntimeError(f'Unhandled Core character {cp:04X}')
    bc,mc=map(lambda s:int(s,16),decomp);base=cmap[bc];mark=marks[mc]
    if bc==ord('i') and mc not in (0x326,0x327,0x328):base=gname(0x131)
    if bc==ord('j') and mc not in (0x326,0x327,0x328):base=gname(0x237)
    anchor='ogonek' if mc==0x328 else 'bottom' if mc in (0x326,0x327) else 'top'
    if chr(bc).isupper() and mc in case_marks:mark=case_marks[mc]
    if cp in (0x13D,0x13E,0x10F,0x165):mark='caroncomb.alt';anchor='side'
    if cp==0x123:mark='commaaccentcomb.above';anchor='top'
    if cp in (0x122,0x136,0x137,0x13B,0x13C,0x145,0x146):mark=marks[0x326]
    ax,ay=anchors[base][anchor];width=ufo[base].width
    if anchor=='side':width=max(width,ax+bounds(mark)[2]+35)
    name=gname(cp);g=add(name,width,codepoint=cp,components=[(base,I),(mark,(1,0,0,1,ax,ay))],inherit=[base])
    data=copy.deepcopy(anchors[base])
    if anchor=='top':data['top']=(ax,ay+bounds(mark)[3]+45)
    if anchor in ('bottom','ogonek'):data['bottom']=(ax,ay+bounds(mark)[1]-35)
    anchors[name]=data;g.anchors=[Anchor(float(v[0]),float(v[1]),k) for k,v in data.items()]
    compositions.append((bc,mc,cp))
# Keep iogonek soft-dotted in longer decomposed mark sequences.
name='iogonek.dotless';base=gname(0x131);ax,ay=anchors[base]['ogonek']
add(name,ufo[base].width,components=[(base,I),(marks[0x328],(1,0,0,1,ax,ay))],inherit=[base])
anchors[name]=copy.deepcopy(anchors[gname(0x12F)]);ufo[name].anchors=[Anchor(float(v[0]),float(v[1]),k) for k,v in anchors[name].items()]

# Additional practical symbols and the remaining printable Latin-1 characters.
add(gname(0xA4),640,path(ellipse(320,350,181,181)+' '+ellipse(320,350,138,138)+' '+poly([(92,597),(129,625),(242,493),(210,466)])+' '+poly([(509,625),(547,597),(432,466),(400,494)])+' '+poly([(92,103),(129,75),(242,207),(210,234)])+' '+poly([(509,75),(547,103),(432,234),(400,206)])),0xA4)
add(gname(0xA6),190,path(rect(81,-160,109,220)+' '+rect(81,380,109,760)),0xA6)
add(gname(0xAC),630,path(poly([(55,370),(575,370),(575,139),(542,139),(542,337),(55,337)])),0xAC)
cmap[0xAD]=cmap[ord('-')]
# Micro uses the established u with a tapered descending left stem.
r=merged([componentchar('u')]);path('M32,200 L100,200 L100,-176 L42,-225 L32,-225 Z').replay(r)
add(gname(0xB5),ufo[cmap[ord('u')]].width,r,0xB5,inherit=[cmap[ord('u')]])
for digit in '0123456789':
    base=cmap[ord(digit)];width=round(ufo[base].width*.59+30)
    for suffix,y in [('super',390),('sub',-155),('numr',350),('dnom',0)]:
        name=f'{UV2AGL[ord(digit)]}.{suffix}';add(name,width,components=[(base,(.59,0,0,.59,15,y))])
        cp=({'0':0x2070,'1':0xB9,'2':0xB2,'3':0xB3}.get(digit) if suffix=='super' else None)
        if suffix=='super' and digit in '456789':cp=0x2070+int(digit)
        if suffix=='sub':cp=0x2080+int(digit)
        if cp is not None:ufo[name].unicodes=[cp];cmap[cp]=name
fractions={0xBC:('1','4'),0xBD:('1','2'),0xBE:('3','4'),0x2153:('1','3'),0x2154:('2','3'),0x215B:('1','8'),0x215C:('3','8'),0x215D:('5','8'),0x215E:('7','8')}
add('fraction.rule',240,path(poly([(0,-25),(283,735),(308,735),(25,-25)])))
for cp,(a,b) in fractions.items():
    add(gname(cp),730,codepoint=cp,components=[(f'{UV2AGL[ord(a)]}.numr',(1,0,0,1,0,0)),('fraction.rule',(1,0,0,1,200,0)),(f'{UV2AGL[ord(b)]}.dnom',(1,0,0,1,410,0))])
dagger=poly([(180,-120),(180,388),(45,388),(45,419),(180,419),(180,662),(211,708),(242,662),(242,419),(377,419),(377,388),(242,388),(242,-120)])
add(gname(0x2020),425,path(dagger),0x2020)
r=path(dagger);path(rect(45,180,377,211)).replay(r);add(gname(0x2021),425,r,0x2021)
add(gname(0x2030),1040,merged([componentchar('%'),componentchar('o',(.51,0,0,.68,743,-10))]),0x2030)
add(gname(0x2116),1120,merged([componentchar('N'),componentchar('o',(.57,0,0,.57,779,410))]),0x2116)
for cp,points in [(0x2192,[(20,285),(610,285),(464,161),(486,141),(704,300),(486,459),(464,439),(610,315),(20,315)]),(0x2190,[(704,285),(114,285),(260,161),(238,141),(20,300),(238,459),(260,439),(114,315),(704,315)])]:
    add(gname(cp),745,path(poly(points)),cp)
for cp,rotation in [(0x2191,(0,1,-1,0,670,-40)),(0x2193,(0,-1,1,0,70,710))]:
    r=RecordingPen();recording(gname(0x2192)).replay(TransformPen(r,rotation));add(gname(cp),745,r,cp)
check=poly([(35,283),(105,332),(263,135),(599,706),(631,692),(276,19),(239,11)])
add(gname(0x2713),700,path(check),0x2713)
# A dotted circle makes unattached combining marks visible to shaping engines.
r=RecordingPen()
for j in range(16):
    a=2*math.pi*j/16;path(dia(300+220*math.cos(a),260+220*math.sin(a),34)).replay(r)
g=add(gname(0x25CC),620,r,0x25CC);g.anchors=[Anchor(300,530,'top'),Anchor(300,-10,'bottom'),Anchor(480,0,'ogonek')]

# Shared crossbars make the f ligatures drawn forms rather than spaced strings.
ligs={'ff':'f_f','fi':'f_i','fl':'f_l','ffi':'f_f_i','ffl':'f_f_l'}
for chars,name in ligs.items():
    positions=[0]
    for a,b in zip(chars,chars[1:]):positions.append(positions[-1]+(273 if a==b=='f' else 285))
    parts=[componentchar(c,(1,0,0,1,float(x),0)) for c,x in zip(chars,positions)]
    r=merged(parts)
    # A fine horizontal link unifies the neighboring stems and crossbars.
    for x in positions[1:]:path(rect(125,422,x+135,441)).replay(r)
    width=positions[-1]+ufo[cmap[ord(chars[-1])]].width
    g=add(name,width,r,inherit=[cmap[ord(chars[0])],cmap[ord(chars[-1])]])
    carets[name]=positions[1:];g.anchors=[Anchor(float(x),0,f'caret_{i+1}') for i,x in enumerate(positions[1:])]
    for i,(c,x) in enumerate(zip(chars,positions)):
        base=cmap[ord(c)]
        for kind in ['top','bottom','ogonek']:
            ax,ay=anchors[base][kind];g.anchors.append(Anchor(float(ax+x),float(ay),f'{kind}_{i+1}'))
    for cp,target in [(0xFB00,'ff'),(0xFB01,'fi'),(0xFB02,'fl'),(0xFB03,'ffi'),(0xFB04,'ffl')]:
        if target==chars:g.unicodes=[cp];cmap[cp]=name

# Tabular figures preserve each digit's source shape and use an equal advance.
tabwidth=math.ceil(max(max(ufo[cmap[ord(c)]].width,bounds(cmap[ord(c)])[2]-bounds(cmap[ord(c)])[0]) for c in '0123456789')/10)*10+40
for c in '0123456789':
    base=cmap[ord(c)];add(base+'.tnum',tabwidth,components=[(base,(1,0,0,1,(tabwidth-ufo[base].width)/2,0))])

# Feature source. Original pairs are extended by first/last-side inheritance.
header='languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nlanguagesystem latn ROM;\nlanguagesystem latn TRK;\nlanguagesystem latn AZE;\n'
tops=[marks[cp] for cp in case_marks];cases=[case_marks[cp] for cp in case_marks]
capital=[name for cp,name in cmap.items() if chr(cp).isupper() and ud.category(chr(cp)).startswith('L')]
features=header+'@TopMarks = ['+' '.join(tops)+'];\n@CaseMarks = ['+' '.join(cases)+'];\n@AllTopMarks = [@TopMarks @CaseMarks commaaccentcomb.above];\n@CapitalBases = ['+' '.join(dict.fromkeys(capital))+'];\n'
features+='feature ccmp {\n lookup ComposeAccents {\n'
for bc,mc,cp in compositions:features+=f' sub {cmap[bc]} {marks[mc]} by {cmap[cp]};\n'
features+=' } ComposeAccents;\n lookup SoftDots {\n lookupflag UseMarkFilteringSet @AllTopMarks;\n'
features+=f' sub {cmap[ord("i")]}\' @AllTopMarks by {gname(0x131)};\n sub {cmap[ord("j")]}\' @AllTopMarks by {gname(0x237)};\n sub {gname(0x12F)}\' @AllTopMarks by iogonek.dotless;\n }} SoftDots;\n sub @CapitalBases @TopMarks\' by @CaseMarks;\n}} ccmp;\n'
features+='feature locl {\n script latn; language ROM;\n'+f' sub {gname(0x15E)} by {gname(0x218)};\n sub {gname(0x15F)} by {gname(0x219)};\n}} locl;\n'
features+='feature liga {\n lookupflag IgnoreMarks;\n'
for chars in ['ffi','ffl','ff','fi','fl']:features+=' sub '+' '.join(cmap[ord(c)] for c in chars)+' by '+ligs[chars]+';\n'
features+='} liga;\n'
features+='feature tnum {\n'+''.join(f' sub {cmap[ord(c)]} by {cmap[ord(c)]}.tnum;\n' for c in '0123456789')+'} tnum;\n'
for feature,suffix in [('sups','super'),('subs','sub'),('numr','numr'),('dnom','dnom')]:
    features+=f'feature {feature} {{\n'+''.join(f' sub {cmap[ord(c)]} by {UV2AGL[ord(c)]}.{suffix};\n' for c in '0123456789')+f'}} {feature};\n'
features+='feature frac {\n'+''.join(f' sub {cmap[ord(a)]} {cmap[ord("/")]} {cmap[ord(b)]} by {cmap[cp]};\n' for cp,(a,b) in fractions.items())+'} frac;\n'
leftgroups={};rightgroups={}
for name,base in last.items():leftgroups.setdefault(base,[]).append(name)
for name,base in first.items():rightgroups.setdefault(base,[]).append(name)
ufo.groups.clear();kern={}
for base,names in leftgroups.items():ufo.groups['public.kern1.'+base]=names
for base,names in rightgroups.items():ufo.groups['public.kern2.'+base]=names
for sub in oldfont['kern'].kernTables:
    for (a,b),v in sub.kernTable.items():kern[('public.kern1.'+a,'public.kern2.'+b)]=v
exceptionfile=OUT/'sources/kerning-exceptions.json'
if exceptionfile.exists():
    for row in json.loads(exceptionfile.read_text(encoding='utf8')):kern[(row['left_glyph'],row['right_glyph'])]=row['kern']
ufo.kerning.clear();ufo.kerning.update(kern)
ufo.features.text=features

# Nonprinting controls are blank by design; soft hyphen retains hyphen shape.
for cp in (0x200B,0x200C,0x200D,0x2060,0xFEFF):add(f'uni{cp:04X}',0,codepoint=cp)
ufo[cmap[0xAD]].unicodes=list(dict.fromkeys(ufo[cmap[0xAD]].unicodes+[0xAD]))
for n in ('space',):ufo[n].unicodes=[32,160]
assert core.issubset(cmap),[hex(cp) for cp in core-set(cmap)]
for n,w in oldwidths.items():assert ufo[n].width==w,(n,w,ufo[n].width)
ufo.glyphOrder=list(oldfont.getGlyphOrder())+sorted(set(ufo.keys())-set(oldfont.getGlyphOrder()))
info=ufo.info;info.familyName='Aetheris Display';info.styleName='Regular';info.styleMapFamilyName='Aetheris Display';info.styleMapStyleName='regular';info.unitsPerEm=1000;info.versionMajor=1;info.versionMinor=100
info.copyright='Copyright 2026 The Gilded Threshold';info.openTypeNameDesigner='The Gilded Threshold';info.openTypeNameManufacturer='The Gilded Threshold'
info.openTypeNameLicense='This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org'
info.openTypeNameLicenseURL='https://openfontlicense.org';info.openTypeNameDescription='An ornamental display typeface with sharp contrast, pointed serifs and curved flourishes. Local release candidate by The Gilded Threshold.'
info.postscriptFontName='AetherisDisplay-Regular';info.postscriptFullName='Aetheris Display Regular';info.openTypeNameVersion='Version 1.100';info.openTypeNameUniqueID='1.100;NONE;AetherisDisplay-Regular'
info.openTypeOS2VendorID='NONE';info.openTypeOS2WeightClass=400;info.openTypeOS2WidthClass=5;info.openTypeOS2Type=[];info.openTypeOS2Selection=[7]
info.xHeight=440;info.capHeight=700;info.postscriptUnderlinePosition=-140;info.postscriptUnderlineThickness=35
allbounds=[bounds(n) for n in ufo.keys()];asc=max(1120,math.ceil(max(b[3] for b in allbounds)+45));desc=min(-450,math.floor(min(b[1] for b in allbounds)-35))
info.ascender=asc;info.descender=desc;info.openTypeHheaAscender=asc;info.openTypeHheaDescender=desc;info.openTypeHheaLineGap=0
info.openTypeOS2TypoAscender=asc;info.openTypeOS2TypoDescender=desc;info.openTypeOS2TypoLineGap=0;info.openTypeOS2WinAscent=asc;info.openTypeOS2WinDescent=-desc
info.openTypeOS2CodePageRanges=[0,1,4,7];info.openTypeGaspRangeRecords=[dict(rangeMaxPPEM=65535,rangeGaspBehavior=[0,1,2,3])]
ufo.lib['public.openTypeCategories']={n:('mark' if n in list(marks.values())+list(case_marks.values())+['caroncomb.alt','commaaccentcomb.above'] else 'ligature' if n in ligs.values() else 'base') for n in ufo.keys()}
ufotarget=(OUT/'sources/AetherisDisplay.ufo').resolve()
assert ufotarget.is_relative_to(OUT.resolve())
with UFOWriter(ufotarget,formatVersion=3) as writer:ufo.write(writer,saveAs=True)
font=compileTTF(ufo,removeOverlaps=True,overlapsBackend='pathops',useProductionNames=False,inplace=False,flattenComponents=True)
font['OS/2'].fsSelection|=64|128;font['OS/2'].ulCodePageRange1|=1;font['OS/2'].recalcAvgCharWidth(font)
class DropDuplicateLines(FilterPen):
    def moveTo(self,p):self.current=p;super().moveTo(p)
    def lineTo(self,p):
        if p!=self.current:super().lineTo(p)
        self.current=p
    def qCurveTo(self,*points):
        super().qCurveTo(*points)
        if points[-1] is not None:self.current=points[-1]
    def curveTo(self,*points):super().curveTo(*points);self.current=points[-1]
for name in font.getGlyphOrder():
    g=font['glyf'][name]
    if not g.isComposite() and g.numberOfContours>0:
        pen=TTGlyphPen(None);g.draw(DropDuplicateLines(pen),font['glyf']);font['glyf'][name]=pen.glyph()
from fontTools.ttLib.tables.ttProgram import Program
font['prep']=newTable('prep');font['prep'].program=Program();font['prep'].program.fromBytecode(b'\xb8\x01\xff\x85\xb0\x04\x8d')
font['maxp'].maxStackElements=max(1,font['maxp'].maxStackElements)
# Script language declarations support downstream font selection and QA.
font['meta']=newTable('meta');font['meta'].data={'dlng':'Latn','slng':'Latn'}
fixed_time=int((datetime(2026,11,12,tzinfo=timezone.utc)-datetime(1904,1,1,tzinfo=timezone.utc)).total_seconds())
font['head'].created=fixed_time;font['head'].modified=fixed_time;font.recalcTimestamp=False
# Add a Unicode full-repertoire cmap, even though this set is in the BMP.
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
if not any(t.format==12 for t in font['cmap'].tables):
    t=CmapSubtable.newSubtable(12);t.platformID=3;t.platEncID=10;t.language=0;t.cmap=dict(font.getBestCmap());font['cmap'].tables.append(t)
font.save(OUT/'AetherisDisplay-Regular.ttf')
font.flavor='woff2';font.save(OUT/'AetherisDisplay-Regular.woff2');font.flavor=None
check=TTFont(OUT/'AetherisDisplay-Regular.ttf',checkChecksums=2);finalcmap=check.getBestCmap();assert core.issubset(finalcmap)
svgdir=OUT/'svg';svgdir.mkdir(exist_ok=True);gs=check.getGlyphSet()
coverage=[]
for cp,n in sorted(finalcmap.items()):
    if ud.category(chr(cp)) in ('Cc','Cf','Zs'):continue
    p=SVGPathPen(gs);gs[n].draw(p);bb=BoundsPen(gs);gs[n].draw(bb)
    if not bb.bounds:continue
    x0,y0,x1,y1=bb.bounds;advance=check['hmtx'][n][0];left=min(x0,0)-40;right=max(x1,advance)+40
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left} {-asc} {right-left} {asc-desc}"><path transform="scale(1,-1)" d="{p.getCommands()}"/></svg>'
    (svgdir/f'U{cp:04X}.svg').write_text(svg)
    coverage.append(dict(character=chr(cp),codepoint=f'U+{cp:04X}',name=ud.name(chr(cp),'UNKNOWN'),glyph=n,core=cp in core,new=cp not in oldfont.getBestCmap()))
(OUT/'qa/coverage.json').write_text(json.dumps(dict(required=len(core),covered=len(core&set(finalcmap)),missing=sorted(core-set(finalcmap)),mapped_codepoints=len(finalcmap),glyphs=len(check.getGlyphOrder()),characters=coverage),ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'sources/recipes.json').write_text(json.dumps(recipes,indent=2))
(OUT/'sources/features.fea').write_text(ufo.features.text)
(OUT/'qa/build-summary.json').write_text(json.dumps(dict(core_required=len(core),core_covered=len(core&set(finalcmap)),missing_core=[],mapped_codepoints=len(finalcmap),glyphs=len(check.getGlyphOrder()),ligatures=list(ligs),ascent=asc,descent=desc,author='The Gilded Threshold',license='SIL Open Font License 1.1',published=False),indent=2))
print((OUT/'qa/build-summary.json').read_text())
