var editor = ace.edit("editor");
editor.setTheme("ace/theme/chrome");
editor.getSession().setMode("ace/mode/python");
document.getElementById('editor').style.fontSize='16px';

var feature_id;
var scen_id;
var template_id;
var attr_id;
var type_id;

// monitor the editor

function reset_editor() {
  editor.setValue('');
  $('#save_status').text('');
};

$(document).ready(function(){

  // load the scenarios
  $('#scenarios').on('hide.bs.select', function (e) {
    scen_id = Number($('#scenarios option:selected').attr("data-tokens"));
    $('#features').attr('disabled',false);
    $('#features').selectpicker('refresh');
    reset_editor();
  });

  // load the variables when the feature is clicked
  $('#features').on('hide.bs.select', function (e) {
    reset_editor();
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
      load_data(feature_id, feature_type, attr_id, scen_id);
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
var original_value;
var attr_data = null;
function load_data(feature_id, feature_type, attr_id, scen_id) {
  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    attr_id: attr_id,
    scen_id: scen_id
  };
  $.getJSON($SCRIPT_ROOT+'_get_variable_data', data, function(resp) {
    attr_data = resp.result;
    if (attr_data != null) {
      original_value = attr_data.value.value;
    } else {
      original_value = '';
    };
    editor.setValue(original_value);
    editor.gotoLine(1);

  });
};

// save data
$(document).on('click', '#save_changes', function() {
  var new_value = editor.getValue();
  if (new_value != original_value) {
    if (attr_data == null) {
      var val = new_value;
      $.getJSON('/_add_variable_data', {scen_id:scen_id, attr_id:attr_id, val:val}, function(resp) {
        var status = resp.status;
        if (status==1) {
          notify('success','Success!','Variable updated.')
        };
      });
    } else {
      $.getJSON('/_update_variable_data', {attr_data:attr_data}, function(resp) {
        var status = resp.status;
        if (status==1) {
          notify('success','Success!','Variable updated.')
        };
      });
    };
  } else {
    notify('info','Nothing saved.','No edits detected.')
  };
});