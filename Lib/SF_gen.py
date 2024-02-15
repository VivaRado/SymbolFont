#!/usr/bin/env python
# SymbolFont 0.6.0
# python3 SF_gen.py -s '/media/root/2e8bc55c-ed6f-46ce-9ad9-996aa9703e0c/320/_code/symbolfont/bin/opentype-svg/fonts/SVGs'

__doc__="""\
Generates OTF SymbolFont using SVG Ligature Files.

Usage:
  python SF_gen.py -s <folder_path>

Options:
  -s  --svgdir path to folder containing SVG files.
	  (the file names must match the names of the ligatures. e.g.: A_B.svg )
  -n  --fontname optional, output OTF file name.
"""

from svg.path import parse_path, Path, Line, CubicBezier, QuadraticBezier
from fontTools.misc.transform import Transform
from fontTools.misc.transform import Identity
from builtins import chr
import os
import sys
import re
import argparse
import fontTools.ttLib as ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.svgLib import SVGPath

__dirname, __filename = os.path.split(os.path.abspath(__file__))
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--svgdir', help="Specify the SVG file directory.")
parser.add_argument('-n', '--fontname', help="Specify the name of the generated font.", default=argparse.SUPPRESS)
reCopyCounter = re.compile("#\d+$")

def readFile(filePath):
	f = open(filePath, "rt")
	data = f.read()
	f.close()
	return data

def getGlyphNameFromFileName(filePath):
	fontFileName = os.path.split(filePath)[1]
	return os.path.splitext(fontFileName)[0]

def makeFontCopyPath(fontPath):
	dirName, fileName = os.path.split(fontPath)
	fileName, fileExt = os.path.splitext(fileName)
	fileName = reCopyCounter.split(fileName)[0]
	fontCopyPath = os.path.join(dirName, fileName + fileExt)
	n = 0

	while os.path.exists(fontCopyPath):
		fontCopyPath = os.path.join(dirName, fileName + "_" + repr(n) + fileExt)
		n += 1
	return fontCopyPath

def create_feature_list(feature_tag, lookup_count):
	"""Create a FeatureList for the GSUB table."""
	feature_record = ot.FeatureRecord()
	feature_record.FeatureTag = feature_tag
	feature_record.Feature = ot.Feature()
	feature_record.Feature.LookupCount = lookup_count
	feature_record.Feature.LookupListIndex = range(lookup_count)
	feature_record.Feature.FeatureParams = None

	feature_list = ot.FeatureList()
	feature_list.FeatureCount = 1
	feature_list.FeatureRecord = [feature_record]

	return feature_list

def create_script_list(script_tag='DFLT'):
    """Create a ScriptList for the GSUB table."""
    def_lang_sys = ot.DefaultLangSys()
    def_lang_sys.ReqFeatureIndex = 0xFFFF
    def_lang_sys.FeatureCount = 1
    def_lang_sys.FeatureIndex = [0]
    def_lang_sys.LookupOrder = None

    script_record = ot.ScriptRecord()
    script_record.ScriptTag = script_tag
    script_record.Script = ot.Script()
    script_record.Script.DefaultLangSys = def_lang_sys
    script_record.Script.LangSysCount = 0
    script_record.Script.LangSysRecord = []

    script_list = ot.ScriptList()
    script_list.ScriptCount = 1
    script_list.ScriptRecord = [script_record]

    return script_list

def create_simple_gsub(lookups, script='DFLT', feature='liga'):
	"""Create a simple GSUB table."""
	gsub_class = ttLib.getTableClass('GSUB')
	gsub = gsub_class('GSUB')

	gsub.table = ot.GSUB()
	gsub.table.Version = 0x00010000

	gsub.table.ScriptList = create_script_list(script)

	gsub.table.FeatureList = create_feature_list(feature, len(lookups))
	gsub.table.LookupList = create_lookup_list(lookups)
	return gsub

def create_lookup_list(lookups):
	"""Create a LookupList for the GSUB table."""
	lookup_list = ot.LookupList()
	lookup_list.LookupCount = len(lookups)
	lookup_list.Lookup = lookups

	return lookup_list

def create_lookup(font, ligs, flag=0):
	"""Create a Lookup based on mapping table."""
	data_ligs = {tuple(key.split('_')): key for key in ligs}
	ligature_subst = ot.LigatureSubst()
	ligature_subst.ligatures = data_ligs
	
	#("A", "B", "C"): "A_B_C",

	lookup = ot.Lookup()
	lookup.LookupType = 4
	lookup.LookupFlag = flag
	lookup.SubTableCount = 1
	lookup.SubTable = [ligature_subst]

	return lookup

