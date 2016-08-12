var myInterval;

$('button#run_app').bind('click', function() {

    $(this).button('loading');

    // 1. get run data and store it as json
    // in the future, we will get this from a form, scenario builder, etc.
    args = {
        start_date: 5,
        end_date: 10,
    };
    
    // 2. call run app route, sending json data with scenario information
    $.getJSON($SCRIPT_ROOT+'/_run_model', {'params': JSON.stringify(args)}, function(resp) {
        status = resp.result.status;
        model_progress(status);
    });
});

//$( document ).ready(model_progress());

function model_progress(status) {
    if (status == -1) {
        $("button#run_app").button('reset')
        $("#status_message").text("There's something wrong.")
    } else if (status == 0) {
        $("button#run_app").button('reset')
        $("#status_message").text("No model running.")
    } else if (status == 1) {
        $("#status_message").text("Model running...");
        myInterval = setInterval(update_model_progress, 1000)
    } else if (status == 2) {
        $("button#run_app").button('reset')
        $("#status_message").text("Model complete!")      
    };
};

function update_model_progress() {
    var width;
    $.getJSON(
        $SCRIPT_ROOT+'/_model_progress',
        function(data) {
            status = data.result.status;
            progress = data.result.progress;
        });
        width = "width:"+progress+"%";
        $('#model_run_progress').attr('style',width);
        $("#model_run_progress").text(progress+"%");
        if (progress == 100) {
            clearInterval(myInterval)
            $("#status_message").text("Model complete!");
            $("button#run_app").button('reset')
        }
};
