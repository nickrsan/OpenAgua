var editor = ace.edit("editor");
editor.setTheme("ace/theme/chrome");
editor.getSession().setMode("ace/mode/python");
document.getElementById('editor').style.fontSize='14px';

var feature_id, scen_id, template_id, res_attr_id, res_attr_name, attr_id, type_id;

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
    var selected = $('#features option:selected');
    var data_tokens = selected.attr("data-tokens");
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
    res_attr_name = data_tokens.res_attr_name;
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
      var res_attrs = _.sortBy(resp.res_attrs, 'name');
      var vpicker = $('#variables');
      vpicker.empty();
      $.each(res_attrs, function(index, res_attr) {
        if (res_attr.attr_is_var == 'N') {
          var data_tokens = {attr_id: res_attr.attr_id, res_attr_id: res_attr.id, res_attr_name: res_attr.name};
          vpicker
            .append($('<option>')
              .attr('data-tokens',JSON.stringify(data_tokens))
              .text(res_attr.name)
            );
          };
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
    attr_data = resp.attr_data;
    if (attr_data != null) {
      original_value = attr_data.value.value;
    } else {
      original_value = '';
    };
    editor.setValue(original_value);
    editor.gotoLine(1);
    updateChart(res_attr_name, resp.eval_data)
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
        if (resp.status==1) {
          notify('success','Success!','Data added.');
          updateChart(res_attr_name, resp.eval_data);
        };
      });
    } else {
      attr_data.value.value = new_value;
      var data = {scen_id: scen_id, attr_data: JSON.stringify(attr_data)};
      $.getJSON('/_update_variable_data', data, function(resp) {
        if (resp.status==1) {
          notify('success','Success!','Data updated.');
          original_value = new_value;
          updateChart(res_attr_name, resp.eval_data);
        };
      });
    };
  } else {
    notify('info','Nothing saved.','No edits detected.')
  };
});

// chart functions
var myChart = null;

function updateChart(title, eval_data) {
  if (eval_data != null) {
    //chartjs(title, eval_data)
    highstock(title, eval_data)
  } else {
    hideCharts()  
  };
};

function hideCharts() {
  //$('#chartjs').hide();
  $('#highstock').hide();
};

// make chartjs chart
function chartjs(title, eval_data) {
  $('#chartjs').show();
  if (myChart != null) { myChart.destroy() }
  var ctx = document.getElementById("monthly_chart");
  myChart = new Chart(ctx, {
      type: 'line',
      data: {
          //labels: eval_data.dates,
          datasets: [{
              label: title,
              data: eval_data.values,
          }]
      },
      options: {
          responsive: true,
      }
  });

};

// make highstock chart
function highstock(title, eval_data) {

    // prepare the data - this could be done server side instead if plotly uses the same format
    // On the other hand, Lodash makes it easy!
    var data = _.zip(eval_data.dates, eval_data.values);

    $('#highstock').show();
    
    // Create the chart
    $('#highstock').highcharts('StockChart', {

        rangeSelector : {
            selected : 1
        },

        //title : {
            //text : title
        //},
        
        chart: {
            height: 300
        },

        series : [{
            name : title,
            data : data,
            tooltip: {
                valueDecimals: 2
            },
            marker : {
                    enabled : true,
                    radius : 3
            }
        }],
        
        yAxis: {
          opposite: false
        },
        
        rangeSelector : {
            allButtonsEnabled: true,
            buttons: [{
                type: 'month',
                count: 12,
                text: '1 year',
                dataGrouping: {
                    forced: true,
                    units: [['day', [1]]]
                }
            }, {
                type: 'year',
                count: 5,
                text: '5 years',
                dataGrouping: {
                    forced: true,
                    units: [['week', [1]]]
                }
            }, {
                type: 'all',
                text: 'All',
                dataGrouping: {
                    forced: true,
                    units: [['month', [1]]]
                }
            }],
            buttonTheme: {
                width: 60
            },
            selected: 0
        },
    });

};