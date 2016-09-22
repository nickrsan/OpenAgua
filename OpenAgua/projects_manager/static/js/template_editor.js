// create the editor
var container = $("#jsoneditor")[0];
var options = {
    modes: ['code', 'tree'],
    ace: ace
};
var jsoneditor = new JSONEditor(container, options);

// load the template
$(document).on('click', '.edit_template', function(e) {
    e.preventDefault();
    
    var id = Number($(this).attr('data-id'));
    var name = $(this).attr('data-name');
    
    var func = 'get_template'
    var args = {'template_id': id}
    $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(resp) {
        var template = resp.result;    
    
        jsoneditor.set(template);
        
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
            jsoneditor.set(template);
        }        
        
    });
});