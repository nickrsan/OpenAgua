$("button#add_project").bind('click', function() {
  $('#modal_add_project').modal('show');
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
            update_projects(active_project_id);
            notify('success', 'Success!', 'Project "'+name+'" added.');
        }
    });
});

$("button#add_network").bind('click', function() {
  $('#modal_add_network').modal('show');
});
$("button#add_network_confirm").bind('click', function() {
      var net = {
        name: $('#network_name').val(),
        description: $('#network_description').val()
      }
      var tpl_id = $('#net_template').val();
      var data = {net: JSON.stringify(net), tpl_id: tpl_id};
      $.getJSON($SCRIPT_ROOT + '/_add_network', data, function(resp) {
        status_code = resp.result.status_code;
        if ( status_code == -1 ) {
            $("#add_network_error").text('Name already in use. Please try again.');
        } else if ( status_code == 1 ){
            $('#modal_add_network').modal('hide');
            update_networks(active_project_id, active_network_id);
            notify('success', 'Success!', 'Network "'+name+'" added.');
        }
    });
});

// create menu items that result in modals
function menu_item_modal(text, title, target) {
    var li = $('<li>')
        .append($('<a>')
            .attr('type','button')
            .attr('data-target', target)
            .attr('data-toggle', 'modal')
            .attr('title', title)
            .text(text)
        );
    return li;
}

// create menu item
function menu_item(action, text, tooltip) {
    var li = $('<li>')
        .append($('<a>')
            .attr('href', '')
            .attr('type','button')
            .addClass(action)
            .attr('title', tooltip)
            .text(text)
        );
    return li;
}

// project actions
var project_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share project with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Rename this project.">Rename</a>'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Permanently delete previously deactivated networks.">Clean up</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('purge_project', 'Delete', 'Permanently delete this project.'));
        
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

// actions for templates attached to a network
var template_actions =
    $('<ul>').addClass("dropdown-menu")
        .append(menu_item('detach_template', 'Detach', 'Detach template from the selected network.'));

// template actions for template manager
var template_all_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share template with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#">Edit</a>'))
        .append($('<li>').html('<a href="#">Rename</a>'))
        .append($('<li>').html('<a href="#">Attach to network</a>'))
        .append($('<li>').html('<a href="#">Export</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('delete_template', 'Delete', 'Permanently delete this template.'));
        
function make_button_div(class_type, actions) {
    var btn_div = $('<div>')
    .addClass("btn-group pull-right")
    .append(
        $('<button>')
            //.addClass(class_type+"_dropdown")
            .addClass("btn btn-default btn-sm dropdown-toggle")
            .attr("type", "button")
            .attr("data-toggle", "dropdown")
            .text("Action")
            .append($('<span>').addClass("caret"))
    )
    .append(actions);
    return btn_div;
}

project_dropdown = make_button_div('project', project_actions);
network_dropdown = make_button_div('network', network_actions);
template_dropdown = make_button_div('template', template_actions);
template_all_dropdown = make_button_div('template_all', template_all_actions);

// update project list
function update_projects(active_project_id) {
    var func = 'get_projects';
    var args = {}
            
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var projects = resp.result;
        
        if (projects.length) {
            var ul = $('#project_list ul');
            ul.empty();
            $.each(projects, function(index, project){
            
                var dropdown = project_dropdown.clone()
                    //.find('button').attr('id', project.id).end()
                    .find('a')
                        .attr('data-name', project.name)
                        .attr('data-id', project.id)
                    .end();
            
                var li = $('<li>')
                    .text(project.name)
                    .addClass("project")
                    .addClass("list-group-item clearfix")
                    .append(dropdown);
                    
                if (project.id == active_project_id) {
                    li.addClass('active');
                    $("#network_list_description").html('Networks for '+project.name)
                }
                ul.append(li);
            });
        } else {
            $('#project_list').html('<p>No projects. Please create a project.</p>')            
        }
    });
}

