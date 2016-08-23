var editor = ace.edit("editor");
editor.setTheme("ace/theme/chrome");
editor.getSession().setMode("ace/mode/python");
document.getElementById('editor').style.fontSize='16px';

var feature_id;
var scenario_id;
var template_id;
var attr_id;
var type_id;
$(document).ready(function(){

  // load the scenarios
  $('#scenarios').on('hide.bs.select', function (e) {
    scenario_id = Number($('#scenarios option:selected').attr("data-tokens"));
    $('#features').attr('disabled',false);
    $('#features').selectpicker('refresh');
  });

  // load the variables when the feature is clicked
  $('#features').on('hide.bs.select', function (e) {
    var data_tokens = $('#features option:selected').attr("data-tokens");
    var feature_data = $.parseJSON(data_tokens);
    type_id = feature_data.type_id;
    feature_id = feature_data.feature_id;
    feature_type = feature_data.feature_type;
    if (!isNaN(feature_id)) {
      load_variables(type_id);
    };    
  });

  // load the variable data when the variable is clicked
  $('#variables').on('hide.bs.select', function (e) {
    attr_id = Number($('#variables option:selected').attr("data-tokens"));
    if (!isNaN(attr_id)) {
      load_data(feature_id, feature_type, attr_id, scenario_id);
    };    
  });  
  
});

// load the variables (aka attributes in Hydra)
function load_variables(type_id) {
  var data = {type_id: type_id}
  $.getJSON($SCRIPT_ROOT+'/_get_variables', data, function(resp) {
      var variables = resp.result;
      var vpicker = $('#variables')
      vpicker.empty();
      $.each(variables, function(index, variable) {
        vpicker
          .append($('<option>')
            .attr('data-tokens',variable.attr_id)
            .text(variable.attr_name.replace(/_/g,' '))
          );
      });
      vpicker.attr('disabled',false);
      vpicker.selectpicker('refresh');
  });
};

// load the variable data
function load_data(feature_id, feature_type, attr_id, scenario_id) {
  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    attr_id: attr_id,
    scen_id: scenario_id
  };
  $.getJSON($SCRIPT_ROOT+'_get_variable_data', data, function(resp) {
    var attr_data = resp.result;
    var value;
    if (attr_data != null) {
      value = attr_data.value.value;
    } else {
      value = '';
    };
    editor.setValue(value);
    editor.gotoLine(1);

  });
};