// a much better notification system using bootstrap-notify: http://bootstrap-notify.remabledesigns.com
// type options are: success, info, warning, and danger
function notify(type, title, message) {
        $.notify({
                // options
                title: "<strong>"+title+" </strong> ",
                message: message
        },{
                // settings
                type: type
        });
};

// a generic call to Hydra Server (but still via Flask)
function hydra_call(func, args) {
        var result;
        $.getJSON($SCRIPT_ROOT + '/_hydra_call', {func: func, args: JSON.stringify(args)}, function(data) {
        result = data.result;
        });
        return result;
};
