// a much better notification system using bootstrap-notify: http://bootstrap-notify.remabledesigns.com
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
