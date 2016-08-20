$("button#add_project").bind('click', function() {
  $('#modal_add_project').modal('show');
});

$('.project_item').mouseover(function() {
   $(".project_dropdown #"+this.value).show();
});

$('.project_item').mouseout(function() {
   $(".project_dropdown #"+this.value).hide();
});

$("button#add_network").bind('click', function() {
  $('#modal_add_network').modal('show');
});

$('.network_item').mouseover(function() {
   $("#dropdown_network_"+this.value).show();
});

$('.network_item').mouseout(function() {
   $("#dropdown_network_"+this.value).hide();
});

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
            $('#modal_add_project').modal('hide');
            update_projects(active_project_id)
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
            $('#modal_add_network').modal('hide');
            update_networks(active_project_id)
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

// project actions
var project_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share project with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Rename this project.">Rename</a>'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Permanently delete previously deactivated networks.">Clean up</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Permanently delete this project.">Delete</a>'));
        
// network actions
var network_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share network with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#">Edit</a>'))
        .append($('<li>').html('<a href="#">Rename</a>'))
        .append($('<li>').html('<a href="#">Attach template</a>'))
        .append($('<li>').html('<a href="#">Clean up</a>'))
        .append($('<li>').html('<a href="#">Export</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Delete this network from the project, but keep it in the database.">Deactivate</a>'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Permanently delete this network.">Delete</a>'));
        
// template actions
var template_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share template with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#">Edit</a>'))
        .append($('<li>').html('<a href="#">Rename</a>'))
        .append($('<li>').html('<a href="#">Attach to network</a>'))
        .append($('<li>').html('<a href="#">Export</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#">Delete</a>'));
        
function make_button_div(class_type, actions) {
    var btn_div = $('<div>')
    .addClass("btn-group pull-right")
    .append(
        $('<button>')
            .addClass("btn btn-default btn-sm dropdown-toggle")
            .addClass(class_type+"_dropdown")
            .attr("type", "button")
            .attr("data-toggle", "dropdown")
            .text("Action")
            .append($('<span>').addClass("caret"))
    )
    .append(actions);
    return btn_div;
};

project_dropdown = make_button_div('project', project_actions);
network_dropdown = make_button_div('network', network_actions);
template_dropdown = make_button_div('template', template_actions);

// update project list
function update_projects(active_project_id) {
    var func = 'get_projects';
    var args = {};
            
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var projects = resp.result;
        
        if (projects.length) {
            var ul = $('#project_list ul');
            ul.empty();
            $.each(projects, function(index, project){
            
                var dropdown = project_dropdown.clone()
                    .find('button').attr('id', project.id)
                    .end();
            
                var li = $('<li>')
                    .text(project.name)
                    .addClass("list-group-item clearfix")
                    .addClass("project_item")
                    .val(project.id)
                    //.attr("id", project.id)
                    .append(dropdown);
                if (project.id == active_project_id) {
                    li.addClass('active');
                    $("#network_list_description").html('Networks for '+project.name)
                };
                ul.append(li);
            });
        } else {
            $('#project_list').html('<p>No projects. Please create a project.</p>')            
        };
    });
};

// update network list
function update_networks(active_project_id, active_network_id) {
    var func = 'get_networks'
    var args = {'project_id':active_project_id, 'include_data':'N'}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var networks = resp.result;
        
         if (networks.length) {
            var ul = $('#network_list ul');        
            ul.empty();
            $.each(networks, function(index, network){
            
                var dropdown = network_dropdown.clone()
                    .find('button').attr('id', network.id)
                    .end();
            
                var li = $('<li>')
                    .text(network.name)
                    .addClass("list-group-item clearfix")
                    .addClass("network_item")
                    .val(network.id)
                    //.attr("id", network.id)
                    .append(dropdown);
                if (network.id == active_network_id) {
                    li.addClass('active')
                };
                ul.append(li);
            });
        
        } else {
            $('#network_list').text('No networks yet.')            
        };
    });
};

// update template list
function update_templates(active_network_id, active_template_id) {
    var func = 'get_templates'
    var args = {}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var templates = resp.result,
            ul = $('#template_list ul');
        ul.empty();
        $.each(templates, function(index, template){

            var dropdown = template_dropdown.clone()
                .find('button').attr('id', template.id)
                .end();
        
            var li = $('<li>')
                .text(template.name)
                .addClass("list-group-item clearfix")
                .addClass("template_item")
                .val(template.id)
                //.attr("id", template.id)
                .append(dropdown);
            if (template.id == active_template_id) {
                li.addClass('active')
            };
            ul.append(li);
            
        });
    });
};

$( document ).ready(function() {
    update_projects(active_project_id);
    update_networks(active_project_id, active_network_id);
    update_templates(active_network_id, active_template_id);
});