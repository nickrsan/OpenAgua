// global variables
var feature_id, feature_type,
    scen_id, scen_name,
    template_id,
    res_attr, res_attr_id, res_attr_name,
    type_id,
    data_type,
    unit,
    dimension;

//var default_data_type = 'function'; // setting this is subjective

// initialize selectpick
$(".selectpicker")
  .addClass("show-menu-arrow")
  .selectpicker("refresh");

// initialize scalar viewer
var scalarInput = $('#scalar_input_field')

// initialize text viewer
var textInput = $('#text_input_field')

// initialize Ace code viewer
var aceViewer = ace.edit("function_input");
aceViewer.setTheme("ace/theme/chrome");
aceViewer.getSession().setMode("ace/mode/python");
aceViewer.setReadOnly(true);
aceViewer.$blockScrolling = Infinity // disable error message; cursor is placed at the beginning below
aceViewer.setOptions({
  fontSize: "12pt"
});

// initialize handsontable (time series viewer)
var hotInput = makeHandsontable('timeseries_input', $(".timeseries").css("height"))
var hotTable = makeHandsontable('timeseries_table', $(".timeseries").css("height"))

$(document).ready(function(){

  clearOutput()

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearInput();
    clearTable();
    clearOutput();
    
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
            aceInput.setValue('');          
          }
          updateInput(cur_data_type, unit, dimension);
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
      aceInput.setValue('');
    }
  });

});


// FUNCTIONS

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
    
    loadInputData(cur_data_type, res_attr_data, eval_value);
    loadTableData(cur_data_type, scen_name, eval_value);
    loadOutputData(cur_data_type, scen_name, eval_value);
    saved();
    
  });
}


function loadInputData(cur_data_type, res_attr_data, eval_value) {

  clearInput();
  updateInput(cur_data_type, unit, dimension);
  
  switch(cur_data_type) {
      
    case 'function':
      if (res_attr_data == null) {
        original_data = '';
      } else {
        original_data = JSON.parse(res_attr_data.value.metadata).function;
      }
      setDataTypeSelector(cur_data_type);
      updateAceInput(original_data);
      break;
  
    case 'timeseries':
      original_data = _.cloneDeep(eval_value);
      setDataTypeSelector(cur_data_type);
      var col_headers = ['Month', scen_name]; // get from settings later
      updateHandsontable(hotInput, eval_value, col_headers);
      break;
      
    case 'scalar':
      if (res_attr_data == null) {
        original_data = ''
      } else {
        original_data = res_attr_data.value.value;       
      }
      scalarInput(original_data)
      break;
      
    case 'descriptor':
      if (res_attr_data == null) {
        original_data = ''
      } else {
        original_data = res_attr_data.value.value;       
      }
      textInput(original_data)
      break;
      
    case 'array':
      break;
      
    default:
      break;
  }
}
 
function loadTableData(cur_data_type, scen_name, eval_value) {

  clearOutput();
  
  switch(cur_data_type) {
      
    case 'function':
      tableTimeseries(scen_name, eval_value);
      break;
  
    case 'timeseries':
      outputTimeseries(scen_name, eval_value);
      break;
      
    case 'scalar':
      if (eval_value == null) {
        clearOutput('No data to show')
      } else {
        outputScalar(eval_value)
      }
      break;
      
    case 'descriptor':
      if (eval_value == null) {
        clearOutput('No data to show')
      } else {
        outputDescriptor(eval_value)
      }
      break;
      
    case 'array':
      outputArray('No data to show.')
      break;
      
    default:
      break;
  }
}
    
function loadOutputData(cur_data_type, scen_name, eval_value) {

  clearOutput();
  
  switch(cur_data_type) {
      
    case 'function':
      outputTimeseries(scen_name, eval_value);
      break;
  
    case 'timeseries':
      outputTimeseries(scen_name, eval_value);
      break;
      
    case 'scalar':
      if (eval_value == null) {
        clearOutput('No data to show')
      } else {
        outputScalar(eval_value)
      }
      break;
      
    case 'descriptor':
      if (eval_value == null) {
        clearOutput('No data to show')
      } else {
        outputDescriptor(eval_value)
      }
      break;
      
    case 'array':
      outputArray('No data to show.')
      break;
      
    default:
      break;
  }
}

// INPUT VIEWER FUNCTIONS

function updateInput(data_type, unit, dimension) {
  $('.input').hide();
  $('#input_'+data_type).show();
  $('#input').show()
  $('#unit').html('<strong>&nbsp;Unit: </strong>'+unit+'&nbsp;('+dimension+')');
}

function clearInput() {
  scalarInput.val('');
  textInput.val('');
  aceInput.setValue('');
  $('#input').hide();
}

function updateAceInput(original_data) {
  aceInput.setValue(original_data);
  aceInput.gotoLine(1);
  saved();
}

function scalarInput(original_data) {
  scalarInput.val(original_data);
}

function textInput(original_data) {
  textInput.val(original_data);
}

// OUTPUT VIEWER FUNCTIONS

function outputTimeseries(title, timeseries) {
  clearOutput('');
  $('#output_timeseries').show();
  amchart(title, timeseries, dateFormat, "output_timeseries", false)
}

function outputScalar(value) {
  clearOutput('');
  $("#output_scalar").text(value).show();
}

function outputArray(value) {
  clearOutput('');
  $("#output_array").text(value).show(); // placeholder
}

function clearOutput(msg='No data to output') {
  $('.output').empty().hide()
  if (msg.length) {
    $('#output_status').text(msg); 
  } else {
    $('#output_status').empty().hide();  
  }
}