var pivotOutput,
  type_attrs = [], 
  plotlyDiv = 'plotlyArea',
  plotlyListenerBuilt = false, loadedChart = null;

$( document ).ready( function() {
  pivotOutput = $("#pivot");
  
  loadPivot(
    chartRendererName = chartSetup.renderer,
    width = getChartWidth(),
    height = getChartHeight(),
    pivotOptions = chartSetup.config
  );  
  
  var attr_id;
  
  //$('#chart_renderer').select2();
  
  // load feature types
  //$('#filterby').select2({
   //placeholder: 'Filter by...'
  //});
  
  //$('#filterby').on('change', function (e) {
    //var selected = $('#filterby option:selected');
    //type_attrs = [];
    //if (selected.length) {
      //$('.filter').hide();
      //filterby = selected.val();
      //if (filterby !== 'none' && filterby !== null) {
        //$('#'+filterby+'_filter_container').show();
        //filterParams.filterby = filterby;
      //} else {
        //filterParams = {};
        //$('.filter').hide();
        ////$(".filter option").removeAttr("selected");
        ////$('.filter select').selectpicker('refresh');
      //}
    //}
  //});

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
  
  //$('#res_type_filter').select2({
    //placeholder: 'Select a feature...',
    //multiple: 'multiple'
  //});

  //$('#res_type_filter').on('change', function(e) {
    //var ttype_id;
    //filterParams.ttype_ids = [];
    //var selected_ttypes = $('#res_type_filter option:selected');
    
    //if (selected_ttypes.length) {
      //$.each(selected_ttypes, function(key, selected_ttype) {
        //ttype_id = Number(selected_ttype.dataset.id);
        //filterParams.ttype_ids.push(ttype_id);
        //if (type_attrs.length) {
          //type_attrs = _.intersectionBy(type_attrs, ttypes[ttype_id].typeattrs, 'attr_id');
        //} else {
          //type_attrs = ttypes[ttype_id].typeattrs;
        //}
      //});
      
      //var select = $('#secondary_filter').empty();
      //$.each(type_attrs, function(i, ta) {
        //select.append($('<option>').val(ta.attr_id).text(ta.attr_name));
      //});
      //select.select2({
        //placeholder: 'Select variables...',
        //multiple: 'multiple'
      //});
      //$('#secondary_filter_container').show();
    //} else {  
      //$('#secondary_filter_container').hide();
      ////$("#secondary_filter").removeAttr("selected");
      ////$('#secondary_filter').selectpicker('refresh');
      //filterParams.ttype_ids = [];
    //}
  //});
  
  $('#res_type_filter').on('hidden.bs.select', function(e) {
    var idx, ttype_id, type_attrs;
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
    $('#secondary_filter option:selected').each(function(i, item) {
      filterParams.attr_ids.push(Number(item.value));
    });
  });
  
  $("#load_options").click( function() {
    loadPivot(
      chartRendererName=$("#chart_renderer").val(),
      width=getChartWidth(),
      height=getChartHeight()
    );
  });
  
});

function loadPivot(chartRendererName, width, height, pivotOptions={}) {
  spinner.spin(spinDiv);
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
  
  opts.onEditValues = function (changes) { $(".changesOutput").html(JSON.stringify(changes)) };
  opts.onDrawTable = function (htTable) { $(".changesOutput").empty() };
  
  loadedChart = chartRendererName;
  
  var defaultVals
  if (Object.keys(filterParams).length === 0) {
    defaultVals = ['value']
  } else {
    defaultVals = []
  }
  
  // default options if they are not provided
  if ( Object.keys(pivotOptions).length === 0 ) {
    pivotOptions = {
      vals: defaultVals,
      aggregatorName: "Average",
    };
  }
  
  // renderers and options not saved with chart
  $.extend(pivotOptions, {
    renderers: $.extend({}, chartRenderers, $.pivotUtilities.renderers),
    rendererOptions: opts
  });
  
  pivotOptions.onRefresh = function(config) {
      var pivot_config = JSON.parse(JSON.stringify(config));
      //delete some values which are functions
      delete pivot_config["aggregators"];
      delete pivot_config["renderers"];
      //delete some bulky default values
      delete pivot_config["rendererOptions"];
      delete pivot_config["localeStrings"];
      chartSetup.config = pivot_config;
      chartSetup.renderer = chartRendererName
  }
  
  $.getJSON("/_load_pivot_data", {filters: JSON.stringify(filterParams)}, function( resp ) {
      var pivotData = resp.data;      
      pivotOutput.pivotUI(
        pivotData,
        pivotOptions,
        true
      );
      addOptGroups(nCharts);
      prettifyPivot(chartSetup.config.rendererName);
      updateResizeListener(chartRendererName);

  });
  
  spinner.spin(false);
}

function addOptGroups(nCharts) {
    //add optgroups
    var select = $(".pvtRenderer");
    var selections = select.children();
    var charts = $('<optgroup>').attr('label','Charts');
    var tables = $('<optgroup>').attr('label','Tables');
    select.append(charts);
    select.append(tables);
    selections.each(function(i, option) {
      if ( i < nCharts) {
        $(this).appendTo(charts);
      } else {
        $(this).appendTo(tables);
      }
    });
}

