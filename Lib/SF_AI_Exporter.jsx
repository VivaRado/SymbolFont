//Global
// SymbolFont AI Exporter 0.2.0
var _docRef = app.activeDocument;
var _docPath = _docRef.path;
var _ignoreHidden = true;
var _destination;
var desired_scale = 100;
var _auxDoc;
var dlg = new Window('dialog', 'SymbolFont - Adobe Illustrator Exporter');
var set_width = 100;
//ArtBoard size
var boardSizeX = get_scale(500);
var boardSizeY = get_scale(500);
var artBoardSize = (function setArtBoardSize() {
	var size = [0 - boardSizeX, 0, 0, 0 - boardSizeY];
	return size;
}());
//EPS Export Options
var epsExportOptions = (function epsExportOptions() {
	var options = new EPSSaveOptions();
	options.includeDocumentThumbnails = true;
	options.saveMultipleArtboards = false;
	options.compatibility = Compatibility.ILLUSTRATOR8;
	return options;
}());
//SVG Export Options
var svgExportOptions = (function svgExportOptions() {
	var options = new ExportOptionsSVG();
	options.embedRasterImages = true;
	options.compatibility = Compatibility.ILLUSTRATOR8;
	return options;
}());
//Start export
function initExport() {
	//Get N1 layers
	var layersN1 = _docRef.layers[0].layers;
	var activelayer = _docRef.activeLayer;
	//dlg.add('statictext', undefined, layersN1);
	for (x = 0; x < _docRef.layers.length; x++) {
		if (_docRef.layers[x] == activelayer) {
			for (i = 0; i < _docRef.layers[x].layers.length; i++) {
				//Export N1 layer
				exportLayer(_docRef.layers[x].layers[i]);
			}
		}
	}
	//Close the auxiliar document
	_auxDoc.close(SaveOptions.DONOTSAVECHANGES);
}
//Export Layer
function exportLayer(layer, path) {
	if (!(_ignoreHidden && !layer.visible)) {
		try {
			copyLayerTo(layer, _auxDoc);
			selectAll(_auxDoc);
			reNameLayer(_auxDoc, layer.name);
			var set_width = centerLayer(_auxDoc);
			ungroup(_auxDoc);
			ungroup(_auxDoc);
			//exportAsEPS(layer.name, _auxDoc, path);
			exportAsSVG(layer.name, _auxDoc, path);
			//Delete all the content of auxiliar document
			_auxDoc.activeLayer.pageItems.removeAll();
		} catch (ex) {};
	}
};

function get_scale(_num) {
	return (_num / 100) * desired_scale;
}
//Copy layer to auxiliar document
function copyLayerTo(layer, doc) {
	var pageItem;
	var numPageItems = layer.pageItems.length;
	for (var i = 0; i < numPageItems; i += 1) {
		pageItem = layer.pageItems[i];
		pageItem.duplicate(_auxDoc.activeLayer, ElementPlacement.PLACEATEND);
	}
};
//Selectt all
function selectAll(doc) {
	var pageItems = doc.pageItems;
	var numPageItems = doc.pageItems.length;
	for (var i = 0; i < numPageItems; i += 1) {
		var item = pageItems[i];
		item.selected = true;
	}
};
//Rename layer
function reNameLayer(doc, name) {
	doc.activeLayer.name = name;
};
//
function getChildAll(obj) {
	var childsArr = new Array();
	for (var i = 0; i < obj.pageItems.length; i++) childsArr.push(obj.pageItems[i]);
	return childsArr;
}
//
function ungroup(obj) {
	var elements = getChildAll(obj);
	if (elements.length < 1) {
		obj.remove();
		return;
	} else {
		for (var i = 0; i < elements.length; i++) {
			try {
				if (elements[i].parent.typename != "Layer") {
					elements[i].moveBefore(obj)
				};
				if (elements[i].typename == "GroupItem") {
					ungroup(elements[i])
				};
			} catch (e) {
				
			}
		}
	}
}
//Center layer
function centerLayer(doc) {
	var layer = doc.layers;
	var group = layer[0].groupItems[0];
	var has_dot = false;
	var dotX = 0;
	var dotY = 0;
	try {
		var the_dot = layer[0].groupItems[0].groupItems[1];
		has_dot = true;
	} catch (ex) {
		has_dot = false;
	};
	group.resize(desired_scale, // x
		desired_scale, // y
		undefined, // changePositions
		undefined, // changeFillPatterns
		undefined, // changeFillGradients
		undefined, // changeStrokePattern
		undefined, // changeLineWidths
		Transformation.CENTER); // scaleAbout
	group.top = 0;
	group.left = 0;
	group.translate(0 - boardSizeX, 0);
	if (has_dot) {
		var halfWidth = group.width / 2;
		var halfHeight = group.height / 2;
		var halfBoardSizeX = boardSizeX / 2;
		var halfBoardSizeY = boardSizeY / 2;
		dotX = the_dot.position[0] + (the_dot.width / 2);
		dotY = the_dot.position[1] + ((0 - the_dot.height) / 2);
		var posX = 0 - dotX;
		var posY = 0 - dotY;
		group.translate(posX, posY);
		the_dot.remove();
	} else {
		var halfWidth = group.width / 2;
		var halfHeight = group.height / 2;
		var halfBoardSizeX = boardSizeX / 2;
		var halfBoardSizeY = boardSizeY / 2;
		var posX = halfBoardSizeX - halfWidth;
		var posY = halfHeight - halfBoardSizeY;
		group.translate(posX, posY);
	}
	var _group = layer[0].groupItems[0];
	return Math.floor(_group.width)
};
//Export as SVG
function exportAsSVG(name, doc) {
	var file = new File(_destination + '/' + name + '.svg');
	_auxDoc.exportFile(file, ExportType.SVG, svgExportOptions);
};
function exportAsEPS(name, doc) {
	var file = new File(_destination + '/' + name + '.eps');
	//options.artboardRange = (artboardIndex+1).toString();
	_auxDoc.saveAs(file, epsExportOptions)
};
//Init
(function() {
	//Choose destination folder
	_destination = Folder.selectDialog('Select folder for SVG files.', _docPath);
	if (!_destination) {
		return;
	}
	//Create auxiliar document
	_auxDoc = app.documents.add(DocumentColorSpace.RGB);
	_auxDoc.artboards[0].artboardRect = artBoardSize;
	//Star the export
	initExport();
	dlg.add('statictext', undefined, 'Export Done');
	dlg.show();
}());