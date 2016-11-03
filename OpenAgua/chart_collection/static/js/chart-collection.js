

// load selected chart
$(function() {

    $(".edit").click( function() {
        var chartId = $(this).data('id');
        $.getJSON( "/_load_chart", { chart_id: chartId }, function(resp) {
            window.location = resp.redirect;
        });
    });

    $('#thumbnails').magnificPopup({
        delegate: 'a', // child items selector, by clicking on it popup will open
        type: 'image',
        // other options
        gallery: {
            enabled: true,
            navigateByImgClick: true,
            preload: [1,1]
        }
    });
    
    $('.trash').click( function() {
        var chart_id = $(this).data('id');
        var col = $(this).closest(".col");
        bootbox.confirm('Are you sure you want to delete this chart?',
            function(confirm) {
                if (confirm) {
                     $.ajax({
                        type : "POST",
                        url : '_delete_chart',
                        data: JSON.stringify({chart_id: chart_id}),
                        contentType: 'application/json',
                        success: function(resp) {
                            if (resp.result === 1) {
                                col.remove();
                                notify('success', 'Success!', 'Chart deleted.');
                            } else {
                                notify('warning', 'Failure!', 'Something went wrong. Chart not deleted.');
                            }
                        }
                    });
                }
            }
        );
    })

});