var editor = ace.edit("editor");
editor.setTheme("ace/theme/chrome");
editor.getSession().setMode("ace/mode/python");
document.getElementById('editor').style.fontSize='16px';

var feature_id, scen_id, template_id, res_attr_id, attr_id, type_id;

// monitor the editor

function reset_editor() {
  editor.setValue('');
  $('#save_status').text('');
};

$(document).ready(function(){

  // load the scenarios
  $('#scenarios').on('changed.bs.select', function (e) {
    scen_id = Number($('#scenarios option:selected').attr("data-tokens"));
    $('#features').attr('disabled',false);
    $('#features').selectpicker('refresh');
    reset_editor();
  });

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
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
  $('#variables').on('changed.bs.select', function (e) {
    var selected = $('#variables option:selected');
    var data_tokens = JSON.parse(selected.attr("data-tokens"));
    res_attr_id = data_tokens.res_attr_id;
    attr_id = data_tokens.attr_id;
    load_data(feature_id, feature_type, attr_id, scen_id);
  });
  
});

// load the variables (aka attributes in Hydra)
function load_variables(type_id) {
  var data = {
    type_id: type_id,
    feature_id: feature_id,
    feature_type: feature_type
    };
  $.getJSON($SCRIPT_ROOT+'/_get_variables', data, function(resp) {
      var res_attrs = resp.res_attrs;
      var attr_dict = resp.attr_dict;
      var vpicker = $('#variables');
      vpicker.empty();
      $.each(res_attrs, function(index, res_attr) {
        var data_tokens = {attr_id: res_attr.attr_id, res_attr_id: res_attr.id};
        vpicker
          .append($('<option>')
            .attr('data-tokens',JSON.stringify(data_tokens))
            .text(attr_dict[res_attr.attr_id].replace(/_/g,' '))
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
  $.getJSON($SCRIPT_ROOT+'/_get_variable_data', data, function(resp) {
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
      var data = {
        scen_id: scen_id,
        res_attr_id: res_attr_id,
        attr_id: attr_id,
        val: new_value
      };
      $.getJSON('/_add_variable_data', data, function(resp) {
        var status = resp.status;
        if (status==1) {
          notify('success','Success!','Variable updated.')
        };
      });
    } else {
      attr_data.value.value = new_value;
      var data = {scen_id: scen_id, attr_data: JSON.stringify(attr_data)}
      $.getJSON('/_update_variable_data', data, function(resp) {
        if (resp.status==1) {
          notify('success','Success!','Variable updated.')
        };
      });
    };
  } else {
    notify('info','Nothing saved.','No edits detected.')
  };
});