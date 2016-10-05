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
var aceInput = ace.edit("function_input");
aceInput.setTheme("ace/theme/chrome");
aceInput.getSession().setMode("ace/mode/python");
aceInput.setReadOnly(true);
aceInput.$blockScrolling = Infinity // disable error message; cursor is placed at the beginning below
aceInput.setOptions({
  fontSize: "12pt"
});

// initialize handsontable (time series viewer)
var hotInput = makeHandsontable('timeseries_table_input', $("#timeseries_table_input").css("height"))
var hotTable = makeHandsontable('timeseries_table', $("#timeseries_table").css("height"))

$(document).ready(function(){

  clearViewers();

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearViewers();
    
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
        //if (res_attr.attr_is_var == 'Y') {
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
          //}
      });
      vpicker.attr('disabled',false);
      $('#variables').selectpicker('render');
      $('#variables').selectpicker('refresh');
      
      // deselect all variables (select offers no function for this?)
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
  var default_input_types = {timeseries: 'timeseries_table', descriptor: 'text', scalar: 'scalar', array: 'array_table'}
  var input_type;
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
      data_type = res_attr_data.value.type;
      input_type = default_input_types[data_type]
      metadata = JSON.parse(res_attr_data.value.metadata)
      if (metadata.hasOwnProperty('function')) {
        if (metadata.function.length) {
          input_type = 'function';
        }
      }
      
    }
    
    loadInputData(input_type, res_attr_data, eval_value);
    loadTableData(data_type, scen_name, eval_value);
    loadOutputData(data_type, scen_name, eval_value);
    
    $('#unit').html('<strong>&nbsp;Unit: </strong>'+unit+'&nbsp;('+dimension+')');
    
  });
}

function loadInputData(input_type, res_attr_data, eval_value) {

  showInput(input_type);

  switch(input_type) {
      
    case 'function':
      if (res_attr_data == null) {
        val = '';
      } else {
        val = JSON.parse(res_attr_data.value.metadata).function;
      }
      aceInput.setValue(val);
      aceInput.gotoLine(1);
      break;
  
    case 'table':
      var col_headers = ['Month', scen_name]; // get from settings later
      updateHandsontable(hotInput, eval_value, col_headers);
      break;
      
    case 'scalar':
      if (res_attr_data == null) {
        scalarInput.val('');
      } else {
        scalarInput.val(res_attr_data.value.value);  
      }
      break;
      
    case 'text':
      if (res_attr_data == null) {
        descriptorInput.val('');
      } else {
        descriptorInput.val(res_attr_data.value.value);       
      }
      break;
      
    case 'array':
      break;
      
    default:
      break;
  }
}
 
function loadTableData(data_type, scen_name, eval_value) {
  
  switch(data_type) {
  
    case 'timeseries':
      showTable(data_type);
      $('#timeseries_table').show();
      var col_headers = ['Month', scen_name]; // get from settings later
      updateHandsontable(hotTable, eval_value, col_headers);
      break;
      
    case 'scalar':
      break;
      
    case 'descriptor':
      break;
      
    case 'array':
      break;
      
    default:
      break;
  }
}
    
function loadOutputData(data_type, scen_name, eval_value) {
  
  switch(data_type) {
  
    case 'timeseries':
      showOutput(data_type);
      amchart('Results', eval_value, dateFormat, "timeseries_output", false, "MMM YYYY")
      break;
      
    case 'scalar':
      showOutput(data_type);
      $("#scalar_output").text(eval_value);
      break;
      
    case 'descriptor':
      break;
      
    case 'array':
      break;
      
    default:
      break;
  }
}

function showOutput(data_type) {
  $('#'+data_type+'_output').show();
}

function showTable(data_type) {
  $('#'+data_type+'_table').show();
}

function showInput(input_type) {
  $('#'+input_type+'_input').show();
}

function clearViewers() {
  $('.viewer').hide();
}