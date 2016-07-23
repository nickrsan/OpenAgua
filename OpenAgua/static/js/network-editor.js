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

// add custom drawing tools based on template

L.Draw.MarkerA = L.Draw.Marker.extend({
    initialize: function (map, options) {
        this.type = 'A';

        L.Draw.Feature.prototype.initialize.call(this, map, options);
    },

    addHooks: function () {
        L.Draw.Marker.prototype.addHooks.call(this);

        if (this._map) {
            this._tooltip.updateContent({ text: '' });
        }
    }
});

//L.DrawToolbar.include({
    //getModeHandlers: function (map) {
        //return [
            //{
                //enabled: true,
                //handler: new L.Draw.MarkerA(map, { icon: new L.Icon.Default() }),
                //title: 'Place reservoir marker'
            //},
            //{
                //enabled: true,
                //handler: new L.Draw.Marker(map, { icon: new L.Icon.Default() }),
                //title: 'Place demand marker'
            //},
            //{
                //enabled: true,
                //handler: new L.Draw.Marker(map, { icon: new L.Icon.Default() }),
                //title: 'Place inflow marker'
            //}
        //];
    //}
//});

var drawControl = new L.Control.Draw({
    draw: {
        position: 'topleft'
    },
    edit: {
        featureGroup: newItems // to edit we should add also currentItems
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

map.on('draw:created', function (e) {
    var type = e.layerType,
        layer = e.layer;

    if (type === 'marker') {
        layer.bindPopup('A popup!');
    }

    newItems.addLayer(layer);
    guideLayers.push(layer); // snapping
    $("#save_status").text('EDITS NOT SAVED!');
});

map.on('draw:edited', function (e) {
    var layers = e.layers;
    var countOfEditedLayers = 0;
    layers.eachLayer(function(layer) {
        countOfEditedLayers++;
    });
    console.log("Edited " + countOfEditedLayers + " layers");
});

// button - load existing network, if any
$('button#load_network').bind('click', function() {
  $.getJSON($SCRIPT_ROOT + '/_load_network', function(data) {
    var currentItems_geoJson = JSON.parse(data.result.features);
    currentItems.clearLayers();
    currentItems.addData(currentItems_geoJson);
    $("#load_status").text(data.result.status_message);
    
  });
  return false;
});

// button - save edits
// if successful, need to update map with data.result.network_data
$('button#save_edits').bind('click', function() {
  $.getJSON($SCRIPT_ROOT + '/_save_network', {new_features: getJson(newItems)}, function(data) {
    var currentItems_geoJson = JSON.parse(data.result.features);
    currentItems.clearLayers();
    newItems.clearLayers();
    currentItems.addData(currentItems_geoJson); 
    $("#save_status").text(data.result.status_message);
  });
});

// button - clear edits
$('button#clear_edits').bind('click', function() {
  newItems.eachLayer(function(layer) {
    newItems.removeLayer(layer);
    guideLayers.pop(layer);
    $("#save_status").text('Edits cleared.');
  });
});

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