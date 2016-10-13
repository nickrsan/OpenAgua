var pivotOutput, filterParams = {};

function loadPivot(chartRendererName='plotly', filterParams, chartWidth) {

  // Get JSON-formatted data from the server
  var chartRenderers, nCharts, opts, defaultVals;
  
  switch(chartRendererName) {
    case 'plotly':
      chartRenderers = $.pivotUtilities.plotly_renderers;
      opts = {width: chartWidth}
      nCharts = 6;
      break;
    case 'gchart':
      chartRenderers = $.pivotUtilities.gchart_renderers;
      google.charts.load("visualization", "1", {packages:["corechart", "charteditor"]});
      opts = {gchart: {width: chartWidth}}
      nCharts = 5;
      break;
    case 'c3':
      chartRenderers = $.pivotUtilities.c3_renderers;
      opts = {c3: {size: {width: chartWidth}}};
      nCharts = 5;
      break;
    default:
      break;      
  }
  
  if (filterParams === {}) {
    defaultVals = ['value']
  } else {
    defaultVals = []
  }
  
  $.getJSON("/_load_pivot_data", {filters: JSON.stringify(filterParams)}, function( resp ) {
      var pivotData = resp.data;
      var pivotOptions = {
          vals: defaultVals,
          aggregatorName: "Average",
          renderers: $.extend(chartRenderers, $.pivotUtilities.renderers),
          rendererOptions: opts,
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
  // prettify the pivotUI (including with Bootstrap classes)
  $(".pvtSelect select").addClass('selectpicker')
    .attr({'data-style': 'btn-primary', 'title': 'Chart or table...'}).selectpicker('refresh');
  $(".pvtVals select").addClass('selectpicker')
    .attr({'data-style': 'btn-default'}).selectpicker('refresh');
  $(".pvtAttrDropdown").addClass('selectpicker').selectpicker('refresh');
  $("#pivot button:contains('Select')").addClass('btn btn-default');
  $("#pivot button:contains('OK')").addClass('btn btn-primary')
    .parent().addClass('pvtSearchOk');
  $("#pivot input.pvtSearch").addClass('form-control').css('margin-top', '5px');
  //$('.pvtAttrDropdown option').first().text('[no attribute]');
}

$(function() {

  pivotOutput = $("#pivot");

  // make plotly node
  //var gd = Plotly.d3.select('body').append('div').node();
  
  loadPivot(chartRenderName='plotly',
    filterParams=filterParams,
    chartWidth=getChartWidth());
  
  $("#load_options").click( function() {
    pivotOutput.empty();
    loadPivot(
      chartRendererName=$("#chart_renderer").val(),
      filterParams=filterParams,
      chartWidth=getChartWidth()
    );
  });

  var d3 = Plotly.d3;

  var HEIGHT_IN_PERCENT_OF_PARENT = 80;

  var gd3 = d3.select('.pvtRendererArea')
      .style({
          width: getChartWidth(),  
          height: HEIGHT_IN_PERCENT_OF_PARENT + 'vh',
      });
      
  var chartNode = gd3.node();

  $( window ).resize(function() {
    var width = getChartWidth();
    var chartNode = Plotly.d3.select('.pvtRendererArea').style('width', width).node();
    Plotly.Plots.resize(chartNode);
  });
  
  // load feature types
  $('#filterby').on('changed.bs.select', function (e) {
    var selected = $('#filterby option:selected');
    if (selected.length) {
      $('.filters').hide();
      filterby = selected.val();
      if (filterby !== 'none' && filterby !== null) {
        $('#'+filterby+'_filter_container').show();
        filterParams.filterby = filterby;
      } else {
        filterParams = {};
        $('.filter').hide();
        $(".filter option").removeAttr("selected");
        $('.filter select').selectpicker('refresh');
      }
    }
  });
  
  $('#res_type_filter').on('hidden.bs.select', function(e) {
    var idx, ttype_id, type_attrs, attr_id;
    var type_attrs = [];
    filterParams.ttype_ids = [];
    $('#res_type_filter option:selected').each(function() {
      ttype_id = Number($(this).attr('data-id'));
      if (type_attrs.length) {
        type_attrs = _.intersectionBy(type_attrs, ttypes[ttype_id].typeattrs, 'attr_id');
      } else {
        type_attrs = ttypes[ttype_id].typeattrs;
      }
      filterParams.ttype_ids.push(ttype_id);
    });
    var select = $('#secondary_filter').attr('title', 'Variables').empty();
    $.each(type_attrs, function(i, ta) {
      select.append($('<option>').val(ta.attr_id).text(ta.attr_name));
    });
    select.selectpicker('refresh');
    $('#secondary_filter_container').show();
  });
  
  $('#secondary_filter').on('hidden.bs.select', function(e) {
    filterParams.attr_ids = [];
    $('#secondary_filter option:selected').each(function() {
      //attr_id = Number($(this).attr('data-id'));
      attr_id = Number($(this).val()); // this is inconsistent with above method, but is correct
      filterParams.attr_ids.push(attr_id);
    });
  });
  
});

function getChartWidth() {
  return $("#pivot_panel").width() - 250; //$(".pvtRows").width() 
}

function loadFilteredData() {

}

//$('#save_as_thumbnail').click(function() {
    //html2canvas($("#pvtRendererArea"), {
      //onrendered: function(canvas) {
        //$("body").append(canvas);
      //}
    //});
//});