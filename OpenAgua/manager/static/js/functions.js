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

function make_button_div(class_type, actions) {
    var btn_div = $('<div>')
    .addClass("btn-group")
    .append(
        $('<button>')
            //.addClass(class_type+"_dropdown")
            .addClass("btn btn-default btn-sm dropdown-toggle")
            .attr("type", "button")
            .attr("data-toggle", "dropdown")
            //.text("Action")
            .append($('<i>').addClass("fa fa-bars"))
    )
    .append(actions);
    return btn_div;
}