$( function() {
  $('#locale').on('changed.bs.select', function(e) {
    $.get('/_change_locale', {'locale': $('#locale option:selected').val()}, function() {
      location.reload();
    });
  });
});