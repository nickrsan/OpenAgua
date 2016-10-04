// global variables
var feature_id, feature_type,
    scen_id, scen_name,
    template_id,
    res_attr, res_attr_id, res_attr_name,
    type_id,
    orig_data_type, cur_data_type;

var unit,
    dimension, 
    original_data,
    res_attr_data;

// initialize selectpick
$(".selectpicker")
  .addClass("show-menu-arrow")
  .selectpicker("refresh");

// initialize scalar editor
var scalarInput = $('#scalar_input')

// initialize text editor
var textInput = $('#text_input')

// initialize Ace code editor
var aceEditor = ace.edit("function");
aceEditor.setTheme("ace/theme/chrome");
aceEditor.getSession().setMode("ace/mode/python");
aceEditor.$blockScrolling = Infinity // disable error message; cursor is placed at the beginning below
aceEditor.setOptions({
  fontSize: "12pt"
});

// initialize handsontable (time series editor)
var hotEditor = makeHandsontable('timeseries', $("#timeseries").css("height"), unsaved)

$(document).ready(function(){

  clearPreview()

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearEditor();
    clearPreview();
    
    setDataTypeSelector("scalar");
    
    //$('#datatypes').attr('disabled', true).selectpicker('refresh');
    $('#scenarios').attr('disabled', true).selectpicker('refresh');
    var selected = $('#features option:selected');
    if (selected.length) {
      var tags = $.parseJSON(selected.attr("data-tags"));
      type_id = tags.type_id;
      feature_id = tags.feature_id;
      feature_type = tags.feature_type;
      loadVariables(type_id);
    }
  });

  // load the variable data when the variable is clicked
  $('#variables').on('changed.bs.select', function (e) {
    var selected = $('#variables option:selected');
    if (selected.length) {
      res_attr = JSON.parse(selected.attr("data-tags"));
      unit = res_attr.unit;
      dimension = res_attr.dimension;
      orig_data_type = res_attr.data_type;
      var spicker = $('#scenarios');
      if (spicker.attr('disabled')) {
        spicker.attr('disabled',false).selectpicker('refresh');
      }
      if (scen_id != null) {
        loadVariableData();
      } else {
      var stitle = 'Select a scenario'
      $('button[data-id="scenarios"]')
        .attr('title',stitle).children('.filter-option').text(stitle)
      }
    }
  });
  
  // select the data class
  $('#datatypes').on('changed.bs.select', function (e) {
    var selected = $('#datatypes option:selected');
    
    var tags = JSON.parse(selected.attr("data-tags"));
    var temp_data_type = tags.data_type;
      var msg = 'Are you sure you want to change the data type? This change will become permanent if the new data is saved.'
      bootbox.confirm(msg, function(confirm) {
        if (confirm) {          
          cur_data_type = temp_data_type;
          if (cur_data_type == 'function' & cur_data_type != orig_data_type) {
            aceEditor.setValue('');          
          }
          updateEditor(cur_data_type, unit, dimension);
        } else {
          setDataTypeSelector(cur_data_type);
        }
      });
  });
  
  // load the scenarios
  $('#scenarios').on('hide.bs.select', function (e) {
    var selected = $('#scenarios option:selected');
    if (selected.length) {
      var tags = JSON.parse(selected.attr("data-tags"));
      scen_id = tags.scen_id;
      scen_name = tags.scen_name;
      loadVariableData();
    } else {
      scen_id = null;
      scen_name = null;
      hideCharts();
      aceEditor.setValue('');
    }
  });
  
  // listen to text editor changes
  $('#text_input').on('input', function() {
    unsaved();
  });
  
  // listen to function editor changes
  aceEditor.getSession().on("change", function() {
    unsaved();
  });

});


// save data
$('#check, #save').click(function() {

  var action = $(this).attr('id')

  var new_data,
      unchanged;

  switch(cur_data_type) {
  
    case "function":
      new_data = aceEditor.getValue(); 
      unchanged = (new_data == original_data);
      break;
      
    case "timeseries":
      new_data = _.map(hotEditor.getData(), function(row, index) {
        return {date: row[0], value: row[1]}      
      })
      unchanged = _.isEqual(original_data, new_data)
      break;

    case "scalar":
      new_data = scalarInput.val();
      unchanged = new_data == original_data;
      break;

    case "descriptor":
      new_data = textInput.val();
      unchanged = new_data == original_data;
      break;

    case "array":
      break;

    default:
      new_data = null;
      unchanged = true;
      break;
  }
  
  // also check if the data type has changed
  if (cur_data_type != orig_data_type) {
    unchanged = false;  
  }
  
  // notify if nothing has changed
  if (unchanged) {
    var msg;
    if (action == 'save') {
      msg = 'No change detected. Nothing saved';
    } else {
      msg = 'No change detected.'    
    }
    notify('info', 'Alert!', msg);
    saved();
    return;
  } else {
    checkOrSaveData(new_data, action);
  }
  
});

