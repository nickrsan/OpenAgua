
var node_names;

$('.modal').on('shown.bs.modal', function() {
    $(this).find('[autofocus]').focus();
});

// VARIABLES

var deleted_layer, deleted_feature, purged_layer, purged_feature,
    pointLeafletId = {}, linkLeafletId = {}; // id-to-id dictionaries

// main context menu
var mapContextmenuOptions = {
    zoomControl: false,
    contextmenu: true,
    contextmenuWidth: 200,
    contextmenuItems: [{
        text: 'Show coordinates',
        callback: showCoordinates
        }, {
        text: 'Center map here',
        callback: centerMap
    }]
};

// CREATE BASIC MAP
var map, tileLayer, currentItems, controlSearch, locateControl, drawControl, guideLayers;

$(function() {
    
    // set map div height
    $('#map').height($(window).height() - 120);

    map = L.map('map', mapContextmenuOptions);
    
    tileLayer = new L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        maxZoom: 18,
    });
    
    // the layer containing the features        
    currentItems = new L.geoJson();
    
    // add search
    controlSearch = new L.Control.Search({
        position:'topright',	
        layer: currentItems,
        propertyName: 'name',
        //circleLocation: false,
        //initial: false,
        zoom: 8,
        marker: false
    });
    map.addControl( controlSearch );
    
    // add zoom buttons
    L.control.zoom({position:'topright'}).addTo(map);
    
    // add locate button
    locateControl = new L.control.locate(options={
        position: 'topright',
        drawCircle: false,
        drawMarker: false,
        icon: 'fa fa-location-arrow',
        keepCurrentZoomLevel: true,
        setView: 'once',
        strings: {title: "Go to my location"}
    });
    map.addControl(locateControl);
    
    drawControl = new L.Control.Draw({
        draw: {
            position: 'topleft',
            polygon: false,
            circle: false,
            rectangle: false,
        },
        edit: {
            featureGroup: currentItems,
            //edit: false,
            //remove: false,
        }
    });
    
    // snapping
    guideLayers = new Array();
    
    drawControl.setDrawingOptions({
        marker: { guideLayers: guideLayers, snapDistance: 25 },
        polyline: { guideLayers: guideLayers, snapDistance: 25 },
    });
    
    map.addControl(drawControl);
    
    map.spin(true);
})

// load existing network
$(function() {
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

$(function() {
    var gj;
    var newItems = new L.FeatureGroup();
    map.addLayer(newItems);

    // add new features   
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

    // edit features
    map.on('draw:edited', function (e) {
        map.spin(true);
        var layers = e.layers, new_gj, points = [], polylines = [];
        layers.eachLayer(function(layer) {
            new_gj = layer.toGeoJSON();
            if (new_gj.geometry.type == 'Point') {
                points.push(new_gj);
            } else {
                polylines.push(new_gj);
            }
        });
        $.ajax({
            type : "POST",
            url : $SCRIPT_ROOT + '/_edit_geometries',
            data: JSON.stringify({points: points, polylines: polylines}),
            contentType: 'application/json',
            success: function(resp) {
                if (resp.statuscode == 1) {
                    layers.eachLayer(function(layer) {
                        if (layer.feature.geometry.type !== 'Point') {
                            currentItems.removeLayer(layer._leaflet_id);
                        }
                    });
                    currentItems.addData(resp.new_gj);
                    refreshCurrentItems();
                    notify('success','Success!','Edits saved.')
                } else {
                    notify('danger','Failure!','Something went wrong. Edits not saved.')
                }
                map.spin(false);
            }
        });
    });

    map.on('draw:deleted', function(e) {
        var layers = e.layers;
        deleteLayers(layers);
    });

    $('button#add_node_confirm').on('click', function() {
        var node_name = $('#node_name').val();
        if ( $('#node_name').val() == "" ) {
            $("#add_node_error").text('Name cannot be blank.');
        } else if (_.includes(node_names, node_name)) {
            $("#add_node_error").text('Name already in use. Please use a different name.');
        } else {
            $('#modal_add_node').modal('hide');
            $(".modal input").empty();

            map.spin(true);
            gj.properties.name = node_name;
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
                        notify('danger', 'Oops!', 'Something went wrong.')
                    } else {
                        newItems.clearLayers();
                        currentItems.removeLayer(pointLeafletId[resp.old_node_id])
                        currentItems.addData(resp.new_gj);
                        refreshCurrentItems();
                        notify('success', 'Success!', 'Feature added.')

                    }
                    map.spin(false);
                }

            });
        }
    });

    $('button#add_link_confirm').on('click', function() {
        //map.spin(true);
        gj.properties.name = $('#link_name').val();
        gj.properties.description = $('#link_description').val();
        gj.properties.template_type_id = $("#link_type option:selected").val();
        gj.properties.template_type_name = $("#link_type option:selected").text();
        //$.getJSON($SCRIPT_ROOT + '/_add_link', {new_link: JSON.stringify(gj)}, function(resp) {

        $.ajax({
            type : "POST",
            url : $SCRIPT_ROOT + '/_add_link',
            data: JSON.stringify(gj),
            contentType: 'application/json',
            success: function(resp) {    

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
                    //map.spin(false);
                    notify('success', 'Success!', 'Feature added.')
                }
            }
        });
    });

    $('button#add_node_cancel').on('click', function() {
        var status_code = 1;
        newItems.clearLayers();
        $('#node_name').val('');
        $('#node_description').val('');
    });

    $('button#add_link_cancel').on('click', function() {
        var status_code = 1;
        newItems.clearLayers();
        $('#link_name').val('');
        $('#link_description').val('');
    });

});


