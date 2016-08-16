var myInterval;

$('button#run_app').bind('click', function() {

    $(this).button('loading');

    // 1. get run data and store it as json
    args = {
        ti: $('#initial_timestep').data().date,
        tf: $('#final_timestep').data().date,
    };
    
    // 2. call run app route, sending json data with scenario information
    $.getJSON(
        $SCRIPT_ROOT+'/_run_model',
        {'user_args': JSON.stringify(args)},
        function(resp) {
            status = resp.result.status;
            model_progress(status);
    });
});

//$( document ).ready(update_model_progress());

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
        function(resp) {
            progress = resp.result.progress;
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
