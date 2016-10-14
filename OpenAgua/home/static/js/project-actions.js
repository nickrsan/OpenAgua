var proj_networks = [];

var project_actions =
  $('<ul>').addClass("dropdown-menu")
    .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share project with another OpenAgua user.">Share</a>'))
    .append($('<li>').attr('role','separator').addClass('divider'))
    .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Rename this project.">Rename</a>'))
    .append($('<li>').attr('role','separator').addClass('divider'))
    .append(menu_item('purge_project', 'Delete', 'Permanently delete this project.'));

var project_dropdown = make_button_div('project', project_actions);

// update project list
function update_projects() {
  var func = 'get_projects';
  var args = {}

  $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {

    var projects = resp.result;
    populate_projects(projects);
  });
}

function populate_projects(projects) {

  var projlist = $('#project_list'),
  cell, project_item, proj_btn, dropdown, menu, preview, footer;

  projlist.empty();

  $.each(projects, function(index, project){  

    cell = $('<div>').addClass('project-col col col-sm-12 col-md-12 col-lg-12');

    proj_btn = $('<button>')
      .addClass("project-btn btn btn-default")
      .attr('data-id', project.id)
      .attr('data-name', project.name)
      .text(project.name);    

    project_item = $('<div>').addClass('project');
    project_item.append(proj_btn);

    // add the menu
    dropdown = project_dropdown.clone()
      .addClass('dropdown-menu-right')
      .find('a')
      .attr('data-name', project.name)
      .attr('data-id', project.id)
      .end();
    menu = $('<div>').addClass('project-menu')
      .append(dropdown);
    project_item.append(menu);

    if (project.id === active_project_id) {
      project_item.addClass('active')
      $('#network_list_description').html('Networks for <span class="project-name">' + project.name + '</span>')
    }

    cell.append(project_item)
    projlist.append(cell)

  });

  cell = $('<div>').addClass('project-col col col-sm-12 col-md-12 col-lg-12');

  project_item = $('<div>').addClass('project').addClass('add_project');
  project_item.html('<button id="add_project" class="btn btn-default">Add project</button>')

  cell.append(project_item)
  projlist.append(cell)
}

$(function() {
    update_projects(active_project_id);
    $("#project_list").on("mouseenter", ".project", 
      function () {
        $(this).find('.project-menu').show();
      }
    );
    $("#project_list").on("mouseleave", ".project", 
      function () {
        $(this).find('.project-menu').hide();
        $(this).find('.project-menu .btn-group').removeClass('open');
      }
    );

    $('#projects').on('click', '.project-btn', function() {
      active_project_id = Number($(this).attr('data-id'));
      active_network_id = null;
      update_projects(active_project_id)
      update_networks(active_project_id, active_network_id);
    });    
  
    $(document).on('click', '#add_project', function() {
      $('#modal_add_project').modal('show');
    });

    $(document).on('click', "#add_project_confirm", function() {
      var project_name = $('#project_name').val();
      var data = {proj: {name: project_name, description: $('#project_description').val()}}

      $.ajax({
        type : "POST",
        url : '/_add_project',
        data: JSON.stringify(data),
        contentType: 'application/json',
        success: function(resp) {            

          status_code = resp.status_code;
          if ( status_code == -1 ) {
            $("#add_project_error").text('Name already in use. Please try again.');
          } else if ( status_code == 1 ) {
            $('#modal_add_project').modal('hide');
            active_project_id = resp.new_project_id;
            update_projects(active_project_id);
            notify('success', 'Success!', 'Project "'+project_name+'" added.');
          }
        }
      });
    });
    
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
        }
      });
    });
});