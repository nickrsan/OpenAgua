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
var hotOutput = makeHandsontable('timeseries_output', $(".timeseries").css("height"))

$(document).ready(function(){

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearViewers();
    clearChart();
       
    $('#datatypes').attr('disabled', true).selectpicker('refresh');
    $('#scenarios').attr('disabled', true).selectpicker('refresh');
    var selected = $('#features option:selected');
    if (selected.length) {
      var data_tokens = $.parseJSON(selected.attr("data-tokens"));
      type_id = data_tokens.type_id;
      feature_id = data_tokens.feature_id;
      feature_type = data_tokens.feature_type;
      loadVariables(type_id);
    }
  });

  // load the variable data when the variable is clicked
  $('#variables').on('changed.bs.select', function (e) {
    var selected = $('#variables option:selected');
    if (selected.length) {
      res_attr = JSON.parse(selected.attr("data-tokens"));
      unit = res_attr.unit;
      dimension = res_attr.dimension;
      data_type = res_attr.data_type;
      var spicker = $('#scenarios');
      if (spicker.attr('disabled')) {
        spicker.attr('disabled',false).selectpicker('refresh');
      }
      if (scen_id != null) {
        loadData();
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
      var data_tokens = JSON.parse(selected.attr("data-tokens"));
      scen_id = data_tokens.scen_id;
      scen_name = data_tokens.scen_name;
      loadData();
    } else {
      scen_id = null;
      scen_name = null;
      hideCharts();
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
        //if (res_attr.attr_is_var == 'N') {
          var data_tokens = {
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
              .attr('data-tokens',JSON.stringify(data_tokens))
              .val(res_attr.tpl_type_attr.name)
              .text(res_attr.tpl_type_attr.name)
            );
          //}
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
function loadData() {

  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    res_attr_id: res_attr.res_attr_id,
    scen_id: scen_id
  }
  
  // really we should load this data from the network scenario - i.e., one hydra call
  $.getJSON($SCRIPT_ROOT+'/_get_variable_data', data, function(resp) {
    var is_from_function = false;
    var res_attr_data = resp.res_attr_data;
    if (res_attr_data != null) {
      data_type = res_attr_data.value.type;
      metadata = JSON.parse(res_attr_data.value.metadata)
      if (metadata.hasOwnProperty('function') && metadata.function.length > 0) {
          is_from_function = true;
      }
    }
    
    // define the data to plot
    var plot_data = resp.timeseries;
    
    // clear the viewer
    clearViewers();
    
    // load the returned time series into the table and plot, even if empty
    loadDataActions(data_type, is_from_function, res_attr_data);
    col_headers = ['Month',scen_name];
    updateInputViewer(data_type, is_from_function, plot_data, col_headers, unit, dimension);
    updateOutputViewer(data_type, plot_data, col_headers, unit, dimension);
    if (data_type == 'descriptor') {
      clearChart();
    } else {
      updateChart(scen_name, plot_data);    
    }
    
    // turn on the data type selector
    $("#datatypes").attr("disabled", false).selectpicker("refresh");
    
  });
}

function loadDataActions(data_type, is_from_function, res_attr_data) {

    switch(data_type) {
    
      case 'timeseries':
        //original_data = _.cloneDeep(plot_data);
        break;
        
      case 'scalar':
        if (res_attr_data == null) {
          original_data = ''
        } else {
          original_data = res_attr_data.value.value;       
        }
        scalarViewer(original_data)
        break;
        
      case 'descriptor':
        if (res_attr_data == null) {
          original_data = ''
        } else {
          original_data = res_attr_data.value.value;       
        }
        textViewer(original_data)
        break;
        
      case 'array':
        break;
        
      default:
        break;
    }
    
    if (is_from_function && res_attr_data != null) {
      updateAceViewer(JSON.parse(res_attr_data.value.metadata).function);
    }
}

// viewer functions

function updateInputViewer(data_type, is_from_function, plot_data, col_headers, unit, dimension) {
  $('.input_viewer').hide();
  $('.viewer_status').hide();
  $('.viewer_contents').show();
  if (!is_from_function) {
    $('#'+data_type+'_input').show();
  } else {
    $('#function_input').show()
  }
  if (data_type == 'timeseries' & !is_from_function) {
    updateHandsontable(hotInput, plot_data, col_headers);
  }
  $('#unit').html('<strong>&nbsp;Unit: </strong>'+unit+'&nbsp;('+dimension+')');
}

function updateOutputViewer(data_type, plot_data, col_headers, unit, dimension) {
  $('.output_viewer').hide();
  $('.viewer_status').hide();
  $('.viewer_contents').show();
  $('#'+data_type+'_output').show();
  if (data_type == 'timeseries') {
    updateHandsontable(hotOutput, plot_data, col_headers);
  }
  $('#unit').html('<strong>&nbsp;Unit: </strong>'+unit+'&nbsp;('+dimension+')');
}

function clearViewers() {
  scalarInput.val('');
  textInput.val('');
  aceViewer.setValue('');
  $('.viewer_contents').hide();
  $('.viewer_status').show();
}

// update aceViewer
function updateAceViewer(s) {
  aceViewer.setValue(s);
  aceViewer.gotoLine(1);
}

// function scalar input
function scalarViewer(s) {
  scalarInput.val(s);
}

// function scalar input
function textViewer(s) {
  textInput.val(s);
}

// chart functions
function updateChart(title, timeseries) {
  if (timeseries != null) {
    dateFormat = "MM/YYYY" // need to get this from the model setup
    $('#preview_status').hide();
    $('#preview').show();
    amchart(title, timeseries, dateFormat, "preview", false)
  } else {
    clearChart() // actually, we shouldn't get here
  }
}

function clearChart() {
  $('#preview').empty().hide();
  $('#preview_status').show();
}
