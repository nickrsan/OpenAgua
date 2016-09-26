$('.modal').on('shown.bs.modal', function() {
  $(this).find('[autofocus]').focus();
});

// VARIABLES

var deleted_layer;
var deleted_feature;

var purged_layer;
var purged_feature;

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
//L.Control.boxzoom({ position:'topright' }).addTo(map);

// add locate button
var locateControl = new L.control.locate(options={
    position: 'topright',
    drawCircle: false,
    drawMarker: false,
    icon: 'fa fa-location-arrow',
    keepCurrentZoomLevel: true,
    setView: 'once',
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
    edit: false
    //edit: {
        //featureGroup: currentItems, // to edit we should add also currentItems
        //remove: false
    //}
});

// snapping
var guideLayers = new Array();
//guideLayers.push(currentItems);

drawControl.setDrawingOptions({
    marker: { guideLayers: guideLayers, snapDistance: 25 },
    polyline: { guideLayers: guideLayers, snapDistance: 25 },
});

map.addControl(drawControl);

// load existing network
map.spin(true);
$( document ).ready(function() {
    $.getJSON($SCRIPT_ROOT + '/_load_network', function(resp) {
        tileLayer.addTo(map); // add the tiles
        var featuresGJ = JSON.parse(resp.features);
        currentItems.addData(featuresGJ);
        guideLayers.push(currentItems);
        refreshCurrentItems();
        var n = currentItems.getLayers().length;
        var status_message;
        if (n > 0 ) {
            map.fitBounds(currentItems.getBounds(), {padding: [50,50]});
            notify('info', 'Network loaded!', 'Your network has ' + n + ' features.');
        } else {
            map.setView([0, 0], 2);
            notify('info', 'Welcome!', 'Empty network loaded. Please add features.');
        }
        map.addLayer(currentItems);
        map.spin(false);
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

// create features
var gj;
var newItems = new L.FeatureGroup();
map.addLayer(newItems);
map.on('draw:created', function (e) {
    var type = e.layerType,
        layer = e.layer;
    newItems.addLayer(layer);
    gj = layer.toGeoJSON();
    if (type=='marker') {
        $('#modal_add_node').modal('show');
    } else {
        $('#modal_add_link').modal('show');            
    }
});

$('button#add_node_confirm').bind('click', function() {
    gj.properties.name = $('#node_name').val();
    gj.properties.description = $('#node_description').val();
    gj.properties.template_type_id = $("#node_type option:selected").val();
    gj.properties.template_type_name = $("#node_type option:selected").text();    
    
    $.getJSON($SCRIPT_ROOT + '/_add_node', {new_node: JSON.stringify(gj)}, function(resp) {
        status_code = resp.status_code;
        if ( status_code == -1 ) {
            $("#add_node_error").text('Name already in use. Please try again.');
        } else {
            var new_gj = resp.new_gj;
            newItems.clearLayers();
            currentItems.addData(new_gj);
            refreshCurrentItems();
            $('#node_name').val('');
            $('#node_description').val('');
            //$("#save_status").text('node added!');
            $('#modal_add_node').modal('hide');
        };
    });
});

$('button#add_link_confirm').bind('click', function() {
    gj.properties.name = $('#link_name').val();
    gj.properties.description = $('#link_description').val();
    gj.properties.template_type_id = $("#link_type option:selected").val();
    gj.properties.template_type_name = $("#link_type option:selected").text();
    $.getJSON($SCRIPT_ROOT + '/_add_link', {new_link: JSON.stringify(gj)}, function(resp) {
        status_code = resp.status_code;
        if ( status_code == -1 ) {
            $("#add_link_error").text('Name already in use. Please try again.');
        } else {
            var new_gj = resp.new_gj;
            newItems.clearLayers();
            currentItems.addData(new_gj);
            refreshCurrentItems();
            $('#link_name').val('');
            $('#link_description').val('');
            //$("#save_status").text('link added!');
            $('#modal_add_link').modal('hide');
        };
    });
});

$('button#add_node_cancel').bind('click', function() {
    var status_code = 1;
    newItems.clearLayers();
    $('#node_name').val('');
    $('#node_description').val('');
    //$("#save_status").text('Action cancelled.');
});

$('button#add_link_cancel').bind('click', function() {
    var status_code = 1;
    newItems.clearLayers();
    $('#link_name').val('');
    $('#link_description').val('');
    //$("#save_status").text('Action cancelled.');    
});

map.on('draw:edited', function (e) {
    var layers = e.layers;
    var countOfEditedLayers = 0;
    layers.eachLayer(function(layer) {
        countOfEditedLayers++;
    });
});

$('button#delete_feature_confirm').bind('click', function() {
    deleted_json = JSON.stringify(deleted_feature);
    $.getJSON($SCRIPT_ROOT+'/_delete_feature', {deleted: deleted_json}, function(data) {
        status_code = data.result.status_code;
        if ( status_code == 1 ) { // there should be only success
            currentItems.removeLayer(deleted_layer);
            $("#delete_feature_name").text(""); // probably not necessary...
            $("#modal_delete_feature").modal("hide");
        };
    });
});


// FUNCTIONS

// delete a feature
function deleteFeature(e) {
    deleted_layer = e.relatedTarget;
    deleted_feature = e.relatedTarget.feature;
    var name = deleted_feature.properties.name;
    $("#delete_feature_name").text("Delete \"" + name + "\"");
    $('#modal_delete_feature').modal('show');
}

// purge a feature
function purgeFeature(e) {
    //e.preventDefault();
    var msg = 'Permanently delete previously removed features?<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            var purged_json = JSON.stringify(e.relatedTarget.feature);
            $.getJSON($SCRIPT_ROOT+'/_purge_replace_feature', {purged: purged_json}, function(resp) {
                
                $.each(resp.old_gj, function( gj ) {
                    currentItems.removeLayer(gj);
                });
                currentItems.addData(resp.new_gj)
                refreshCurrentItems()
                notify('success','Success!', 'Network updated.');
            });
        }
    });
}

function refreshCurrentItems() {
    currentItems.eachLayer(function(layer) {
        var prop = layer.feature.properties;
        //layer.bindPopup(prop.name); // add popup
        layer.bindLabel(prop.name, {
            noHide: false,
            offset: [20,-15]
        });
        layer.bindContextMenu(getContextmenuOptions(prop.name)); // add context menu
        if (layer.feature.geometry.type == 'Point') {
            var iconUrl = $SCRIPT_ROOT + "/static/hydra/templates/" + prop.template_name + "/template/" + prop.image;
            var icon = new nodeIcon({
                iconUrl: iconUrl
            });
            layer.setIcon(icon); // add icon

        } else {
            layer.setStyle({
                color: prop.color,
                weight: prop.weight,
                dashArray: prop.dashArray,
                lineJoin: prop.lineJoin,
                opacity: prop.opacity,
            });      
        }
        
    });
};


// get shapes to add
function getJson(items) {
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
function getContextmenuOptions(featureName) {
    var contextmenuOptions = {
        contextmenu: true,
        contextmenuItems: [{
            text: featureName,
            index: 0
        }, {
            separator: true,
            index: 1
        }, {
            text: 'Deactivate',
            index: 2,
            callback: deleteFeature
        }, {
            text: 'Delete',
            index: 3,
            callback: purgeFeature
        }, {
            separator: true,
            index: 4
        }, {
            text: 'Show coordinates',
            index: 5,
            callback: showCoordinates
        }, {
            text: 'Center map here',
            index: 6,
            callback: centerMap}],
        contextmenuInheritItems: false
    };
    return contextmenuOptions;
};

// center the map on the selected point
function centerMap(e) {
    map.panTo(e.latlng);
}

// show the coordinates of the selected point
function showCoordinates(e) {
    $("p#coords").text(e.latlng);
    $("#modal_coords").modal("show");
}

