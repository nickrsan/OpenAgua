$('button#run_app').bind('click', function() {

    // 1. get run data and store it as json
    // in the future, we will get this from a form, scenario builder, etc.
    args = {
        app_name: session['app_name'],
        user_id: 1, //temporary
        start_date: 5,
        end_date: 10,
        scenarios: ['base_scenario']
    };
    
    // 2. call run app route, sending json data with scenario information
    $.getJSON($SCRIPT_ROOT+'/_run_model', {'model': args}, function(data) {
        response = data.result.status;
        if (response == 1) {
            model_progress
        } else {
            $("#run-progress").text("Something went wrong.")
        };
    });
});

$( document ).ready(model_progress());

function model_progress() {
    //var status = get_model_status();
    var status = 1;
    if (status == 1) {
        update_model_progress;
        $("#run-progress").show();
        while (status == 1) {
            setTimeout(update_model_progress, 2000);
            //status = get_model_status()
            status = 2;
        };
    } else if (status == 0) {
        $("#status-message").text("No model running.")
    } else if (status == -1) {
        $("#status-message").text("There's something wrong with the model.")
    } else if (status == 2) {
        $("#status-message").text("Model complete!")      
    };
};

function get_model_status() {
    $.getJSON( $SCRIPT_ROOT+'/_model_status', function(data) { var status = data.result.status });
    return status;
};

function update_model_progress() {
    var progress,
        width;
    $.getJSON(
        $SCRIPT_ROOT+'/_model_progress',
        function(data) {
            progress = data.result.progress;
            width = "width:"+progress+"%";
            $('#model-run-progress').attr('style',width);
            $("#model-run-progress").text(progress+"%");
            if (progress==100) {$("#status-message").text("Model complete!")}
        });
};
