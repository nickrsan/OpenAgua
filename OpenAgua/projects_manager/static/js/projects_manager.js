$( document ).ready(function() {
    update_projects(active_project_id);
    update_networks(active_project_id, active_network_id);
    
    $("#network_list").on("mouseenter", ".network_item", 
        function () {
            $(this).css("background-color", "grey");
            $(this).find('img').hide();
        }
    );
    $("#network_list").on("mouseleave", ".network_item", 
        function () {
            $(this).css("background-color", "white");
            $(this).find('img').show();
        }
    );
    
});

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

// project actions
var project_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share project with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Rename this project.">Rename</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('purge_project', 'Delete', 'Permanently delete this project.'));
        
// network actions
var network_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share network with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('edit_schematic', 'Edit schematic', 'Edit the network schematic'))
        .append(menu_item('edit_details', 'Edit details', 'Edit the network name, description and template'))
        //.append(menu_item('attach_template', 'Attach', 'Attach a new template to the selected network.'))
        //.append(menu_item('detach_template', 'Detach', 'Detach template from the selected network.'));
        .append(menu_item('upgrade_template', 'Upgrade', 'Upgrade the template to the latest version'))
        .append(menu_item('clean_up_network', 'Clean up', 'Permanently delete previously deactivated features.'))
        .append($('<li>').html('<a href="#">Export</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('purge_network', 'Delete', 'Permanently delete this network'));

project_dropdown = make_button_div('project', project_actions);
network_dropdown = make_button_div('network', network_actions);

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
        populate_networks(networks);
    });
}

function populate_networks(networks) {

    var N = networks.length
    var netlist = $('#network_list')
    netlist.empty();
    if (N) {
        
        $.each(networks, function(index, network){
        
            var cell = $('<div>').addClass('network_cell col col-sm-6 col-md-4 col-lg-3');
            
            var network_item = $('<div>').addClass('network_item');
        
            var dropdown = network_dropdown.clone()
                .find('a')
                .attr('data-name', network.name)
                .attr('data-id', network.id)
                .end();
            var menu = $('<div>').addClass('network_actions').append(dropdown);
                
            var img = $('<img>').attr('src', network_img).css('width', '90%');
        
            var preview = $('<div>')
                .append(img)
                .after($('<a>').attr('href','/overview').text('Network overview'));
                
            var name = $('<div>')
                .addClass("network_name")
                .text(network.name)
            
            network_item
                .append(menu)
                .append(preview)
                .append(name);
            
            if (network.id == active_network_id) {
                network_item.addClass('active')
            }
            
            cell.append(network_item)
            netlist.append(cell)
            
        });
        
    } else {
        netlist.text('No networks yet.')       
    }
}

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

// clean up network
$(document).on('click', '.clean_up_network', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var msg = 'Permanently delete previously removed features?<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            result = hydra_call('clean_up_network', {network_id: id});
            notify('success','Success!', 'Network has been cleaned up.');
        };
    });
});

// upgrade template
$(document).on('click', '.edit_schematic', function(e) {
    var network_id = Number($(this).attr('data-id'));
    $.get('/_edit_schematic', { network_id: network_id }, function() {
        window.location.href = "/network_editor";    
    });
});

// upgrade template
$(document).on('click', '.upgrade_template', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var msg = 'Upgrade template?<br><b>WARNING: This cannot be undone!<b>'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            var data = {
                template_id: id,
                network_id: active_network_id
            }
            $.getJSON($SCRIPT_ROOT + '/_upgrade_template', data, function(resp) {
                status = resp.status;
                if (status==1) {
                    notify('success','Success!', 'Template has been upgraded.');
                }
            });
        };
    });
});
