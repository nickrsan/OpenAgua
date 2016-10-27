var c = $('#controllers')

function makeselect(id, options) {
  var select = $('<select>');
  $.each(options, function(index, item) {
    select.append($('<option>').val(item).text(item))
  });
  select
    .attr('id', id)
  return select
}

$( document ).ready( function () {

  $("#charttype").select2();

  if ($('#charttype').val() == 'line') {
  
  var xaxis = makeselect('xaxis', ['Time series', 'Annual time series', 'Periodic time series', 'Features', 'Scenarios'])
  
  c.append($('<p>').append(xaxis.css('width','100%')))
  
  $("#xaxis").select2();
  
  }

});