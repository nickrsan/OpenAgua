var jsonEditorDiv = $('#json_editor');
var jsoneditor, options;

// template actions for template manager
var template_all_actions =
    $('<ul>').addClass("dropdown-menu pull-right")
        .append($('<li>').html('<a href="#" data-toggle="tooltip" title="Share template with another OpenAgua user.">Share</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('edit_template_jsoneditor', 'View/edit (JSON)', 'Edit this template using JSON Editor.'))
        //.append(menu_item('edit_template_jsonform', 'View/edit (form)', 'Edit this template using JSON Editor.'))
        .append($('<li>').html('<a href="#">Duplicate</a>'))
        .append($('<li>').html('<a href="#">Export</a>'))
        .append($('<li>').attr('role','separator').addClass('divider'))
        .append(menu_item('delete_template', 'Delete', 'Permanently delete this template.'));

template_all_dropdown = make_button_div('template_all', template_all_actions);

// update all templates list
var all_templates
function update_templates() {
    var func = 'get_templates'
    var args = {}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        all_templates = resp.result
        //var ul = $('#template_list_all ul');
        //ul.empty();
        var table = $('#template_list')
        table.empty();
        $.each(all_templates, function(index, template){

            var tr = new $('<tr>');

            var dropdown = template_all_dropdown.clone()
                .find('a')
                .attr('data-name', template.name)
                .attr('data-id', template.id)
                .end();
        
            //var li = $('<li>')
                //.text(template.name)
                //.addClass("list-group-item")
                //.addClass("template_item")
                //.val(template.id)
                //.append(dropdown);
            //ul.append(li);
            tr.append($('<td>').text(template.id))
                .append($('<td>').text(template.name))
                .append($('<td>').append(dropdown));
            table.append(tr);
        });
    });
};

// load the template
$(document).on('click', '.edit_template_jsoneditor', function(e) {
    e.preventDefault();
    
    // create the editor
    jsonEditorDiv.empty();
    options = {
        modes: ['view', 'form', 'tree', 'code'],
        ace: ace
    };
    jsoneditor = new JSONEditor(jsonEditorDiv[0], options);
    jsoneditor.setMode('view');
    //jsoneditor.setSchema(schema);
    
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
            update_templates();
            notify('success','Success!', 'Template "'+name+'" has been permanently deleted.');
        };
    });
});

$(document).on('click', '#save_as_new_template', function(e) {    
    $.ajax({
        type : "POST",
        url : '/_save_as_new_template',
        data: JSON.stringify({template: jsoneditor.get()}),
        contentType: 'application/json',
        success: function(resp) {            
            var result = JSON.parse(resp.result)
            if ('faultcode' in result) {
                notify('danger', result.faultcode, result.faultstring);
            } else {
                notify('success', 'Success!', 'New template created.');
                jsoneditor.set(result);
            }
        }
    });
});

$(document).on('click', '#modify_template', function(e) {    
    $.ajax({
        type : "POST",
        url : '/_modify_template',
        data: JSON.stringify({template: jsoneditor.get()}),
        contentType: 'application/json',
        success: function(resp) {            

            if (resp.result == -1) {
                notify('danger','Failure!', 'Template not saved.');
            } else {
                notify('success','Success!', 'Template updated.');
                jsoneditor.set(resp.result);
            }
        }
    });
});

$(document).on('click', '#close_editor', function(e) {
    $('#json_editor_wrapper').hide()
});


$( document ).ready(function() {
    update_templates();
});