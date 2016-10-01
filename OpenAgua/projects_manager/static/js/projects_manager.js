$( document ).ready(function() {
    update_projects(active_project_id);
    update_networks(active_project_id, active_network_id);
    
    $("#network_list").on("mouseleave", ".network", 
        function () {
            $(this).find('.network_menu .btn-group').removeClass('open');
        }
    );
    
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
        populate_projects(projects);
    });
}

function populate_projects(projects) {
        
        //var ul = $('#project_list ul');
        //ul.empty();

    var projlist = $('#project_list'),
    cell, project_item, dropdown, menu, preview, footer;

    projlist.empty();
        
    $.each(projects, function(index, project){

        cell = $('<div>').addClass('row').append(
            $('<div>').addClass('project-col col col-sm-12 col-md-12 col-lg-12'));
        
        project_item = $('<div>').addClass('project');
    
        dropdown = project_dropdown.clone()
            .find('a')
            .attr('data-name', project.name)
            .attr('data-id', project.id)
            .end();
        menu = $('<div>').addClass('project_menu')
            .append(dropdown);
    
        preview = $('<div>')
            .addClass('project_preview')
            .text(project.name)
            .append($('<a>')
                .addClass('main_action')
                    .attr('href','/overview')
                        .text('View networks'));
            
        footer = $('<div>')
            .addClass("project_footer")
            .addClass("pull-right")
            
        
        project_item
            .append(menu)
            .append(preview)
            .append(footer);
        
        if (project.id == active_project_id) {
            project_item.addClass('active')
        }
        
        cell.append(project_item)
        projlist.append(cell)
        
    });
    
        // add a button to create a new network
        //cell = $('<div>').addClass('network-col col col-sm-6 col-md-4 col-lg-3');
        
        //network_item = $('<div>').addClass('network').addClass('add_network_cell');
        //network_item.html('<button id="add_network" class="btn btn-default btn-lg">Add network</button>')
        
        //cell.append(network_item).addClass('new_network_cell')
        //netlist.append(cell)

        // OLD SECTION:

        //$.each(projects, function(index, project){
        
            //var dropdown = project_dropdown.clone()
                ////.find('button').attr('id', project.id).end()
                //.find('a')
                    //.attr('data-name', project.name)
                    //.attr('data-id', project.id)
                //.end();
        
            //var hr = $('<div>')
                //.addClass('connector')
                ////.addClass('pull-right')
                //.html('<span class="glyphicon glyphicon-arrow-right"></span')
            //var div = $('<div>')
                //.addClass("project")
                //.text(project.name);
            //var li = $('<li>').addClass("list-group-item").append(div);
                
            //if (project.id == active_project_id) {
                //li.addClass('active').append(hr);
                //$("#network_list_description").html('Networks for '+project.name);
            //}
            //ul.append(li);
        //});            
        
    //});

    $("button#add_project").bind('click', function() {
      $('#modal_add_project').modal('show');
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

    var netlist = $('#network_list'),
        cell, network_item, dropdown, menu, img, preview, footer;

    netlist.empty();
    
    // add existing networks, if any    
    $.each(networks, function(index, network){
    
        cell = $('<div>').addClass('network-col col col-sm-6 col-md-4 col-lg-3');
        
        network_item = $('<div>').addClass('network');
    
        dropdown = network_dropdown.clone()
            .find('a')
            .attr('data-name', network.name)
            .attr('data-id', network.id)
            .end();
        menu = $('<div>').addClass('network_menu')
            .append(dropdown);

        //var img = $('<img>').attr('src', network_img).css('width', '100%');
        img = $('<i>').addClass('fa fa-map-o');
    
        preview = $('<div>')
            .addClass('network_preview')
            .append(img)
            .append($('<a>')
                .addClass('main_action')
                    .attr('href','/overview')
                        .text('Overview'));
            
        footer = $('<div>')
            .addClass("network_footer")
            .text(network.name)
        
        network_item
            .append(menu)
            .append(preview)
            .append(footer);
        
        if (network.id == active_network_id) {
            network_item.addClass('active')
        }
        
        cell.append(network_item)
        netlist.append(cell)
        
    });
    
    // add a button to create a new network
    cell = $('<div>').addClass('network-col col col-sm-6 col-md-4 col-lg-3');
    
    network_item = $('<div>').addClass('network').addClass('add_network_cell');
    network_item.html('<button id="add_network" class="btn btn-default btn-lg">Add network</button>')
    
    cell.append(network_item).addClass('new_network_cell')
    netlist.append(cell)
    
    // add the binding after networks are shown
    $("button#add_network").click(function() {
      $('#modal_add_network').modal('show');
    });

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
