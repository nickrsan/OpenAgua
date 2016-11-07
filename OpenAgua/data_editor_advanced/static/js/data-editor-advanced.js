var pivotOutput,
  type_attrs = [];

$( document ).ready( function() {
  pivotOutput = $("#pivot");

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

  $('#res_type_filter').on('changed.bs.select', function(e) {
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
    loadPivot();
  });

});

function loadPivot() {
  spinOn('Data loading...');
  
  // Get JSON-formatted data from the server
  var opts = {}, defaultVals;

  //opts.onEditValues = function (changes) {
    ////$(".changesOutput").html(JSON.stringify(changes))
    //$(".changesOutput").text('Changes not saved.')
  //};
  //opts.onDrawTable = function (htTable) {
    //$(".changesOutput").empty()
  //};

  // default options if they are not provided
  if ( Object.keys(pivotOptions).length === 0 ) {
    pivotOptions = {
      vals: ['value'],
      aggregatorName: "Average",
    };
  }

  // renderers and options not saved with chart
  $.extend(pivotOptions, {
    renderers: $.extend({}, $.pivotUtilities.novix_renderers),
    rendererOptions: {
      showTotals: false
    },
    rendererName: 'Input Table'
  });

  pivotOptions.cols = [];
  pivotOptions.rows = ["year", "month"];
  
  pivotOptions.onRefresh = function(config) {
    pivotConfig = JSON.parse(JSON.stringify(config));
    //delete some values which are functions
    delete pivotConfig["aggregators"];
    delete pivotConfig["renderers"];
    //delete some bulky default values
    delete pivotConfig["rendererOptions"];
    delete pivotConfig["localeStrings"];
  }

  $.getJSON("/_load_pivot_data", {filters: JSON.stringify(filterParams)}, function( resp ) {
    var pivotData = resp.data;
    //makePivot(pivotOutput, pivotData, pivotOptions, true);
    pivotOutput.pivotUI( pivotData, pivotOptions, true );
    //$('.pvtRenderer').hide().css('position','absolute');
    //$('.pvtAttrDropdown').hide().css('position','absolute');
    $('.pvtAttr:contains("scenario")').closest('li').hide();
    addTheme();
    spinOff();
  });
}

//// add the pivot area
//function makePivot(container, data, options, overwrite) {
//}

function addTheme() {
  $(".pvtAggregator").addClass('selectpicker').attr({'data-style': 'btn-default'}).selectpicker('refresh');
  $(".pvtAttrDropdown").addClass('selectpicker').selectpicker('refresh');
  $("#pivot button:contains('Select')").addClass('btn btn-default');
  $("#pivot button:contains('OK')").addClass('btn btn-primary')
    .parent().addClass('pvtSearchOk');
  $("#pivot input.pvtSearch").addClass('form-control').css('margin-top', '5px');
  $('table tr td:nth-child(2)').css('width','100%');
}

// RESIZE FUNCTIONS

//$(function () {
  //$(window).on('resize', resizePivot);
  //$('#menu-toggle').on('click', resizePivotDelay);
//});

function resizePivotDelay() {
  setTimeout(resizePivot, 500);
}

function resizePivot() {
  if ($('.novixPivot').length) {
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
    var saveType = $(this).attr('id');
    switch(saveType) {
      case 'save':
        //saveDialog(url, w, h);
        break;
      case 'saveas':
        //saveAsDialog(url, w, h);
        break;
      default:
        break;
    }
  });
});

function saveDialog(url, w, h) {

  var form = $('<form>')
  var form = $('<div>').append(thumbnail).append(form).html();
  bootbox.confirm({
    title: 'Overwrite existing setup?',
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
  formData.append('options', JSON.stringify(pivotConfig));
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
