

// load selected chart
$(function() {
    
    $(".edit").click( function() {
        var chartId = Number($(this).parent().attr('id'));
        $.getJSON( "/_load_chart", { chart_id: chartId }, function(resp) {
            window.location = resp.redirect;
        });
    });
    
});