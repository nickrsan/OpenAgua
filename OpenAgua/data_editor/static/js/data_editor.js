// global variables
var feature_id, feature_type, scen_id, scen_name, template_id, res_attr_id, res_attr_name, type_id, data_type

var unit,
    dimension;
  
var res_attr;
  
var original_data;
var attr_data;

var heights = {
  descriptor: "220px",
  timeseries: "220px",
  eqtimeseries: "220px",
  scalar: "70px",
  array: "220px",
}

//var default_data_type = 'descriptor'; // setting this is subjective

// initialize Ace code editor
var aceEditor = ace.edit("descriptor");
aceEditor.setTheme("ace/theme/chrome");
aceEditor.getSession().setMode("ace/mode/python");
aceEditor.$blockScrolling = Infinity // disable error message; cursor is placed at the beginning below
document.getElementById("descriptor").style.fontSize='14px';

// initialize handsontable (time series editor)
var hotEditor = makeHandsontable('timeseries', 220)

$(document).ready(function(){

  clearEditor();
  clearChart();

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearEditor();
    clearChart();
    
    selectDataType("scalar");
    
    $('#datatypes').attr('disabled', true).selectpicker('refresh');
    $('#scenarios').attr('disabled', true).selectpicker('refresh');
    var selected = $('#features option:selected');
    if (selected.length) {
      var data_tokens = $.parseJSON(selected.attr("data-tokens"));
      type_id = data_tokens.type_id;
      feature_id = data_tokens.feature_id;
      feature_type = data_tokens.feature_type;
      load_variables(type_id);
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
        load_data();
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
    if (selected.length) {
      var data_tokens = JSON.parse(selected.attr("data-tokens"));
      data_type = data_tokens.data_type;
      updateEditor(data_type, unit, dimension);
    }
  });
  
  
  // load the scenarios
  $('#scenarios').on('hide.bs.select', function (e) {
    var selected = $('#scenarios option:selected');
    if (selected.length) {
      var data_tokens = JSON.parse(selected.attr("data-tokens"));
      scen_id = data_tokens.scen_id;
      scen_name = data_tokens.scen_name;
      load_data();
    } else {
      scen_id = null;
      scen_name = null;
      hideCharts();
      aceEditor.setValue('');
    }
  });
});

// load the variables (aka attributes in Hydra)
function load_variables(type_id) {
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
          var data_tokens = {
            attr_id: res_attr.attr_id,
            res_attr_id: res_attr.id,
            res_attr_name: res_attr.tpl_type_attr.name,
            data_type: res_attr.tpl_type_attr.data_type,
            unit: res_attr.tpl_type_attr.unit,
            dimension: res_attr.tpl_type_attr.dimension,
          }
          vpicker
            .append($('<option>')
              .attr('data-tokens',JSON.stringify(data_tokens))
              .text(res_attr.tpl_type_attr.pretty_name)
            );
          }
      });
      vpicker.attr('disabled',false);
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
function load_data() {

  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    attr_id: res_attr.attr_id,
    scen_id: scen_id
  }
  $.getJSON($SCRIPT_ROOT+'/_get_variable_data', data, function(resp) {
    attr_data = resp.attr_data;
    if (attr_data != null) {
      data_type = attr_data.value.type;
    } //else {
      // default data type is defined at beginning of script
      //data_type = default_data_type;
    //}
    
    // set the data type selector
    selectDataType(data_type);
    
    // toggle the editors
    updateEditor(data_type, unit, dimension);
    
    // load the returned time series into the table and plot, even if empty
    dataActions(data_type, attr_data, resp.timeseries)
    
    // turn on the data type selector
    $("#datatypes").attr("disabled", false).selectpicker("refresh");
    
  });
}

// set the data type selector
function selectDataType(data_type) {
  var selector = $('#datatypes')
  selector.children().removeAttr('selected')
  selector.val(data_type);
  selector.selectpicker('refresh')
}

function dataActions(data_type, attr_data, plot_data) {

    switch(data_type) {
        
      case 'descriptor':
        if (attr_data == null) {
          original_data = '';
        } else {
          original_data = attr_data.value.value;
        }
        updateAceEditor(original_data)
        break;
    
      case 'timeseries': 
        break;
        
      case 'eqtimeseries':
        break;
        
      case 'scalar':
        if (attr_data == null) {
          original_data = ''
        } else {
          original_data = attr_data.value.value;       
        }
        scalarInput(original_data)
        break;
        
      case 'array':
        break;
        
      default:
        break;
    }
  
    // in all cases, the plot_data can be loaded directly into the table
    // however, this will not be saved, unless save is clicked while in 
    // table view mode
    var colHeaders = ['Month',scen_name];
    updateHandsontable(plot_data, colHeaders);
    updateChart(scen_name, plot_data);

}

// save data
$(document).on('click', '#save', function() {

  var new_data,
      unchanged;

  switch(data_type) {
  
    case "descriptor":
      new_data = aceEditor.getValue(); 
      unchanged = (new_data == original_data);
      break;
      
    case "timeseries":
      var original_data = hotEditor.getSourceData();
      new_data = _.map(hotEditor.getData(), function(row, index) {
        return {date: row[0], value: row[1]}      
      })
      //unchanged = _.isEqual(original_data, new_data)
      unchanged = false
      break;

    case "eqtimeseries":
      break;

    case "scalar":
      new_data = $('#scalar_input').val();
      break;

    case "array":
      break;

    default:
      new_data = null;
      unchanged = true;
      break;
  }
  
  // notify if nothing has changed
  if (unchanged) {
    notify('info', 'Alert!', 'No change detected. Nothing saved.');
    return;
  }
  
  // add or update data; function separated out for readability
  updateHydraData(new_data, data_type); // new dataset  
});

// data functions
function updateHydraData(new_data, data_type) {
  var data = {
    data_type: data_type,
    scen_id: scen_id,
    res_attr: JSON.stringify(res_attr), 
    attr_data: JSON.stringify(attr_data), // old data container
    new_data: JSON.stringify(new_data)
  };
  $.getJSON('/_add_variable_data', data, function(resp) {
    if (resp.status == 1) {
      dataActions(data_type, resp.attr_data, resp.timeseries);
      notify('success','Success!','Database updated.');
    }
  });
}

// editor functions
function updateEditor(data_type, unit, dimension) {
  $('.editor').hide()
  var div = $('#'+data_type)
  div.css("height", heights[data_type])
  div.show()
  $('#unit').html('<strong>&nbsp;Unit: </strong>'+unit+'&nbsp;('+dimension+')');
  $('#editor').show()
  $('#editor_status').empty();
}

function clearEditor() {
  $('#editor').hide()
  $('#editor_status').text('No variable loaded')
}

// update updateAceEditor
function updateAceEditor(original_data) {
  aceEditor.setValue(original_data);
  aceEditor.gotoLine(1);  
}

// function scalar input
function scalarInput(original_data) {
  $("#scalar_input").text(original_data)
}

// chart functions
function updateChart(title, timeseries) {
  if (timeseries != null) {
    $('#preview').text();
    dateFormat = "MM/YYYY" // need to get this from the model setup
    amchart(title, timeseries, dateFormat, "preview")
  } else {
    clearChart() // actually, we shouldn't get here
  }
}

function clearChart() {
  $('#preview').empty().text('No variable loaded')
}