function prettifyPivot(originalVal) {
  // prettify the pivotUI (including with Bootstrap classes)
  $('#pivot tbody').children('tr:first').children('td:first').addClass('pvtSelect');
  //$(".pvtSelect select")
  var pvtRenderer = $(".pvtSelect select").addClass('selectpicker').attr({'id':'pvtSelect', 'data-style': 'btn-primary'})
  if (originalVal.length === 0) {
    pvtRenderer.attr('title', 'Chart or table...');
  }
  pvtRenderer.selectpicker('refresh');
  $(".pvtAggregator").addClass('selectpicker').attr({'data-style': 'btn-default'}).selectpicker('refresh');
  $(".pvtAttrDropdown").addClass('selectpicker').selectpicker('refresh');
  $("#pivot button:contains('Select')").addClass('btn btn-default');
  $("#pivot button:contains('OK')").addClass('btn btn-primary')
    .parent().addClass('pvtSearchOk');
  $("#pivot input.pvtSearch").addClass('form-control').css('margin-top', '5px');
  $('table tr td:nth-child(2)').css('width','100%');
  //$("<div>").attr('id', 'plotArea').css({width: "100%", height: "100%"})
    //.appendTo($('body'));
  //$('.pvtAttrDropdown option').first().text('[no attribute]');
  //$('.pvtSelect').selectpicker('val', originalVal);
  $('.pvtSelect').selectpicker('refresh');
}

function updateResizeListener(chartRendererName) {
  $('#pvtSelect').off('hidden.bs.select');
  $('#pvtSelect').on('hidden.bs.select', function() {
    if ($(this).find('option:selected').parent().attr('label') == 'Charts') {
      loadedChart = chartRendererName;
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
  return $(window).height() - 300;
}

//BOTTOM

$( function() {

  $('.save').click( function(e) {
  
    e.preventDefault();
    var div = $('#'+plotlyDiv);
    var dw = div.width(), dh = div.height();
    var w, h;
    if ( dw >= dh ) {
      w = 300;
      h = dh * w / dw;
    } else {
      h = 300;
      w = dw * h / dh;
    }
    Plotly.toImage(div[0], {
        format: 'png',
        height: dh,
        width: dw,
      })
      .then(function(url){
      
        switch($(this).attr('id')) {
          case 'save':
            saveDialog(url);
            break;
          case 'saveas':
            saveAsDialog(url);
            break;
          default:
            break;
        }
        
      });
  });
});

function saveAsDialog(url) {

  var thumbnail = $('<div>')
    .append($('<img>').attr('src', url).height(h).width(w).css('border', 'thin solid grey'))
    .css({'text-align': 'center'});
    
  var form = $('<form>')
  var form = $('<div>').append(thumbnail).append(form).html();
  bootbox.confirm({
      title: 'Overwrite existing chart?',
      message: form,
      closeButton: true,
      buttons: {
          cancel: {
              label: '<i class="fa fa-times"></i> Cancel'
          },
          confirm: {
              label: '<i class="fa fa-check"></i> Save'
          }
      },
      callback: function(result) {
        if (result) {
          var form = $('#chart_form')[0];
          var formData = new FormData(form);
          saveChart(formData, url, false);
        }
      }
  });
}

function saveAsDialog(url) {

  var thumbnail = $('<div>')
    .append($('<img>').attr('src', url).height(h).width(w).css('border', 'thin solid grey'))
    .css({'text-align': 'center'});
    
  var form = $('<form id="chart_form">').html(
  '<br/><div class="form-group"> \
    <label for="name">Name</label> \
    <input type="text" class="form-control" id="name" name="name"> \
  </div> \
  <div class="form-group"> \
    <label for="description">Description</label> \
    <textarea class="form-control" id="description" name="description"/> \
  </div> \
  <p id="saveerror"></p>')
  
  var form = $('<div>')
    .append(thumbnail)
    .append(form)
    .html();
  bootbox.confirm({
      title: 'Save to collection',
      message: form,
      closeButton: true,
      buttons: {
          cancel: {
              label: '<i class="fa fa-times"></i> Cancel'
          },
          confirm: {
              label: '<i class="fa fa-check"></i> Save'
          }
      },
      callback: function(result) {
        if (result) {
          var name = $('#name').val();
          if ($.inArray(name, chartNames) === 0) {
            $('#saveerror').text('Name already exists.')
            return false;
          } else {
            var form = $('#chart_form')[0];
            var formData = new FormData(form);
            saveChart(formData, url, true);
            chartNames.push(name);
          }
        }
      }
  });
}

saveChart = function(formData, url, asnew) {
  formData.append('thumbnail', url);
  formData.append('filters', JSON.stringify(filterParams));
  formData.append('setup', JSON.stringify(chartSetup));
  formData.append('asnew', asnew);
  $.ajax({
    type: "POST",
    url: '_save_chart_as',
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function(resp){
      notify('success', 'Success!', 'Chart saved to Chart Collections.')
    }
  });
}
