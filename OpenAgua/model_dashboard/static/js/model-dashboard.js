var scenarioLog,
  showScenarioDetails,
  myInterval,
  interval = 2500,
  scen_log = '';

$(function() {
  $("#progress_bars").on('click', '.btn-scenario-log', function() {
    loadScenarioLog(scen_log);
    showScenarioDetails = true;
  });

  $('button#run_model').click(function() {
  
    $('.log').empty();
    scen_log = '';
  
    var scids = [];
    $("#scenarios option:selected").each(function() {
      scids.push(Number($(this).val()))
    });
  
    if (scids.length) {
  
      $(this).button('loading');
      $('button#stop_model').show();
      //$('button#view_run_log').show();
      update_progress_bar(0);
  
      // collect run parameters here
      var commandData = {
        scids: scids,
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
    } else {
      notify('danger', 'Error!', 'No scenarios selected. Please try again.')    
    }
  
  });
  
  //$( document ).ready(update_model_progress());
  
  // stop the model
  $('button#stop_model').click(function() {
    bootbox.confirm({
      message: 'Are you sure you want to stop this model run? Model results may not be complete.', 
      callback: function(result) {
        if (result) {
          clearInterval(myInterval);
          $("#status_message").text("Model stopped");
          $("button#run_model").button('reset');
          $("button#stop_model").hide();
  
          notify('success', 'Success!', 'Model stopped.');
        }
      }
      });
  });
});

// FUNCTIONS

function interval(func, wait, times){
  var interv = function(w, t){
    return function(){
      if(typeof t === "undefined" || t-- > 0){
        setTimeout(interv, w);
        try{
          func.call(null);
        }
        catch(e){
          t = 0;
          throw e.toString();
        }
      }
    };
  }(wait, times);

  setTimeout(interv, wait);
};


function check_progress() {
  $.getJSON($SCRIPT_ROOT+'/_model_progress', function(resp) {
    $('#main_log').text(resp.main_log).animate({scrollTop:$('#main_log')[0].scrollHeight}, 1000)
    scen_log = resp.scen_log;
    if (showScenarioDetails) {
      loadScenarioLog(scen_log);
    }
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
      model_stopped = false;
      update_progress_bar(0);
      myInterval = setInterval(check_progress, interval);
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

function loadScenarioLog(scen_log) {
  $("#scen_log").text(scen_log)
    .animate({scrollTop:$("#scen_log")[0].scrollHeight}, 1000);
}