def svg2glif(svg, name, width=0, height=0, unicodes=None, transform=None, version=2):
	t = Identity.scale(1, -1).translate(0, -width)
	pen = T2CharStringPen(width, None)
	outline = SVGPath.fromstring(svg, transform=t)
	outline.draw(pen)
	glyph_a = pen.getCharString()

	return {name:glyph_a}

def import_svg(svgFilePathsList, lw, lh):
	svg_glyphs = {}
	
	for svgFilePath in svgFilePathsList:
		fileName = os.path.basename(svgFilePath)
		gName = getGlyphNameFromFileName(svgFilePath)
		if '_' in gName:
			svgItemData = readFile(svgFilePath)
			svg_glif = svg2glif(svgItemData, gName, width = lw, height = lh )
			svg_glyphs.update(svg_glif)
	return svg_glyphs

def drawEmptyGlyph(pen):
	pen.moveTo((0, 0))
	pen.closePath()

def processFont(fontPath, svgFilePathsList, options):

	familyName 		= "SymbolFont"
	styleName 		= "Regular"
	version 		= "0.1"
	l_width 		= 500
	l_height 		= 500
	imported_glyphs = import_svg(svgFilePathsList, l_width, l_height)

	nons 			= [".notdef", ".null", "space"]
	ligs 			= imported_glyphs.keys()
	lrng 			= range(65, 91) # A-Z
	crng 			= list(map(chr,lrng))
	cmap 			= { **{ 32: "space"}, **dict(zip( lrng,crng)) }
	w_nons 			= {".notdef": l_width, "space": l_width, ".null": 0}
	w_lets 			= dict(zip( crng, [l_width] * len(crng)))
	w_ligs 			= dict(zip( ligs, [l_width] * len(ligs)))
	advanceWidths 	= { **w_nons, **w_lets,**w_ligs }

	fb = FontBuilder(1000, isTTF=False)
	fb.setupGlyphOrder([*nons, *crng, *ligs])
	fb.setupCharacterMap(cmap)

	nameStrings = dict(
		familyName=dict(en=familyName),
		styleName=dict(en=styleName),
		uniqueFontIdentifier="fontBuilder: " + familyName + "." + styleName,
		fullName=familyName + "-" + styleName,
		psName=familyName + "-" + styleName,
		version="Version " + version,
	)

	pen_b = T2CharStringPen(l_width, None)
	drawEmptyGlyph(pen_b)
	eg_b = pen_b.getCharString()

	charStrings = {
		**{ ".notdef": eg_b, "space": eg_b, ".null": eg_b },
		**dict(zip( crng, [eg_b] * len(crng))),
		**imported_glyphs
	}
	fb.setupCFF(nameStrings["psName"], {"FullName": nameStrings["psName"]}, charStrings, {})
	lsb = {gn: cs.calcBounds(None)[0] for gn, cs in charStrings.items()}
	metrics = {}
	for gn, advanceWidth in advanceWidths.items():
		metrics[gn] = (advanceWidth, lsb[gn])

	fb.setupHorizontalMetrics(metrics=metrics)
	fb.setupHorizontalHeader(ascent=l_height, descent=0)
	fb.setupNameTable(nameStrings)
	fb.setupOS2(sTypoAscender=l_height, usWinAscent=l_height, usWinDescent=0)
	fb.setupPost()

	fb.font["GSUB"] = create_simple_gsub([create_lookup(fb.font, ligs)])

	fontCopyPath = makeFontCopyPath(fontPath)

	print('SAVING:',fontCopyPath)

	fb.save(fontCopyPath)

class Options(object):
	svgFolderPath = None
	fontName = 'symbolfont.otf'

	def __init__(self, args):
		if args.svgdir:
			path = os.path.realpath(args.svgdir)
			if os.path.isdir(path):
				self.svgFolderPath = path
			else:
				print("ERROR: %s is not a valid folder path." % path, file=sys.stderr)
				sys.exit(1)
		if 'fontname' in vars(args):
			if args.fontname != self.fontName:
				self.fontName = "%s.otf" % args.fontname

def Generate():

	options = Options(parser.parse_args()) 
	fontPath = os.path.join(os.path.abspath(os.path.join(__dirname, os.pardir)),'Source','fonts',options.fontName)
	svgFilePathsList = []
	for dirName, subdirList, fileList in os.walk(options.svgFolderPath):
		for file in fileList:
			svgFilePathsList.append(os.path.join(dirName, file))
	if not svgFilePathsList:
		print("No SVG files were found.", file=sys.stdout)
		sys.exit(1)

	processFont(fontPath, svgFilePathsList, options)

if __name__ == "__main__":
	if len(sys.argv) == 1:
		print(__doc__)
	else:
		Generate()