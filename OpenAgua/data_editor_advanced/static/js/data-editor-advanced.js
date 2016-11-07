var pivotOutput,
  type_attrs = [], 
  plotlyDiv = 'plotlyArea',
  inputLabel = 'Input',
  previewLabel = 'Preview',
  pivotOptions,
  pvtTypeOld;
var pvtTypeOld = 'Input';

$( document ).ready( function() {
  pivotOutput = $("#pivot");
  pivotOptions = pivotSetup.config;

  loadPivot(
    pivotSetup.renderer,
    getPivotWidth(),
    getPivotHeight()
  );  

  var attr_id;

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
      width=getPivotWidth(),
      height=getPivotHeight()
    );
  });

});

function loadPivot(chartRendererName, width, height) {
  spinner.spin(spinDiv);
  // Get JSON-formatted data from the server
  var chartRenderers, nCharts, opts, defaultVals;

  switch(chartRendererName) {
    case 'plotly':
      chartRenderers = $.pivotUtilities.plotly_renderers;
      opts = {
        width: getPivotWidth,
        height: getPivotHeight,
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
  
  var nTables = 2;

  opts.onEditValues = function (changes) { $(".changesOutput").html(JSON.stringify(changes)) };
  opts.onDrawTable = function (htTable) { $(".changesOutput").empty() };

  // handsontable
  opts.showTotals = false;

  activeRenderer = chartRendererName;

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
    renderers: $.extend({}, $.pivotUtilities.novix_renderers, chartRenderers),
    rendererName: "Input Table",
    rendererOptions: opts,
  });

  pivotOptions.cols = [];
  pivotOptions.rows = ["year", "month"];
  
  pivotOptions.onRefresh = function(config) {
    //pivotConfig = JSON.parse(JSON.stringify(config));
    pivotSetup.config = JSON.parse(JSON.stringify(config));
    //delete some values which are functions
    delete pivotSetup.config["aggregators"];
    delete pivotSetup.config["renderers"];
    //delete some bulky default values
    delete pivotSetup.config["rendererOptions"];
    delete pivotSetup.config["localeStrings"];
    pivotSetup.renderer = chartRendererName
  }

  $.getJSON("/_load_pivot_data", {filters: JSON.stringify(filterParams)}, function( resp ) {
    var pivotData = resp.data;
    makePivot(pivotOutput, pivotData, pivotOptions, true, nTables)
    //addAutoTranspose(pivotData, nTables);
  });

  spinner.spin(false);
}

// add the pivot area
function makePivot(container, data, options, overwrite, nTables) {
    container.pivotUI( data, options, overwrite );
    addOptGroups(nTables);
    addTheme(options.rendererName);
    addAutoTranspose(data, nTables); // delete data and get from within function
}

function addOptGroups(nTables) {
  //add optgroups
  var select = $(".pvtRenderer");
  var selections = select.find('option');
  var tables = $('<optgroup>').attr('label', inputLabel);
  var charts = $('<optgroup>').attr('label', previewLabel);
  //select.empty();
  select.append(tables);
  select.append(charts);
  selections.each(function(i, option) {
    if ( i < nTables) {
      $(this).appendTo(tables);
    } else {
      $(this).appendTo(charts);
    }
  });
}

function addTheme(originalVal) {
  // prettify the pivotUI (including with Bootstrap classes)
  $('#pivot tbody').children('tr:first').children('td:first').addClass('pvtSelect');
  //$(".pvtSelect select")
  var pvtRenderer = $(".pvtSelect select").addClass('selectpicker').attr({'id':'pvtSelect', 'data-style': 'btn-primary'})
  if (originalVal === undefined || originalVal.length === 0) {
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

// swap rows & columns when switching between input and preview
function addAutoTranspose(pivotData, nTables) {
  var select = $('#pvtSelect');
  select.on('hidden.bs.select', function() {
    var pvtType = $(this).find("option:selected").parent().attr('label');
    if (pvtType !== pvtTypeOld) {
      var rendererName = $(this).find("option:selected").val();
      pivotOptions.rendererName = rendererName;
      pivotOptions.cols = pivotSetup.config.rows;
      pivotOptions.rows = pivotSetup.config.cols;
      // need a line to get pivotData from table (i.e., as modified)
      makePivot(pivotOutput, pivotData, pivotOptions, true, nTables)
    }
    pvtTypeOld = pvtType;
  });
}

// RESIZE FUNCTIONS

$(function () {
  $(window).on('resize', resizePivot);
  $('#menu-toggle').on('click', resizePivotDelay);
});

function resizePivotDelay() {
  setTimeout(resizePivot, 500);
}

function resizePivot() {
  var rArea = $('.pvtRendererArea');
  if (rArea.find('#plotlyArea').length) {
    resizePlotly();
  } else if (rArea.find('.novixPivot').length) {
    resizeHot();
  }
}

function resizePlotlyDelay() {
  var timeout = setTimeout(resizePlotly(), 500);
}

function resizePlotly() {
  Plotly.relayout(plotlyDiv, {
    width: getPivotWidth(),
    height: getPivotHeight()
  });
  Plotly.redraw(plotlyDiv);
}

function resizeHotDelay() {
  var timeout = setTimeout(resizeHot, 500);
}

function resizeHot() {
  $('.novixPivot').height(getPivotHeight());
  //var hot = $('.novixPivot').handsontable('getInstance');
  //hot.updateSettings({
    //height: getPivotHeight()
  //});
}

var getPivotWidth = function() {
  return window.innerWidth - getWidthOffset();
}

var getPivotHeight = function() {
  return window.innerHeight - getHeightOffset();
}

function getWidthOffset() {
  return $('#sidebar-wrapper').width() + 280;
}

function getHeightOffset() {
  return $('#navbar').height() + 250;
}

//BOTTOM

$( function() {

  $('.save').click( function(e) {
    e.preventDefault();
    var saveType = $(this).attr('id'),
      div = $('#'+plotlyDiv),
      //dw = div.width(),
      //dh = div.height(),
      w, h;
    var dw = 900;
    //var dh = dw * 6 / 9;
    var dh = dw * 1 / 2;
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

      switch(saveType) {
        case 'save':
          saveDialog(url, w, h);
          break;
        case 'saveas':
          saveAsDialog(url, w, h);
          break;
        default:
          break;
      }

    });
  });
});

function saveDialog(url, w, h) {

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

function saveAsDialog(url, w, h) {

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
  formData.append('setup', JSON.stringify(pivotSetup));
  formData.append('asnew', asnew);
  $.ajax({
    type: "POST",
    url: '_save_chart',
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function(resp){
      notify('success', 'Success!', 'Chart saved to Chart Collection.')
    }
  });
}
