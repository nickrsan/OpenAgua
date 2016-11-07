// a much better notification system using bootstrap-notify: http://bootstrap-notify.remabledesigns.com
// type options are: success, info, warning, and danger

var spinDiv, spinner;

function notify(type, title, message) {
  $.notify({
    // options
    title: "<strong>"+title+" </strong> ",
    message: message
  },{
    // settings
    type: type,
    placement: {
      from: "bottom",
      align: "right"
    }
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

$( function() {
  var opts = {
    lines: 13 // The number of lines to draw
  , length: 28 // The length of each line
  , width: 14 // The line thickness
  , radius: 42 // The radius of the inner circle
  , scale: 0.5 // Scales overall size of the spinner
  , corners: 1 // Corner roundness (0..1)
  , color: '#000' // #rgb or #rrggbb or array of colors
  , opacity: 0.5 // Opacity of the lines
  , rotate: 0 // The rotation offset
  , direction: 1 // 1: clockwise, -1: counterclockwise
  , speed: 1 // Rounds per second
  , trail: 60 // Afterglow percentage
  , fps: 20 // Frames per second when using setTimeout() as a fallback for CSS
  , zIndex: 2e9 // The z-index (defaults to 2000000000)
  , className: 'spinner' // The CSS class to assign to the spinner
  , top: '50%' // Top position relative to parent
  , left: '50%' // Left position relative to parent
  , shadow: false // Whether to render a shadow
  , hwaccel: false // Whether to use hardware acceleration
  , position: 'absolute' // Element positioning
  }
  spinner = new Spinner(opts);
});

function spinOn(message) {
  spinDiv = $('#spinner');
  var spinEl = document.getElementById('spinner');
  spinDiv.html('<p>'+message+'</p>');
  spinDiv.show();
  spinner.spin(spinEl);
}

function spinOff() {
  spinner.spin(false);
  spinDiv.hide();
}