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
  return false;
});