// clear changes
$('#revert').click(function() {
  loadVariableData();
  saved();
  errmsg('');
});

// FUNCTIONS

// error message
function errmsg(msg) {
  if (msg.length) {
    $('#errmsg').text('ERROR: ' + msg)
      .css('color','red');
  } else {
    $('#errmsg').text('');
  }
}

// load the variables (aka attributes in Hydra)
function loadVariables(type_id) {
  var vpicker = $('#variables');
  vpicker.empty();
  var data = {
    type_id: type_id,
    feature_id: feature_id,
    feature_type: feature_type
    }
  $.getJSON($SCRIPT_ROOT+'/_get_variables', data, function(resp) {
      var res_attrs = _.sortBy(resp.res_attrs, 'name');
      $.each(res_attrs, function(index, res_attr) {
        if (res_attr.attr_is_var == 'N') {
          var tags = {
            attr_id: res_attr.attr_id,
            type_id: type_id,
            res_attr_id: res_attr.id,
            res_attr_name: res_attr.tpl_type_attr.name,
            data_type: res_attr.tpl_type_attr.data_type,
            unit: res_attr.tpl_type_attr.unit,
            dimension: res_attr.tpl_type_attr.dimension,
          }
          vpicker
            .append($('<option>')
              .attr('data-tags',JSON.stringify(tags))
              .val(res_attr.tpl_type_attr.name)
              .text(res_attr.tpl_type_attr.name)
            );
          }
      });
      vpicker.attr('disabled',false);
      $('#variables').selectpicker('render');
      $('#variables').selectpicker('refresh');
      
      // deselect all variables (select offers no function for this)
      var vbutton = $('button[data-id="variables"]')
      vbutton.children('.filter-option').text('Select a variable')
      vbutton.parent().children('.dropdown-menu')
        .children('.inner')
          .children('.selected')
            .removeClass('selected')
  });
}

// load the variable data
function loadVariableData() {

  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    res_attr_id: res_attr.res_attr_id,
    scen_id: scen_id,
    data_type: res_attr.data_type
  }
  $.getJSON($SCRIPT_ROOT+'/_get_variable_data', data, function(resp) {
    res_attr_data = resp.res_attr_data;
    var eval_value = resp.eval_value;
    if (res_attr_data != null) {
      orig_data_type = res_attr_data.value.type;
      metadata = JSON.parse(res_attr_data.value.metadata)
      if (metadata.hasOwnProperty('function')) {
        if (metadata.function.length) {
          orig_data_type = 'function';
        }
      }
    }
    
    cur_data_type = orig_data_type;
    
    loadEditorData(cur_data_type, res_attr_data, eval_value);
    loadPreviewData(cur_data_type, scen_name, eval_value);
    saved();
    
  });
}


function loadEditorData(cur_data_type, res_attr_data, eval_value) {

  clearEditor();
  updateEditor(cur_data_type, unit, dimension);
  
  switch(cur_data_type) {
      
    case 'function':
      if (res_attr_data == null) {
        original_data = '';
      } else {
        original_data = JSON.parse(res_attr_data.value.metadata).function;
      }
      setDataTypeSelector(cur_data_type);
      updateAceEditor(original_data);
      break;
  
    case 'timeseries':
      original_data = _.cloneDeep(eval_value);
      setDataTypeSelector(cur_data_type);
      var col_headers = ['Month', scen_name]; // get from settings later
      updateHandsontable(eval_value, col_headers);
      break;
      
    case 'scalar':
      if (res_attr_data == null) {
        original_data = ''
      } else {
        original_data = res_attr_data.value.value;       
      }
      scalarEditor(original_data)
      break;
      
    case 'descriptor':
      if (res_attr_data == null) {
        original_data = ''
      } else {
        original_data = res_attr_data.value.value;       
      }
      textEditor(original_data)
      break;
      
    case 'array':
      break;
      
    default:
      break;
  }
}

