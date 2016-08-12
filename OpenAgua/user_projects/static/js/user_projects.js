

$("button#add_project").bind('click', function() {
  $('#modal_add_project').modal('show');
});

<!--$('.project_item').mouseover(function() {-->
   <!--$("#dropdown_project_"+this.value).show();-->
<!--});-->

<!--$('.project_item').mouseout(function() {-->
   <!--$("#dropdown_project_"+this.value).hide();-->
<!--});-->

$("button#add_network").bind('click', function() {
  $('#modal_add_network').modal('show');
});

<!--$('.network_item').mouseover(function() {-->
   <!--$("#dropdown_network_"+this.value).show();-->
<!--});-->

<!--$('.network_item').mouseout(function() {-->
   <!--$("#dropdown_network_"+this.value).hide();-->
<!--});-->

$("button#add_project_confirm").bind('click', function() {
      var proj = {
        name: $('#project_name').val(),
        description: $('#project_description').val()};
        activate: $('#activate_project').is(':checked');
      $.getJSON($SCRIPT_ROOT + '/_add_project', {proj: JSON.stringify(proj)}, function(resp) {
        status_code = resp.result.status_code;
        if ( status_code == -1 ) {
            $("#add_project_error").text('Name already in use. Please try again.');
        } else if ( status_code == 1 ){
            $("#project_list ul").append('<li class="list-group-item project_item>'+proj.name+'</li>');
            $('#modal_add_project').modal('hide');
        };
    });
});

$("button#add_network_confirm").bind('click', function() {
      var net = {
        name: $('#network_name').val(),
        description: $('#network_description').val()
      };
      var tpl_id = $('#net_template').val();
      var data = {net: JSON.stringify(net), tpl_id: tpl_id};
      $.getJSON($SCRIPT_ROOT + '/_add_network', data, function(resp) {
        status_code = resp.result.status_code;
        if ( status_code == -1 ) {
            $("#add_network_error").text('Name already in use. Please try again.');
        } else if ( status_code == 1 ){
            $("#network_list ul").append('<li>'+net.name+'</li>');
            $('#modal_add_network').modal('hide');
        };
    });
});

function purge_project(project_id) {
  $('#modal_purge_project').val(project_id);
  $('#modal_purge_project').modal('show');
};

$('button#purge_project_confirm').bind('click', function() {
  var project_id = $('#modal_purge_project').val()
  $.getJSON($SCRIPT_ROOT+'/_purge_project', {project_id: project_id}, function(data) {
      status_code = data.result.status_code;
      if ( status_code == 1 ) { // there should be only success
          $("#purge_project_name").text("");
          $("#modal_purge_project").val(-1);
          $('#project_list ul #'+project_id).remove();
          $("#modal_purge_project").modal("hide");
      };
  });
});