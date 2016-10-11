$('.modal').on('shown.bs.modal', function() {
  $(this).find('[autofocus]').focus();
});

// VARIABLES

var deleted_layer;
var deleted_feature;

var purged_layer;
var purged_feature;

var pointLeafletId = {}, linkLeafletId = {}; // id-to-id dictionaries

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
            notify('info', 'Welcome!', 'Your network is empty. Please add features.');
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
    map.spin(true);
    gj.properties.name = $('#node_name').val();
    gj.properties.description = $('#node_description').val();
    gj.properties.template_type_id = $("#node_type option:selected").val();
    gj.properties.template_type_name = $("#node_type option:selected").text();    
    
    $.ajax({
        type : "POST",
        url : $SCRIPT_ROOT + '/_add_node',
        data: JSON.stringify(gj),
        contentType: 'application/json',
        success: function(resp) {    
    
            status_code = resp.status_code;
            if ( status_code == -1 ) {
                map.spin(false);
                $("#add_node_error").text('Name already in use. Please try again.');
            } else {
                $('#modal_add_node').modal('hide');
                newItems.clearLayers();
                currentItems.removeLayer(pointLeafletId[resp.old_node_id])
                currentItems.addData(resp.new_gj);
                refreshCurrentItems();
                $('#node_name').val('');
                $('#node_description').val('');
                map.spin(false);
                notify('success', 'Success!', 'Feature added.')
                
            }
        }
    
    });
});

$('button#add_link_confirm').bind('click', function() {
    map.spin(true);
    gj.properties.name = $('#link_name').val();
    gj.properties.description = $('#link_description').val();
    gj.properties.template_type_id = $("#link_type option:selected").val();
    gj.properties.template_type_name = $("#link_type option:selected").text();
    $.getJSON($SCRIPT_ROOT + '/_add_link', {new_link: JSON.stringify(gj)}, function(resp) {
        status_code = resp.status_code;
        if ( status_code == -1 ) {
            map.spin(false);
            $("#add_link_error").text('Name already in use. Please try again.');
        } else {
            $('#modal_add_link').modal('hide');
            var new_gj = resp.new_gj;
            newItems.clearLayers();
            currentItems.addData(new_gj);
            refreshCurrentItems();
            $('#link_name').val('');
            $('#link_description').val('');
            map.spin(false);
            notify('success', 'Success!', 'Feature added.')
        };
    });
});

$('button#add_node_cancel').bind('click', function() {
    var status_code = 1;
    newItems.clearLayers();
    $('#node_name').val('');
    $('#node_description').val('');
});

$('button#add_link_cancel').bind('click', function() {
    var status_code = 1;
    newItems.clearLayers();
    $('#link_name').val('');
    $('#link_description').val('');
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

function refreshCurrentItems() {
    currentItems.eachLayer(function(layer) {
        var prop = layer.feature.properties;
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
            pointLeafletId[prop.id] = layer._leaflet_id

        } else {
            layer.setStyle({
                color: prop.color,
                weight: prop.weight,
                dashArray: prop.dashArray,
                lineJoin: prop.lineJoin,
                opacity: prop.opacity,
            });
            linkLeafletId[prop.id] = layer._leaflet_id
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

// delete a feature (need to rename to 'deactivate')
function deleteFeature(e) {
    deleted_layer = e.relatedTarget;
    deleted_feature = e.relatedTarget.feature;
    var name = deleted_feature.properties.name;
    $("#delete_feature_name").text("Delete \"" + name + "\"");
    $('#modal_delete_feature').modal('show');
}

// purge a feature
function purgeFeature(e) {
    var feature = e.relatedTarget.feature
    var msg = 'Permanently delete ' + feature.properties.name + '?<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            map.spin(true);
            var purged_json = JSON.stringify(feature);
            $.getJSON($SCRIPT_ROOT+'/_purge_replace_feature', {purged: purged_json}, function(resp) {
                
                // remove deleted node
                currentItems.removeLayer(pointLeafletId[feature.properties.id])
                
                // remove adjacent links?
                $.each(resp.del_links, function( i, link_id ) {
                    currentItems.removeLayer(linkLeafletId[link_id]);
                });
                
                // add new node
                currentItems.addData(resp.new_gj)
                refreshCurrentItems()
                map.spin(false);
                notify('success','Success!', 'Network updated.');
            });
        }
    });
}


//$('#save_as_thumbnail').click(function() {
    //html2canvas($("#map"), {
      //onrendered: function(canvas) {
        //$("body").append(canvas);
      //}
    //});
//});