function loadPreviewData(cur_data_type, scen_name, eval_value) {

  clearPreview();
  
  switch(cur_data_type) {
      
    case 'function':
      previewTimeseries(scen_name, eval_value);
      break;
  
    case 'timeseries':
      previewTimeseries(scen_name, eval_value);
      break;
      
    case 'scalar':
      if (eval_value == null) {
        clearPreview('No data to preview')
      } else {
        previewScalar(eval_value)
      }
      break;
      
    case 'descriptor':
      if (eval_value == null) {
        clearPreview('No data to preview')
      } else {
        previewDescriptor(eval_value)
      }
      break;
      
    case 'array':
      previewArray('No data to preview.')
      break;
      
    default:
      break;
  }
}

// data functions
function checkOrSaveData(new_data, action) {

  var data = {
    action: action,
    cur_data_type: cur_data_type,
    new_data: new_data
  }
  
  switch(action) {
    case 'check':
      checkData(data);   
      break;
    case 'save':
      saveData(data);
      break;
    }
}

function checkData(data) {

  $.ajax({
    type : "POST",
    url : '/_check_or_save_data',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: function(resp) {

      switch(resp.errcode) {
        case -1:
          notify('danger','Not good!', 'Your data seems incorrect. See error message.');
          errmsg(resp.errmsg);
          break;
        case 1:
          notify('success','Looks good!', 'Remember to save your edits.');
          errmsg('');
        }
        //updateChart(scen_name, resp.eval_value);
        loadPreviewData(cur_data_type, scen_name, resp.eval_value);
        unsaved();
    }
  });
}

function saveData(data) {
  data.orig_data_type = orig_data_type;
  data.scen_id = scen_id;
  data.res_attr = res_attr;
  data.res_attr_data = res_attr_data; // old data container
  
  $.ajax({
    type : "POST",
    url : '/_check_or_save_data',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: function(resp) {
  
      switch(resp.status) {
        case -1:
          notify('danger','Warning!','Your data seems okay, but something still went wrong.');
          errmsg(resp.errmsg);
          unsaved();
          break;
        case 0:
          notify('danger','Warning!','Your data is not correct. Check error message. Nothing saved.')
          errmsg(resp.errmsg);
          unsaved();
          break;
        case 1:
          data_type = cur_data_type;
          res_attr.data_type = data_type; // update local record
          var selected = $('#variables option:selected');
          //selected.data_tokens = JSON.stringify(res_attr);
          selected.data_tags = JSON.stringify(res_attr);
          $('#variables').selectpicker('refresh');
          loadVariableData();
          notify('success','Success!','Data saved.');
          errmsg('');
          saved();
      }
    }
  });   
}

// EDITOR FUNCTIONS

function updateEditor(data_type, unit, dimension) {
  $('.editor').hide();
  $('#'+data_type).show();
  $('#editor_status').hide();
  $('#editor').show()
  $('#unit').html('<strong>&nbsp;Unit: </strong>'+unit+'&nbsp;('+dimension+')');
}

function clearEditor() {
  scalarInput.val('');
  textInput.val('');
  aceEditor.setValue('');
  $('#editor').hide();
  $('#datatypes_wrapper').hide();
  $('#editor_status').show();
}

// set the data type selector
function setDataTypeSelector(data_type) {
  var selector = $('#datatypes')
  selector.children().removeAttr('selected')
  selector.val(data_type);
  selector.selectpicker('refresh');
  $('#datatypes_wrapper').show();
}

function updateAceEditor(original_data) {
  aceEditor.setValue(original_data);
  aceEditor.gotoLine(1);
  saved();
}

function scalarEditor(original_data) {
  scalarInput.val(original_data);
}

function textEditor(original_data) {
  textInput.val(original_data);
}

function unsaved() {
  $('#save_status').text('Changes not saved!');
}
function saved() {
  $('#save_status').empty();
}

// PREVIEW FUNCTIONS

function previewTimeseries(title, timeseries) {
  clearPreview('');
  $('#preview_timeseries').show();
  amchart(title, timeseries, dateFormat, "preview_timeseries", false)
}

function previewScalar(value) {
  clearPreview('');
  $("#preview_scalar").text(value).show();
}

function previewArray(value) {
  clearPreview('');
  $("#preview_array").text(value).show(); // placeholder
}

function clearPreview(msg='No data to preview') {
  $('.preview').empty().hide()
  if (msg.length) {
    $('#preview_status').text(msg); 
  } else {
    $('#preview_status').empty().hide();  
  }
}
