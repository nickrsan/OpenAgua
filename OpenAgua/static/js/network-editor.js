var tilesurl = 'http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        attrib = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        tiles = L.tileLayer(tilesurl, {maxZoom: 18, attribution: attrib}),
        map = new L.Map('map-edit', {
            layers: [tiles],
            center: new L.LatLng(25.66, -100.3),
            zoomControl: false,
            zoom: 8
        });
        
// geoJson items from Hydra Server
var currentItems = new L.geoJson();
map.addLayer(currentItems);

var newItems = new L.FeatureGroup();
map.addLayer(newItems);

// add zoom buttons
L.control.zoom({position:'topright'}).addTo(map);
var zoomboxControl = new L.Control.boxzoom({ position:'topright' });
map.addControl(zoomboxControl);

// add locate button
var locateControl = new L.control.locate(options={
    position: 'bottomright',
    drawCircle: false,
    drawMarker: false,
    icon: 'fa fa-location-arrow',
    keepCurrentZoomLevel: true,
    setView: false,
    strings: {title: "Go to my location"}
});
map.addControl(locateControl);

// full screen button
var fullScreenButton = new L.Control.Fullscreen({position: 'topright'});
map.addControl(fullScreenButton);

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
        featureGroup: newItems // to edit we should add also currentItems
    },
    delete: {
        featureGroup: currentItems    
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
    var currentItems_geoJson = JSON.parse(data.result.features);
    currentItems.clearLayers();
    currentItems.addData(currentItems_geoJson);
    $("#load_status").text(data.result.status_message);
  });
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
        console.log(status_code);
        if ( status_code == -1 ) {
            $("#add_feature_error").text('Name already in use. Please try again.');
        } else {
            //var new_gj = JSON.parse(data.result.new_gj);
            console.log(data.result.new_gj)
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
    newItems.removeLayer(layer);
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
    console.log("Edited " + countOfEditedLayers + " layers");
});

map.on('draw:deleted', function (e) {
    var layers = e.layers;
    $('#modal_delete_feature').modal('show');
    //newItems.addLayer(layer);
    status_message = "Deleted!"
    //guideLayers.push(layer); // snapping
    $("#save_status").text(status_message);
});

//// button - save edits
//// if successful, need to update map with data.result.network_data
//$('button#save_edits').bind('click', function() {
    //newLayers = newItems.getLayers();
    //cnt = newLayers.length;
    //if (cnt > 0) {
        //map.spin(true);
        //new_features = getJson(newItems);
        //$.getJSON($SCRIPT_ROOT + '/_save_network', {new_features: new_features}, function(data) {
          //currentItems_geoJson = JSON.parse(data.result.features);
          //currentItems.clearLayers();
          //newItems.clearLayers();
          //currentItems.addData(currentItems_geoJson);
          //status_message = 'Edits saved!';
          //$("#save_status").text('Edits saved!');
          //});
        //map.spin(false);
    //} else {
        //$("#save_status").text('No edits detected. Nothing saved.')
    //};
    
  //});

//// button - clear edits
//$('button#clear_edits').bind('click', function() {
  //newItems.eachLayer(function(layer) {
    //newItems.removeLayer(layer);
    //guideLayers.pop(layer);
    //$("#save_status").text('Edits cleared.');
  //});
//});

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