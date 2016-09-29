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
        update_status(1, 0);
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
    // this doesn't really stop the model, but it stops the javascript
    clearInterval(myInterval);
    $("#status_message").text("Model stopped.");
    $("button#run_model").button('reset');
    $("button#stop_model").hide();
    $("modal_stop_model").hide();
    
});

// FUNCTIONS

function check_progress() {
    $.getJSON($SCRIPT_ROOT+'/_model_progress', function(resp) {
        update_status(resp.status, resp.progress);
    });
}

function update_status(status, progress) {
    var msg = '';
    switch (status) {
        case -2: // something wrong during checking
            msg = "Checking model failed.";
            $("button#run_model").button('reset');
            $("button#stop_model").hide();
            update_progress_bar(0);
            clearInterval(myInterval);
            break;
        case -1:
            msg = "Model initialization failed.";
            $("button#run_model").button('reset');
            $("button#stop_model").hide();
            update_progress_bar(0);
            clearInterval(myInterval);
            break;
        case 1: // just started
            msg = "Model started...";
            $("button#stop_model").show();
            update_progress_bar(0);
            myInterval = setInterval(check_progress, 2000);
            break;
        case 2: // running or still starting
            update_progress_bar(progress);
            if (progress == 0) {
                msg = 'Still starting up...'            
            } else {
                msg = 'Model running...'            
            }
            break;
        case 3: // complete
            msg = "Model complete!";
            $("button#run_model").button('reset');
            $("button#stop_model").hide();
            update_progress_bar(progress);
            clearInterval(myInterval);
            break;
        default:
            msg = "Something has gone terribly wrong!";
            $("button#run_model").button('reset');
            $("button#stop_model").hide();
            update_progress_bar(0);
            clearInterval(myInterval);
            break;
    }
    $("#status_message").text(msg);
}

function update_progress_bar(progress) {
    width = "width:"+progress+"%";
    $('#model_run_progress').attr('style',width);
    $("#model_run_progress").text(progress+"%");
}