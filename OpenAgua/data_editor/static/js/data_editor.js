// global variables
var feature_id, scen_id, scen_name, template_id, res_attr_id, res_attr_name, 
  attr_id, type_id, data_type_name;

var heights = {
  descriptor: "220px",
  timeseries: "220px",
  eqtimeseries: "220px",
  scalar: "70px",
  array: "220px",
}

var default_data_type = 'descriptor'; // setting this is subjective

// initialize Ace code editor
var aceEditor = ace.edit("descriptor");
aceEditor.setTheme("ace/theme/chrome");
aceEditor.getSession().setMode("ace/mode/python");
aceEditor.$blockScrolling = Infinity // disable error message; cursor is placed at the beginning below
document.getElementById("descriptor").style.fontSize='14px';

$(document).ready(function(){

  clearEditor();
  clearPreview();

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearEditor();
    clearPreview();
    
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
      var data_tokens = JSON.parse(selected.attr("data-tokens"));
      res_attr_id = data_tokens.res_attr_id;    
      res_attr_name = data_tokens.res_attr_name;
      attr_id = data_tokens.attr_id;
      var spicker = $('#scenarios');
      if (spicker.attr('disabled')) {
        spicker.attr('disabled',false).selectpicker('refresh');
      }
      if (scen_id != null) {
        load_data(feature_id, feature_type, attr_id, scen_id);
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
      data_type_name = data_tokens.data_type_name;
      toggleEditors(data_type_name);
    }
  });
  
  
  // load the scenarios
  $('#scenarios').on('hide.bs.select', function (e) {
    var selected = $('#scenarios option:selected');
    if (selected.length) {
      var data_tokens = JSON.parse(selected.attr("data-tokens"));
      scen_id = data_tokens.scen_id;
      scen_name = data_tokens.scen_name;
      load_data(feature_id, feature_type, attr_id, scen_id);
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
            res_attr_name: res_attr.name
          }
          vpicker
            .append($('<option>')
              .attr('data-tokens',JSON.stringify(data_tokens))
              .text(res_attr.name)
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
var original_value;
var attr_data = null;
function load_data(feature_id, feature_type, attr_id, scen_id) {

  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    attr_id: attr_id,
    scen_id: scen_id
  }
  $.getJSON($SCRIPT_ROOT+'/_get_variable_data', data, function(resp) {
    attr_data = resp.attr_data;
    var original_value;
    if (attr_data != null) {
      data_type_name = attr_data.value.type;
    } else {
      // default data type is defined at beginning of script
      data_type_name = default_data_type;
    }
    
    // set the data type selector
    selectDataType(data_type_name);
    
    // toggle the editors
    toggleEditors(data_type_name);
    
    // load the returned time series into the table and plot, even if empty
    dataActions(data_type_name, attr_data, resp.timeseries)
    
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

function dataActions(data_type_name, attr_data, plot_data) {

    switch(data_type_name) {
        
      case 'descriptor':
        if (attr_data == null) {
          original_value = '';
        } else {
          original_value = attr_data.value.value;
        }
        updateAceEditor(original_value)
        break;
    
      case 'timeseries': 
        break;
        
      case 'eqtimeseries':
        break;
        
      case 'scalar':
        if (attr_data == null) {
          original_value = ''
        } else {
          original_value = attr_data.value.value;       
        }
        scalarInput(original_value)
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
    handsontable("timeseries", plot_data, colHeaders, heights[data_type_name]);
    updateChart(scen_name, plot_data);

}

// save data
$(document).on('click', '#save', function() {

  switch(data_type_name) {
  
    case "descriptor":
      var new_value = aceEditor.getValue(); 
      break;
      
    case "timeseries":
      break;

    case "eqtimeseries":
      break;

    case "scalar":
      break;

    case "array":
      break;

    default:
      break;
  }

  if (new_value != original_value) {
    if (attr_data == null) {
      var data = {
        scen_id: scen_id,
        res_attr_id: res_attr_id,
        attr_id: attr_id,
        val: new_value
      }
      $.getJSON('/_add_variable_data', data, function(resp) {
        if (resp.status==1) {
          dataActions(data_type_name, attr_data, resp.timeseries);
          notify('success','Success!','Data added.');
        }
      });
    } else {
      attr_data.value.value = new_value;
      var data = {scen_id: scen_id, attr_data: JSON.stringify(attr_data)}
      $.getJSON('/_update_variable_data', data, function(resp) {
        if (resp.status==1) {
          dataActions(data_type_name, attr_data, resp.timeseries);
          original_value = new_value;
          notify('success','Success!','Data updated.');
        }
      });
    }

  } else {
    notify('info','Nothing saved.','No edits detected.')
  }
});

// toggle the editors, depending on the data class selected
function toggleEditors(data_type_name) {
  $('.editor').hide()
  var div = $('#'+data_type_name)
  div.css("height", heights[data_type_name])
  div.show()
  $('#editor').show()
  $('#editor_status').empty();
}

// chart functions

function updateChart(title, timeseries) {
  if (timeseries != null) {
    $('#preview').text();
    dateFormat = "MM/YYYY" // need to get this from the model setup
    amchart(title, timeseries, dateFormat, "preview")
  } else {
    clearPreview() // actually, we shouldn't get here
  }
}

function clearEditor() {
  $('#editor').hide()
  $('#editor_status').text('No variable loaded')
}

function clearPreview() {
  $('#preview').empty().text('No variable loaded')
}

// update updateAceEditor
function updateAceEditor(original_value) {
  aceEditor.setValue(original_value);
  aceEditor.gotoLine(1);  
}


// function scalar input
function scalarInput(original_value) {
  $("#scalar_input").text(original_value)
}