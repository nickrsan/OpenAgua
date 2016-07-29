$('.modal').on('shown.bs.modal', function() {
  $(this).find('[autofocus]').focus();
});

// VARIABLES

// main context menu
var mapContextmenuOptions = {
    zoomControl: false,
    contextmenu: true,
    contextmenuWidth: 140,
    contextmenuItems: [{
        text: 'Show coordinates',
        callback: showCoordinates
        }, {
        text: 'Center map here',
        callback: centerMap
    }]
};

// CREATE BASIC MAP

var map = L.map('map', mapContextmenuOptions);

var tileLayer = new L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
    maxZoom: 18,
});

// the layer containing the features        
var currentItems = new L.geoJson();

// add zoom buttons
L.control.zoom({position:'topright'}).addTo(map);
var zoomboxControl = new L.Control.boxzoom({ position:'topright' });
map.addControl(zoomboxControl);

// add locate button
var locateControl = new L.control.locate(options={
    position: 'topright',
    drawCircle: false,
    drawMarker: false,
    icon: 'fa fa-location-arrow',
    keepCurrentZoomLevel: true,
    setView: false,
    strings: {title: "Go to my location"}
});
map.addControl(locateControl);

// full screen button - NB: function deleted since modal doesn't show in
// full screen mode. Let's add this back for the visualization though. Or,
// figure out how to disable editing in full screen mode.
//var fullScreenButton = new L.Control.Fullscreen({position: 'topright'});
//map.addControl(fullScreenButton);

// feature creation & editing toolbar
// need to revise this for multiple feature types
// see https://github.com/Leaflet/Leaflet.draw/issues/265 and http://jsfiddle.net/jacobtoye/xgdV4/2/
var drawControl = new L.Control.Draw({
    draw: {
        position: 'topleft',
        polygon: false,
        circle: false,
        rectangle: false,
    },
    edit: {
        featureGroup: currentItems, // to edit we should add also currentItems
        remove: false
    }
});
map.addControl(drawControl);

// snapping
var guideLayers = new Array();
guideLayers.push(currentItems);
drawControl.setDrawingOptions({
    marker: { guideLayers: guideLayers, snapDistance: 15 },
    polyline: { guideLayers: guideLayers, snapDistance: 15 },
});

// load existing network
$( document ).ready(function() {
    $.getJSON($SCRIPT_ROOT + '/_load_network', function(data) {
        var featuresGJ = JSON.parse(data.result.features);
        currentItems.addData(featuresGJ);
        refreshCurrentItems();
        var n = currentItems.getLayers().length;
        var status_message;
        if (n > 0 ) {
            map.fitBounds(currentItems.getBounds(), {padding: [50,50]});
            status_message = 'Network loaded, with ' + n + ' features added.'
        } else {
            map.setView([0, 0], 2);
            status_message = 'Empty network loaded. Please add features.'
        };
        tileLayer.addTo(map); // add the tiles
        map.addLayer(currentItems); // add the layers
        $("#load_status").text(status_message);
    });
});

// icon class
var nodeIcon = L.Icon.extend({
    options: {
        iconSize:     [20, 20],
        iconAnchor:   [10, 10],
        popupAnchor:  [0, -15]
    }
});

refreshCurrentItems = function() {
    currentItems.eachLayer(function(layer) {
        var prop = layer.feature.properties;
        var iconUrl = $SCRIPT_ROOT + "/static/hydra/" + prop.template_name + "/" + prop.image;
        var icon = new nodeIcon({iconUrl: iconUrl});
        layer.setIcon(icon); // 1. add icon
        layer.bindPopup(prop.name); // 2. add popup
        layer.bindContextMenu(getContextmenuOptions(prop.name)) // 3. add context menu
    });
};

// create features
var gj;
var newItems = new L.FeatureGroup();
map.addLayer(newItems);
map.on('draw:created', function (e) {
    var type = e.layerType,
        layer = e.layer;
    newItems.addLayer(layer);
    gj = layer.toGeoJSON();
    $('#modal_add_feature').modal('show');
});

$('button#add_feature_confirm').bind('click', function() {
    gj.properties.name = $('#feature_name').val();
    gj.properties.description = $('#feature_description').val();
    gj.properties.type = $("#feature_type").val();
    $.getJSON($SCRIPT_ROOT + '/_add_feature', {new_feature: JSON.stringify(gj)}, function(data) {
        status_code = data.result.status_code;
        if ( status_code == -1 ) {
            $("#add_feature_error").text('Name already in use. Please try again.');
        } else {
            var new_gj = data.result.new_gj;
            newItems.clearLayers();
            currentItems.addData(new_gj);
            refreshCurrentItems();
            $('#feature_name').val('');
            $('#feature_description').val('');
            $("#save_status").text('Feature added!');
            $('#modal_add_feature').modal('hide');
        };
    });
});

$('button#add_feature_cancel').bind('click', function() {
    var status_code = 1;
    newItems.clearLayers();
    $('#feature_name').val('');
    $('#feature_description').val('');
    $("#save_status").text('Action cancelled.');    
});

map.on('draw:edited', function (e) {
    var layers = e.layers;
    var countOfEditedLayers = 0;
    layers.eachLayer(function(layer) {
        countOfEditedLayers++;
    });
    //console.log("Edited " + countOfEditedLayers + " layers");
});

// FUNCTIONS

// get shapes to add
var getJson = function(items) {
    var shapes = [];
    var layerJson;
    
    items.eachLayer(function(layer) {
        layerJson = layer.toGeoJSON();
        shapes.push(layerJson);
    });

    var jsonshapes = JSON.stringify({shapes: shapes});

    return jsonshapes;
};

// feature context menu
getContextmenuOptions = function(featureName) {
    var contextmenuOptions = {
        contextmenu: true,
        contextmenuItems: [{
            text: featureName,
            index: 0
        }, {
            separator: true,
            index: 1
        }, {
            text: 'Delete',
            index: 2,
            callback: deleteFeature
        }, {
            separator: true,
            index: 3
        }, {
            text: 'Show coordinates',
            index: 4,
            callback: showCoordinates
        }, {
            text: 'Center map here',
            index: 5,
            callback: centerMap}],
        contextmenuInheritItems: false
    };
    return contextmenuOptions;
};

function centerMap (e) {
    map.panTo(e.latlng);
}

function showCoordinates (e) {
    $("p#coords").text(e.latlng);
    $("#modal_coords").modal("show");
}

var deleted_layer;
var deleted_feature;
function deleteFeature(e) {
    deleted_layer = e.relatedTarget;
    deleted_feature = e.relatedTarget.feature;
    var name = deleted_feature.properties.name;
    $("#delete_feature_name").text("Delete \"" + name + "\"");
    $('#modal_delete_feature').modal('show');
}

$('button#delete_feature_confirm').bind('click', function() {
    deleted_json = JSON.stringify(deleted_feature);
    $.getJSON($SCRIPT_ROOT+'/_delete_feature', {deleted: deleted_json}, function(data) {
        status_code = data.result.status_code;
        if ( status_code == 1 ) { // there should be only success
            currentItems.removeLayer(deleted_layer);
            $("#delete_feature_name").text(""); // probably not necessary...
            $("#save_status").text("Feature deleted!");
            $("#modal_delete_feature").modal("hide");
        };
    });
});