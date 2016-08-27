var editor = ace.edit("editor");
editor.setTheme("ace/theme/chrome");
editor.getSession().setMode("ace/mode/python");
editor.$blockScrolling = Infinity // disable error message; cursor is placed at the beginning below
document.getElementById('editor').style.fontSize='14px';

var feature_id, scen_id, scen_name, template_id, res_attr_id, res_attr_name, attr_id, type_id;

$(document).ready(function(){

  // load the variables when the feature is clicked
  $('#features').on('changed.bs.select', function (e) {
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
        spicker.attr('disabled',false);
        spicker.selectpicker('refresh');
      }
      if (scen_id != null) {
        load_data(feature_id, feature_type, attr_id, scen_id);
      } else {
      var vbutton = $('button[data-id="scenarios"]');
      var stitle = 'Select a scenario'
      vbutton.attr('title',stitle)
      vbutton.children('.filter-option').text(stitle)
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
      load_data(feature_id, feature_type, attr_id, scen_id);
    } else {
      scen_id = null;
      scen_name = null;
      hideCharts();
      editor.setValue('');
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
          var data_tokens = {attr_id: res_attr.attr_id, res_attr_id: res_attr.id, res_attr_name: res_attr.name};
          vpicker
            .append($('<option>')
              .attr('data-tokens',JSON.stringify(data_tokens))
              .text(res_attr.name)
            );
          }
      });
      vpicker.attr('disabled',false);
      $('#variables').selectpicker('refresh');
      var vbutton = $('button[data-id="variables"]')
      vbutton.children('.filter-option').text('Select a variable')
      vbutton.parent().children('.dropdown-menu').children('.inner').children('.selected')
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
    updateChart(scen_name, resp.eval_data)
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
          updateChart(scen_name, resp.eval_data);
        };
      });
    } else {
      attr_data.value.value = new_value;
      var data = {scen_id: scen_id, attr_data: JSON.stringify(attr_data)};
      $.getJSON('/_update_variable_data', data, function(resp) {
        if (resp.status==1) {
          notify('success','Success!','Data updated.');
          original_value = new_value;
          updateChart(scen_name, resp.eval_data);
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
        
        dataGrouping: {
            approximation: "sum",
            enabled: true,
            forced: true,
            units: [['month',[1]]]

        },

        
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