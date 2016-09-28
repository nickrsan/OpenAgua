var myInterval;

$('button#run_model').bind('click', function() {

    $(this).button('loading');
    $('button#stop_model').show();
    update_progress_bar(0);

    // 1. get run data and store it as json
    commandData = {
        ti: $('#initial_timestep').data().date,
        tf: $('#final_timestep').data().date,
        sol: 'glpk'
    }
    
    $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: $SCRIPT_ROOT+'/_run_model',
      data: JSON.stringify(commandData),
      success: function (resp) {
        model_progress(resp.status);
      },
      dataType: "json"
    });    
    
});

//$( document ).ready(update_model_progress());

// stop the model
$('button#stop_model').bind('click', function() {
    $('#modal_stop_model').show();
});

$('button#stop_model_cancel').bind('click', function() {
    $('#modal_stop_model').hide();
});

$('button#stop_model_confirm').bind('click', function() {
    // 1. get run data and store it as json
    args = {
        app_name: 'openaguamodel'
    };
    
    // 2. call run app route, sending json data with scenario information
    //$.getJSON(
        //$SCRIPT_ROOT+'/_stop_model',
        //{'user_args': JSON.stringify(args)},
        //function(resp) {
            //status = resp.result.status;
            clearInterval(myInterval);
            update_progress_bar(0);
            $("#modal_stop_model").hide();
            $("button#run_model").button('reset');
            $("button#stop_model").hide();
            $("#status_message").text("Model stopped!");
    //});
});

// FUNCTIONS

function model_progress(status) {
    if (status == -1) {
        $("button#run_model").button('reset');
        $("#status_message").text("There's something wrong.");
    } else if (status == 0) {
        $("button#run_model").button('reset');
        $("#status_message").text("No model running.");
    } else if (status == 1) {
        $("#status_message").text("Model running...");
        //myInterval = setInterval(update_model_progress, 1000);
    } else if (status == 2) {
        $("button#run_model").button('reset');
        $("#status_message").text("Model complete!");  
    };
};

function update_model_progress() {
    var width;
    $.getJSON(
        $SCRIPT_ROOT+'/_model_progress',
        function(resp) {
            progress = resp.result.progress;
        });
    update_progress_bar(progress);
    if (progress == 100) {
        clearInterval(myInterval)
        $("#status_message").text("Model complete!");
        $("button#run_model").button('reset')
    };
};

function update_progress_bar(progress) {
    width = "width:"+progress+"%";
    $('#model_run_progress').attr('style',width);
    $("#model_run_progress").text(progress+"%");
};