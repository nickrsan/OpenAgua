// global variables
var feature_id, feature_type,
    scen_id, scen_name,
    template_id,
    res_attr, res_attr_id, res_attr_name,
    type_id,
    orig_data_type, cur_data_type;

var unit,
    dimension;
  
var original_data;
var res_attr_data;

var plot_data, col_headers;

//var default_data_type = 'function'; // setting this is subjective

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
var hotEditor = makeHandsontable('timeseries', $("#timeseries").css("height"))

$(document).ready(function(){

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
    clearEditor();
    clearChart();
    
    setDataTypeSelector("scalar");
    
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
      orig_data_type = res_attr.data_type;
      //cur_data_type = data_type; // initialize cur_data_type
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
  
  // select the data class
  $('#datatypes').on('changed.bs.select', function (e) {
    var selected = $('#datatypes option:selected');
    
    var data_tokens = JSON.parse(selected.attr("data-tokens"));
    var temp_data_type = data_tokens.data_type;
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
      var data_tokens = JSON.parse(selected.attr("data-tokens"));
      scen_id = data_tokens.scen_id;
      scen_name = data_tokens.scen_name;
      loadData();
    } else {
      scen_id = null;
      scen_name = null;
      hideCharts();
      aceEditor.setValue('');
    }
  });
  
  // listen to text editor changes
  $('#text_input').on('input', function() {
    saveStatus(0);
  });
  
  // listen to function editor changes
  aceEditor.getSession().on("change", function() {
    saveStatus(0);
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
    saveStatus(1);
    return;
  } else {
    checkOrSaveData(new_data, action);
  }
  
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
function loadData() {

  var data = {
    type_id: type_id,
    feature_type: feature_type,
    feature_id: feature_id,
    res_attr_id: res_attr.res_attr_id,
    scen_id: scen_id
  }
  $.getJSON($SCRIPT_ROOT+'/_get_variable_data', data, function(resp) {
    res_attr_data = resp.res_attr_data;
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
    
    // define the data to plot
    plot_data = resp.timeseries;
    
    // clear the editor
    clearEditor();
    
    // load the returned time series into the table and plot, even if empty
    loadDataActions(cur_data_type, res_attr_data);
    col_headers = ['Month',scen_name];
    updateEditor(cur_data_type, unit, dimension);
    if (cur_data_type == 'descriptor') {
      clearChart();
    } else {
      updateChart(scen_name, plot_data);    
    }
    saveStatus(1);
    
    // turn on the data type selector
    $("#datatypes").attr("disabled", false).selectpicker("refresh");
    
  });
}

function loadDataActions(data_type, res_attr_data) {

    switch(data_type) {
        
      case 'function':
        if (res_attr_data == null) {
          original_data = '';
        } else {
          original_data = JSON.parse(res_attr_data.value.metadata).function;
        }
        updateAceEditor(original_data);
        setDataTypeSelector(cur_data_type);
        break;
    
      case 'timeseries':
        original_data = _.cloneDeep(plot_data);
        setDataTypeSelector(cur_data_type);
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

// clear changes
$('#revert').click(function() {
  loadData();
  saveStatus(1);
  errmsg('');
});

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
        updateChart(scen_name, resp.timeseries);
        saveStatus(0);
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
          saveStatus(0)
          break;
        case 0:
          notify('danger','Warning!','Your data is not correct. Check error message. Nothing saved.')
          errmsg(resp.errmsg);
          saveStatus(0)
          break;
        case 1:
          data_type = cur_data_type;
          res_attr.data_type = data_type; // update local record
          var selected = $('#variables option:selected');
          selected.data_tokens = JSON.stringify(res_attr);
          $('#variables').selectpicker('refresh');
          loadData();
          notify('success','Success!','Data saved.');
          errmsg('');
          saveStatus(1);
      }
    }
  });   
}

// editor functions
function updateEditor(data_type, unit, dimension) {
  //$('#editor').hide();
  $('.editor').hide();
  $('#'+data_type).show();
  $('#editor_status').hide();
  $('#editor').show()
  if (data_type == 'timeseries') {
      updateHandsontable(plot_data, col_headers);
  }
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

// update updateAceEditor
function updateAceEditor(original_data) {
  aceEditor.setValue(original_data);
  aceEditor.gotoLine(1);
  saveStatus(1);
}

// function scalar input
function scalarEditor(original_data) {
  scalarInput.val(original_data);
}

// function scalar input
function textEditor(original_data) {
  textInput.val(original_data);
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

function saveStatus(code) {
  if(code == 0) {
    $('#savestatus').text('Changes not saved!');
  } else {
    $('#savestatus').text('');  
  }
}