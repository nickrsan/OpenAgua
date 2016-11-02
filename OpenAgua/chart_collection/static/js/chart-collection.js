

// load selected chart
$(function() {
    
    //$(".edit").click( function() {
        //var chartId = Number($(this).parent().attr('id'));
        //$.getJSON( "/_load_chart", { chart_id: chartId }, function(resp) {
            //window.location = resp.redirect;
        //});
    //});
    
    $('#thumbnails').magnificPopup({
      delegate: 'a', // child items selector, by clicking on it popup will open
      type: 'image'
      // other options
    });
    
});