// update network list
function update_networks(active_project_id, active_network_id) {
    var func = 'get_networks'
    var args = {'project_id':active_project_id, 'include_data':'N'}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var networks = resp.result;
        
        var network_list = $('#network_list')
        network_list.empty();
        if (networks.length) {
            var ul = $('<ul>').addClass('list-group');
            $.each(networks, function(index, network){
            
                var dropdown = network_dropdown.clone()
                    .find('a')
                    .attr('data-name', network.name)
                    .attr('data-id', network.id)
                    .end();
            
                var li = $('<li>')
                    .text(network.name)
                    .addClass("list-group-item clearfix")
                    .addClass("network_item")
                    .append(dropdown);
                if (network.id == active_network_id) {
                    li.addClass('active')
                    $("#template_list")
                        .attr("data-id", network.id)
                        .attr("data-name", network.name)
                    $("#template_list_description").html('Templates for '+network.name)
                }
                ul.append(li);
            });
            network_list.append(ul)
            
        } else {
            network_list.text('No networks yet.')       
        }
    });
}

// update network templates list
function update_templates(active_network_id, active_template_id) {
    $.getJSON($SCRIPT_ROOT + '/_get_templates_for_network', {network_id: active_network_id}, function(resp) {
        var templates = resp.templates,
            template_list = $('#template_list');
        template_list.empty();
        if (templates.length) {
            var ul = $('<ul>').addClass('list-group');        
        
            $.each(templates, function(index, template){
    
                var dropdown = template_dropdown.clone()
                    .find('a')
                    .attr('data-name', template.name)
                    .attr('data-id', template.id)
                    .end();
            
                var li = $('<li>')
                    .text(template.name)
                    .addClass("list-group-item clearfix")
                    .addClass("template_item")
                    .val(template.id)
                    .append(dropdown);
                if (template.id == active_template_id) {
                    li.addClass('active')
                }
                ul.append(li);    
            });
            template_list.append(ul);
        }
    });
}

// update all templates list
var all_templates
function update_all_templates() {
    var func = 'get_templates'
    var args = {}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        all_templates = resp.result
        var ul = $('#template_list_all ul');
        ul.empty();
        $.each(all_templates, function(index, template){

            var dropdown = template_all_dropdown.clone()
                .find('a')
                .attr('data-name', template.name)
                .attr('data-id', template.id)
                .end();
        
            var li = $('<li>')
                .text(template.name)
                .addClass("list-group-item clearfix")
                .addClass("template_item")
                .val(template.id)
                .append(dropdown);
            ul.append(li);
            
        });
    });
};

// purge project
$(document).on('click', '.purge_project', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var msg = 'Permanently delete project "'+name+'?"<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            result = hydra_call('purge_project', {project_id: id});
            update_projects(active_project_id);
            update_networks(active_project_id, active_network_id);
            notify('success','Success!', 'Project "'+name+'" has been permanently deleted.');
        };
    });
});

// attach template
$(document).on('click', '.attach_template', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var title = 'Select a template.'
    bootbox.dialog({
      message: templatesList(),
      title: title,
      buttons: {
        cancel: {
          label: "Cancel",
          className: "btn-default",
        },
        main: {
          label: "OK",
          className: "btn-primary",
          callback: function() {
            var selected = $( "select#attach_template_list option:selected" )
            var template_id = Number(selected.val())
            var template_name = selected.text()
            var call = 'apply_template_to_network'
            var args = {
                template_id: template_id,
                network_id: active_network_id
            }
            result = hydra_call(call, args);
            update_templates(active_network_id, active_template_id);
            notify('success','Success!', 'Template "'+template_name+'" has been attached.');
          }
        }
      }
    });
});

function templatesList() {
    var select = $('<select>').attr('id', 'attach_template_list')
    $.each(all_templates, function(index, template) {
        var option = $('<option>').val(template.id).text(template.name)
        select.append(option)
    })
    return select
}

// purge network
$(document).on('click', '.purge_network', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var msg = 'Permanently delete network "'+name+'?"<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            result = hydra_call('purge_network', {network_id: id});
            update_networks(active_project_id, active_network_id);
            notify('success','Success!', 'Network "'+name+'" has been permanently deleted.');
        };
    });
});

// delete template
$(document).on('click', '.delete_template', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var msg = 'Permanently delete template "'+name+'?"<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            result = hydra_call('delete_template', {template_id: id});
            update_templates(active_network_id, active_template_id);
            notify('success','Success!', 'Template "'+name+'" has been permanently deleted.');
        };
    });
});

$( document ).ready(function() {
    update_projects(active_project_id);
    update_networks(active_project_id, active_network_id);
    update_templates(active_network_id, active_template_id);
    update_all_templates();
});