// FUNCTIONS

function refreshCurrentItems() {
    node_names = [];
    currentItems.eachLayer(function(layer) {
        var prop = layer.feature.properties;
        node_names.push(prop.name);
        layer.bindTooltip(prop.name, {
            noHide: false,
            offset: [20,-15]
        });
        layer.bindContextMenu(getContextmenuOptions(prop.name)); // add context menu
        if (layer.feature.geometry.type == 'Point') {
            //var iconUrl = $SCRIPT_ROOT + "/static/hydra/templates/" + prop.template_name + "/template/" + prop.image;
            var iconUrl = $SCRIPT_ROOT + "/static/hydra/templates/openagua/template/" + prop.image;
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
            text: 'Edit name/description',
            index: 2,
            callback: editName
        }, {
            text: 'Quick edit data here',
            index: 3,
            callback: editDataHere
        }, {
            text: 'Edit data in Data Editor',
            index: 4,
            callback: editData
        }, {
            text: 'Delete',
            index: 5,
            callback: purgeFeature
        }, {
            separator: true,
            index: 6
        }, {
            text: 'Show coordinates',
            index: 7,
            callback: showCoordinates
        }, {
            text: 'Center map here',
            index: 8,
            callback: centerMap}],
        contextmenuInheritItems: false
    };
    return contextmenuOptions;
};

// RIGHT-CLICK CALLBACKS

// edit name & description
function editName(e) {}

// edit data in data editor
function editData(e) {

}

// edit data here
function editDataHere(e) {}

// center the map on the selected point
function centerMap(e) {
    map.panTo(e.latlng);
}

// show the coordinates of the selected point
function showCoordinates(e) {
    var lat = e.latlng.lat;
    var lon = e.latlng.lng
    if (e.relatedTarget !== undefined) {
        var gj = e.relatedTarget.toGeoJSON()
        if (gj.geometry.type === 'Point') {
            lon = gj.geometry.coordinates[0];
            lat = gj.geometry.coordinates[1];
        }
    }
    bootbox.alert("Latitude: " + lat.toFixed(3) + ", Longitude: " + lon.toFixed(3));
}

// delete multiple layers

function deleteLayers(layers) {
    var gj, points = [], nodes = [], polylines = [], links = [];

    layers.eachLayer(function(layer) {
        gj = layer.toGeoJSON();
        if (gj.geometry.type == 'Point') {
            points.push(gj)
            nodes.push(gj.properties);
        } else {
            polylines.push(gj)
            links.push(gj.properties);
        }
    });

    bootbox.confirm('Permanently delete these features? This cannot be undone.', function(confirm) {

        if (confirm) {

            map.spin(true);

            $.ajax({
                type : "POST",
                url : $SCRIPT_ROOT + '/_delete_layers',
                data: JSON.stringify({nodes: nodes, links: links}),
                contentType: 'application/json',
                success: function(resp) {
                    if (resp.status_code == 1) {
                        //currentItems.addData(resp.new_gj); // in case any are sent back
                        refreshCurrentItems();
                        notify('success','Success!','Features deleted.');
                    } else {
                        currentItems.addData(polylines); // add back the deleted layers
                        currentItems.addData(points);
                        refreshCurrentItems();
                        notify('danger','Failure!','Something went wrong. Edits not saved.');
                    }
                }
            });
        } else {
            currentItems.addData(polylines); // add back the deleted layers
            currentItems.addData(points);
            refreshCurrentItems();
            notify('info','','Deletion cancelled.');
        }
        map.spin(false);
    });
}

// purge a feature
function purgeFeature(e) {
    var feature = e.relatedTarget.feature
    var msg = 'Permanently delete ' + feature.properties.name + '?<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            map.spin(true);

            $.ajax({
                type : "POST",
                url : $SCRIPT_ROOT + '/_purge_replace_feature',
                data: JSON.stringify(feature),
                contentType: 'application/json',
                success: function(resp) {  

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
                    notify('success','Success!', 'Feature deleted.');
                }
            });
        }
    });
}

//$('#save_as_thumbnail').click(function() {
    //html2canvas($("#map"), {
        //onrendered: function(canvas) {
            //$("body").append(canvas);
        //},
        //allowTaint: true,
        //useCORS: true
    //});
//});