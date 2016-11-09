var pivotOutput,
  hot = null,
  type_attrs = [],
  aggregators;

$( document ).ready( function() {
  pivotOutput = $("#pivot");

  var attr_id;
  
  $('#favorites').on('click','.delete', function(e) {
    e.stopPropagation();
    var setupId = $(this).data('id');
    var setupName = $(this).val();
    deleteSetup(setupId, setupName);
  });
  
  $('#favorites').on('click', 'a', function(e) {
    var setupId = $('#favorites select option:selected').data('id');
    loadPivot(setupId);
  });

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
    var type_attrs = null;
    filterParams.ttype_ids = [];
    var selected_ttypes = $('#res_type_filter option:selected');

    if (selected_ttypes.length) {
      $.each(selected_ttypes, function(key, selected_ttype) {
        ttype_id = Number(selected_ttype.dataset.id);
        if (type_attrs === null) {
          type_attrs = ttypes[ttype_id].typeattrs;
        } else {
          type_attrs = _.intersectionBy(type_attrs, ttypes[ttype_id].typeattrs, 'attr_id');
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
    loadPivot(0); // load filters with no favorite
  });
  
  $("#pivot").arrive('.ht_clone_top_left_corner', function(){
    resizePivot();
  });
  
  aggregators = _.pick($.pivotUtilities.aggregators, ['Sum', 'Average']);
  
});

function loadPivot(setup_id) {
  spinOn('Loading data...');

  var data = {filters: filterParams, setup_id: setup_id}
  
  $.ajax({
    type: "POST",
    url: '_load_input_data',
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: function(resp) {
      var pivotData = resp.data;
      var pivotOptions = extendOptions(resp.setup);
      pivotOutput.pivotUI( pivotData, pivotOptions, true );
      $('.pvtAttr:contains("value")').closest('li').hide();
      types = $('.pvtAttr:contains("feature type")');
      addTheme();
      spinOff();
    }
  });
}

function extendOptions(options) {
  // default options if they are not provided
  if ( Object.keys(options).length === 0 ) {
    options = {
      vals: ['value'],
      cols: [],
      rows: ["year", "month"],
      aggregatorName: "Average",
    };
  }

  // renderers and options not saved with chart
  $.extend(options, {
    renderers: $.extend({}, $.pivotUtilities.novix_renderers),
    rendererOptions: {
      showTotals: false
    },
    rendererName: 'Input Table',
    aggregators: aggregators
  });

  options.onRefresh = function(config) {
    pivotConfig = JSON.parse(JSON.stringify(config));
    delete pivotConfig["aggregators"];
    delete pivotConfig["renderers"];
    delete pivotConfig["rendererOptions"];
    delete pivotConfig["localeStrings"];
  }
  
  //opts.onEditValues = function (changes) {
  ////$(".changesOutput").html(JSON.stringify(changes))
  //$(".changesOutput").text('Changes not saved.')
  //};
  //opts.onDrawTable = function (htTable) {
    //$(".changesOutput").empty()
  //};
  return options;
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

$(function () {
  $(window).on('resize', resizePivot);
  $('#menu-toggle').on('click', resizePivotDelay);
});

function resizePivotDelay() {
  setTimeout(resizePivot, 500);
}

function resizePivot() {
  if ($('.novixPivot').length) {
    hot.updateSettings({
      height: getPivotHeight(),
      width: getPivotWidth()
    });
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

var getPivotWidth = function() {
  return window.innerWidth - getWidthOffset();
}

var getPivotHeight = function() {
  return window.innerHeight - getHeightOffset();
}

function getWidthOffset() {
  return $('#sidebar-wrapper').width() + 260;
}

function getHeightOffset() {
  return $('#navbar').height() + 230;
}

//BOTTOM

$( function() {

  $('.savesetup').click( function(e) {
    e.preventDefault();
    var saveType = $(this).attr('id');
    switch(saveType) {
      case 'savesetup':
        
        break;
      case 'savesetupas':
        saveSetupAsDialog();
        break;
      default:
        break;
    }
  });
  
  $('.savedata').click( function(e) {
    var data = hot.getData();
    saveData(pivotConfig, data)
  });
  
});

function saveSetupDialog(url, w, h) {

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
        saveSetup(formData, false);
      }
    }
  });
}

function saveSetupAsDialog() {

  //var thumbnail = $('<div>')
    //.append($('<img>').attr('src', url).height(h).width(w).css('border', 'thin solid grey'))
    //.css({'text-align': 'center'});

  var form = $('<form id="setup_form">').html(
  '<div class="form-group"> \
    <label for="name">Name</label> \
    <input type="text" class="form-control" id="name" name="name"> \
  </div> \
  <div class="form-group"> \
    <label for="description">Description</label> \
    <textarea class="form-control" id="description" name="description"/> \
  </div> \
  <p id="saveerror"></p>')

  var form = $('<div>')
    //.append(thumbnail)
    .append(form)
    .html();
  bootbox.confirm({
    title: 'Save setup',
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
        if ($.inArray(name, Object.values(savedSetups)) === 0) {
          $('#saveerror').text('Name already exists.')
          return false;
        } else {
          var form = $('#setup_form')[0];
          var formData = new FormData(form);
          saveSetup(formData, true);
        }
      }
    }
  });
}

saveSetup = function(formData, asnew) {
  formData.append('filters', JSON.stringify(filterParams));
  formData.append('setup', JSON.stringify(pivotConfig));
  formData.append('asnew', asnew);
  $.ajax({
    type: "POST",
    url: '_save_setup',
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function(resp) {
      notify('success', 'Success!', 'Setup saved.');
      var favorites = $('#favorites select');
      var name = formData.get('name');
      savedSetups[resp.setup_id] = name;
      newOption = $('<option>').attr('data-id', resp.setup_id).text(name);
      favorites.append(newOption).selectpicker('refresh');
      favorites.selectpicker('val', name);
    }
  });
}

function deleteSetup(setupId, setupName) {
  bootbox.confirm({
    title: 'Delete setup',
    message: 'Delete "'+setupName+'" input setup? This will not delete any data.',
    callback: function(confirm) {
      if (confirm) {
        $.ajax({
          type: 'POST',
          url: '/_delete_setup',
          data: JSON.stringify({setup_id: setupId}),
          contentType: 'application/json',
          success: function(resp) {
            if (resp.result === 1) {
              notify('success', 'Success!', 'Setup deleted.');
              $("#favorites select option[data-id='"+setupId+"']").remove();
              $("#favorites select").selectpicker('refresh');
            } else {
              notify('warning', 'Uh-oh.', 'Something went wrong. Setup not deleted.');
            }
          }
        });   
      }
    }
  });
}

saveData = function(setup, data) {
  $.ajax({
    type: "POST",
    url: '_save_data',
    data: JSON.stringify({setup: setup, data: data}),
    contentType: 'application/json',
    success: function(resp) {
      if (!resp.error) {
        notify('success', 'Success!', 'Data saved.');
      } else {
        notify('warning', 'Uh-oh!', 'Something went wrong. Data not saved.')
      }
    }
  });
}
