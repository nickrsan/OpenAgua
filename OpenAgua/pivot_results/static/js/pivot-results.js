var pivotOutput;

function loadPivot(chartRendererName = 'plotly') {

  // Get JSON-formatted data from the server
  var chartRenderers, nCharts;
  
  switch(chartRendererName) {
    case 'plotly':
      chartRenderers = $.pivotUtilities.plotly_renderers;
      nCharts = 6;
      break;
    case 'gchart':
      chartRenderers = $.pivotUtilities.gchart_renderers;
      google.charts.load("visualization", "1", {packages:["corechart", "charteditor"]});
      nCharts = 5;
      break;
    case 'c3':
      chartRenderers = $.pivotUtilities.c3_renderers;
      nCharts = 5;
      break;
    default:
      chartRenderers = $.pivotUtilities.plotly_renderers;
      nCharts = 6;
      break;      
  }
  
  $.getJSON("/_load_pivot_data", function( resp ) {
      var pivotData = resp.data;
      var pivotOptions = {
          //rows: ['scenario'],
          //cols: ['year'],
          vals: ['value'],
          aggregatorName: "Average",
          //rendererName: "Line Chart",
          renderers: $.extend(chartRenderers, $.pivotUtilities.renderers)
      };
      pivotOutput.pivotUI( pivotData, pivotOptions, true );
      
      //add optgroups
      $('#pivot tbody').children('tr:first').children('td:first').addClass('pvtSelect');
      var select = $(".pvtSelect select");
      var selections = select.children();
      select.empty();
      var charts = $('<optgroup>').attr('label','Charts');
      var tables = $('<optgroup>').attr('label','Tables');
      selections.each(function(i, option) {
        if ( i < nCharts) {
          charts.append(option);
        } else {
          tables.append(option);
        }
      })
      select.append(charts);
      select.append(tables);
      prettifyPivot();
  });
}

function prettifyPivot() {
  // bootstrapify the pivotUI
  $(".pvtSelect select").addClass('selectpicker')
    .attr({'data-style': 'btn-primary', 'title': 'Chart or table...'}).selectpicker('refresh');
  $(".pvtVals select").addClass('selectpicker')
    .attr({'data-style': 'btn-default'}).selectpicker('refresh');
  $(".pvtAttrDropdown").addClass('selectpicker').selectpicker('refresh');
  $("#pivot button:contains('Select')").addClass('btn btn-default');
  $("#pivot button:contains('OK')").addClass('btn btn-primary')
    .parent().css('margin-bottom', '0px')
  $("#pivot input.pvtSearch").addClass('form-control').css('margin-top', '5px');
  //$('.pvtAttrDropdown option').first().text('[no attribute]');
}

$(function() {

  //spinner = $('<div>').appendTo('body');
  //spinner.spin()
  
  pivotOutput = $("#pivot");
  
  loadPivot(chartRenderName = 'plotly');
  //spinner.hide().spin(false);
  
  $("#load_options").click( function() {
    //spinner.show().spin();
    pivotOutput.empty();
    loadPivot(chartRendererName = $("#chart_renderer").val());
    //spinner.hide().spin(false);
  });  
  

});
