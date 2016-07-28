var mapOptions = {
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

var map = L.map('map', mapOptions);

var tileLayer = new L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
    maxZoom: 18,
});

// the layer containing the features        
var currentItems = new L.geoJson();

//items to be added
var newItems = new L.FeatureGroup();
map.addLayer(newItems);

//items to be deleted
var deleteItems = new L.FeatureGroup();
map.addLayer(deleteItems);

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
        featureGroup: currentItems // to edit we should add also currentItems
    },
    delete: {
        featureGroup: currentItems    
    }
});
map.addControl(drawControl);

// load existing network
$( document ).ready(function() {
    $.getJSON($SCRIPT_ROOT + '/_load_network', function(data) {
        var currentItems_geoJson = JSON.parse(data.result.features);
        currentItems.addData(currentItems_geoJson);
        var n = currentItems.getLayers().length;
        var status_message;
        if (n > 0 ) {
            map.fitBounds(currentItems.getBounds());
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

// snapping
var guideLayers = new Array();
guideLayers.push(currentItems);
drawControl.setDrawingOptions({
    marker: { guideLayers: guideLayers, snapDistance: 15 },
    polyline: { guideLayers: guideLayers, snapDistance: 15 },
});

// create features
var gj;
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
    $.getJSON($SCRIPT_ROOT + '/_add_feature', {new_feature: JSON.stringify(gj)}, function(data) {
        status_code = data.result.status_code;
        //console.log(status_code);
        if ( status_code == -1 ) {
            $("#add_feature_error").text('Name already in use. Please try again.');
        } else {
            //console.log(data.result.new_gj)
            var new_gj = data.result.new_gj;
            newItems.clearLayers();
            currentItems.addData(new_gj);
            guideLayers.push(new_gj); // snapping
            $('#feature_name').val('');
            $('#feature_description').val('');
            $("#save_status").text('Network updated!');
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

map.on('draw:deletestart', function (e) {
    var layer = e.layers;
    //deleteItems.addLayer(layer);
    $('#modal_delete_feature').modal('show');
    //status_message = "Deleted!"
    //guideLayers.push(layer); // snapping
    //$("#save_status").text(status_message);
});


map.on('draw:delete', function (e) {
    var layers = e.layers;
    //deleteItems.addLayer(layer);
    $('#modal_delete_feature').modal('show');
    status_message = "Deleted!"
    //guideLayers.push(layer); // snapping
    $("#save_status").text(status_message);
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

// contextmenu functions

function centerMap (e) {
    map.panTo(e.latlng);
}

function showCoordinates (e) {
    $("p#coords").text(e.latlng);
    $("#modal_coords").modal("show");
    //alert(e.latlng);
}