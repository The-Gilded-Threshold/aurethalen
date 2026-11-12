"""Compile the editable UFO; run from any directory with Python 3.12+."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
from ufoLib2 import Font
from ufo2ft import compileTTF
from fontTools.pens.filterPen import FilterPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=ROOT/'fonts')
args=parser.parse_args()
OUT=args.output_dir.resolve()
TTF=OUT/'ttf/Aurethalen-Regular.ttf';WOFF=OUT/'webfonts/Aurethalen-Regular.woff2'
TTF.parent.mkdir(parents=True,exist_ok=True);WOFF.parent.mkdir(parents=True,exist_ok=True)
ufo=Font.open(ROOT/'sources/Aurethalen.ufo')
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
font.save(TTF)
font.flavor='woff2';font.save(WOFF);font.flavor=None
print(json.dumps({str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (TTF,WOFF)},indent=2))
