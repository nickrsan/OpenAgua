var network_actions =
  $('<ul>').addClass("dropdown-menu")
    .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share network with another OpenAgua user">Share</a>'))
    .append($('<li>').attr('role','separator').addClass('divider'))
    .append(menu_item('edit_details', 'Edit details', 'Edit the network name, description and template'))
    .append(menu_item('edit_schematic', 'Edit schematic', 'Edit the network schematic'))
    //.append(menu_item('attach_template', 'Attach', 'Attach a new template to the selected network.'))
    //.append(menu_item('detach_template', 'Detach', 'Detach template from the selected network.'));
    .append(menu_item('upgrade_template', 'Upgrade', 'Upgrade the template to the latest version'))
    .append(menu_item('clean_up_network', 'Clean up', 'Permanently delete previously deactivated features'))
    .append($('<li>').html('<a href="#">Export</a>'))
    .append($('<li>').attr('role','separator').addClass('divider'))
    .append(menu_item('purge_network', 'Delete', 'Permanently delete this network'));

var network_dropdown = make_button_div('network', network_actions);

// update network list
function update_networks(active_project_id, active_network_id) {

  var func = 'get_networks'
  var args = {'project_id': active_project_id, 'include_data':'N'}
  $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
    if ('faultcode' in resp.result) {
      $("#network_list").empty().text("No project loaded.")
    } else {
      populate_networks(resp.result);
    }
  }); 
}

function populate_networks(networks) {

  var netlist = $('#network_list'),
    cell, network_item, dropdown, menu, img, preview, footer, main_action;

  netlist.empty();
  proj_networks = [];

  // add existing networks, if any    
  $.each(networks, function(index, network){

    proj_networks.push(network.name);

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

    main_action = $('<button>')
      .addClass("btn")
      .addClass('study_overview')
      .attr('data-id', network.id)
      .attr('data-name', network.name)
      .text('Overview');

    // keep the following here, in case we switch back to a link
    //main_action = $('<a>')
      //.attr('href','/overview')
      //.text('Overview')

    preview = $('<div>')
      .addClass('network_preview')
      .append(img)
      .append(main_action);

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

  network_item = $('<div>').addClass('network').addClass('add_network');
  network_item.html('<button id="add_network" class="btn btn-default btn-lg">Add network</button>')

  cell.append(network_item)
  netlist.append(cell)

  // go to network overview
  $('.study_overview').click(function(e) {
    var network_id = Number($(this).attr('data-id'));
    $.ajax({
      type : "POST",
      url : '/_load_study',
      data: JSON.stringify({ project_id: active_project_id, network_id: network_id}),
      contentType: 'application/json',
      success: function(resp) {
        window.location.href = "/overview";
      }
    });
  });

  // edit schematic
  $('.study_overview').click(function(e) {
    var network_id = Number($(this).attr('data-id'));
    $.ajax({
      type : "POST",
      url : '/_load_study',
      data: JSON.stringify({ project_id: active_project_id, network_id: network_id}),
      contentType: 'application/json',
      success: function(resp) {
        window.location.href = "/overview";
      }
    });
  });

  // add the binding after networks are shown
  $("button#add_network").click(function() {
    $('#modal_add_network').modal('show');
  });
}

function templatesList() {
  var select = $('<select>').attr('id', 'attach_template_list')
  $.each(all_templates, function(index, template) {
    var option = $('<option>').val(template.id).text(template.name)
    select.append(option)
  })
  return select
}

$(function() {

  update_networks(active_project_id, active_network_id);

  $("#network_list").on("mouseleave", ".network", 
    function () {
      $(this).find('.network_menu .btn-group').removeClass('open');
    }
  );

  // add network
  $("button#add_network_confirm").bind('click', function() {
  var network_name = $('#network_name').val();

  if (_.includes(proj_networks, network_name)) {
    $("#add_network_error").text('Name already in use. Please try again.');
  } else {
    $("#add_network_error").empty();
    var net = {
      name: network_name,
      description: $('#network_description').val(),
      project_id: active_project_id
    }
    var data = {proj_id: active_project_id, net: net, tpl_id: active_template_id}
    $.ajax({
      type : "POST",
      url : '/_add_network',
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: function(resp) {

        if ( resp.status_code == 1 ){
          $('#modal_add_network').modal('hide');
          update_networks(active_project_id, active_network_id);
          $('#network_name').val('');
          notify('success', 'Success!', 'Network "'+network_name+'" added.');
        } else {
          notify('danger', 'Whoops!', 'Something went wrong. Please contact support.')
        }
      }
    });
  }
  });
  
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

});