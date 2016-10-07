$(function() {

  // Get JSON-formatted data from the server
  $.getJSON("/_load_pivot_data", function( resp ) {
      var pivotData = resp.data;
      
      $("#output").pivotUI(
        pivotData, {
          //rows: ['scenario'],
          //cols: ['year'],
          //vals: ['value'],
          //aggregatorName: "Average",
          //rendererName: "Line Chart",
          renderers: $.extend(
              $.pivotUtilities.renderers, 
            $.pivotUtilities.c3_renderers
          )
        });
    });

});
