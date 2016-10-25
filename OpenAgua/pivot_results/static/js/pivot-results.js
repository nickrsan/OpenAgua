var pivotOutput, filterParams = {}, plotlyDiv = 'plotlyArea',
  plotlyListenerBuilt = false, loadedChart = null;

$( document ).ready( function() {

  pivotOutput = $("#pivot");
  
  loadPivot( chartRendererName = 'plotly', width=getChartWidth(), height=getChartHeight() );  
  
  // load feature types
  $('#filterby').on('changed.bs.select', function (e) {
    var selected = $('#filterby option:selected');
    if (selected.length) {
      $('.filter').hide();
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
    var selected_ttypes = $('#res_type_filter option:selected');
    
    if (selected_ttypes.length) {
      $.each(selected_ttypes, function(key, selected_ttype) {
        ttype_id = Number(selected_ttype.dataset.id);
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
    } else {  
      $('#secondary_filter_container').hide();
      $("#secondary_filter").removeAttr("selected");
      $('#secondary_filter').selectpicker('refresh');
      filterParams.ttype_ids = [];
    }
  });
  
  $('#secondary_filter').on('hidden.bs.select', function(e) {
    filterParams.attr_ids = [];
    $('#secondary_filter option:selected').each(function() {
      //attr_id = Number($(this).attr('data-id'));
      attr_id = Number($(this).val()); // this is inconsistent with above method, but is correct
      filterParams.attr_ids.push(attr_id);
    });
  });
  
  $("#load_options").click( function() {
    //pivotOutput.empty();
    loadPivot( chartRendererName=$("#chart_renderer").val(), width=getChartWidth(), height=getChartHeight() );
  });

  
});

function loadPivot(chartRendererName, width, height) {

  // Get JSON-formatted data from the server
  var chartRenderers, nCharts, opts, defaultVals;
  
  switch(chartRendererName) {
    case 'plotly':
      chartRenderers = $.pivotUtilities.plotly_renderers;
      opts = {
        width: width,
        height: height,
        divname: plotlyDiv
      }
      nCharts = 6;
      break;
    case 'gchart':
      chartRenderers = $.pivotUtilities.gchart_renderers;
      google.charts.load("visualization", "1", {packages:["corechart", "charteditor"]});
      opts = {gchart: {width: width, height: height}}
      nCharts = 5;
      break;
    case 'c3':
      chartRenderers = $.pivotUtilities.c3_renderers;
      opts = {c3: {size: {width: width, height: height}}};
      nCharts = 5;
      break;
    default:
      break;      
  }
  
  loadedChart = chartRendererName;
  
  var defaultVals
  if (Object.keys(filterParams).length === 0) {
    defaultVals = ['value']
  } else {
    defaultVals = []
  }
  
  opts.onEditValues = function (changes) { $(".changesOutput").html(JSON.stringify(changes)) }
  opts.onDrawTable = function (htTable) { $(".changesOutput").empty() }
  
  $.getJSON("/_load_pivot_data", {filters: JSON.stringify(filterParams)}, function( resp ) {
      var pivotData = resp.data;
      var pivotOptions = {
          vals: defaultVals,
          aggregatorName: "Average",
          renderers: $.extend({}, chartRenderers, $.pivotUtilities.renderers),
          //renderers: $.extend({}, chartRenderers, $.pivotUtilities.novix_renderers, $.pivotUtilities.renderers),
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
      updateResizeListener(chartRendererName);
  });
}

function prettifyPivot() {
  // prettify the pivotUI (including with Bootstrap classes)
  $(".pvtSelect select").addClass('selectpicker')
    .attr({'id':'pvtSelect', 'data-style': 'btn-primary', 'title': 'Chart or table...'}).selectpicker('refresh');
  $(".pvtVals select").addClass('selectpicker')
    .attr({'data-style': 'btn-default'}).selectpicker('refresh');
  $(".pvtAttrDropdown").addClass('selectpicker').selectpicker('refresh');
  $("#pivot button:contains('Select')").addClass('btn btn-default');
  $("#pivot button:contains('OK')").addClass('btn btn-primary')
    .parent().addClass('pvtSearchOk');
  $("#pivot input.pvtSearch").addClass('form-control').css('margin-top', '5px');
  $('table tr td:nth-child(2)').css('width','100%');
  //$("<div>").attr('id', 'plotArea').css({width: "100%", height: "100%"})
    //.appendTo($('body'));
  //$('.pvtAttrDropdown option').first().text('[no attribute]');
}

function updateResizeListener(chartRendererName) {
  $('#pvtSelect').off('hidden.bs.select');
  $('#pvtSelect').on('hidden.bs.select', function() {
    if ($(this).find('option:selected').parent().attr('label') == 'Charts') {
      //loadedChart = chartRendererName;
      var element = $('#page-content-wrapper');
      switch(chartRendererName) {
        case 'plotly':
          setTimeout(function(){ resizePlotlyChart() }, 50);
          if (!plotlyListenerBuilt) {
            $(window).resize(function() {
              if (loadedChart === chartRendererName) {resizePlotlyChart()}
            });
            $('#menu-toggle').on('click', function() {
              if (loadedChart === chartRendererName) {
                resized = setTimeout(function(){ resizePlotlyChart() }, 500)
              }
            });
            plotlyListenerBuilt = true;
          }
          
          break;
        default:
          break;
      }
    } else {
      loadedChart = null;
    }
  });
}

function resizePlotlyChart() {
  Plotly.relayout(plotlyDiv, {width: getChartWidth(), height: getChartHeight()});
  Plotly.redraw(plotlyDiv);
}

function getChartWidth() {
  return $('#page-content-wrapper').width() - 280;
}

function getChartHeight() {
  return $(window).height() - 255;
}

//$('#save_as_thumbnail').click(function() {
    //html2canvas($("#pvtRendererArea"), {
      //onrendered: function(canvas) {
        //$("body").append(canvas);
      //}
    //});
//});