// create the editor
var container = $("#json_editor")[0];
var options = {
    modes: ['code', 'tree'],
    ace: ace
};
var jsoneditor = new JSONEditor(container, options);

// template actions for template manager
var template_all_actions =
    $('<ul>').addClass("dropdown-menu")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share template with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('edit_template', 'Edit', 'Edit this template here.'))
        .append($('<li>').html('<a href="#">Rename</a>'))
        .append($('<li>').html('<a href="#">Attach to network</a>'))
        .append($('<li>').html('<a href="#">Export</a>'))
        .append(menu_item('update_template', 'Update', 'Update this template with a new one.'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('delete_template', 'Delete', 'Permanently delete this template.'));

template_all_dropdown = make_button_div('template_all', template_all_actions);

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

// load the template
$(document).on('click', '.edit_template', function(e) {
    e.preventDefault();
    
    $('#json_editor_wrapper').show()    
    
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    
    var func = 'get_template'
    var args = {'template_id': id}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var template = resp.result;    
    
        jsoneditor.set(template);
        
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

// update master template
$(document).on('click', '.update_template', function(e) {
    e.preventDefault();
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    var msg = 'Update template?<br>The old template will be overwritten, and all new networks will use the updated template.'
    bootbox.confirm(msg, function(confirm) {
        if (confirm) {
            var data = {
                template_id: id,
                template_name: name,
            }
            $.getJSON($SCRIPT_ROOT + '/_update_template', data, function(resp) {
                status = resp.status;
                if (status==1) {
                    notify('success','Success!', 'Template has been updated.');
                }
            });
        };
    });
});

$(document).on('click', '#save_template', function(e) {
    var template = jsoneditor.get();
    var func = 'update_template'
    var args = {'tmpl': template}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        if ("faultcode" in resp.result) {
            notify('danger','Failure!', 'Template not updated.');
        } else {
            notify('success','Success!', 'Template updated.');
            jsoneditor.set(resp.result);
        }        
        
    });
});

$(document).on('click', '#close_editor', function(e) {
    $('#json_editor_wrapper').hide()
});


$( document ).ready(function() {
    update_all_templates();
});