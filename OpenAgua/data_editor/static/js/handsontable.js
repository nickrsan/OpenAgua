// make handsontable
function makeHandsontable(divname, tableHeight) {

  // settings
  var contextMenu = ['undo', 'redo']
  
  // create the chart
  var container = document.getElementById(divname);
  hot = new Handsontable(container, {
    manualColumnResize: true,
    manualRowResize: false,
    height: tableHeight,
    stretchH: 'last',
    minSpareRows: 0,
    minSpareCols: 0,
    //rowHeaders: true,
    contextMenu: contextMenu,
  });
  
  return hot;

}

// make handsontable
function updateHandsontable(data, colHeaders) {

  // some preprocessing
  var colWidths = [70].concat(_.times(colHeaders.length-1, _.constant(80)));
  var timesteps = _.map(data, function(item) {
      return item.date    
  });
  var numeric_cols = _.map(_.tail(colHeaders), function(item) {
    return {data: 'value', editor: 'numeric'}  
  })
  var columns = [{data: 'date', editor: false}].concat(numeric_cols)
  
  // create the chart
  hot.updateSettings({
    data: data,
    colWidths: colWidths,
    minCols: colHeaders.length,
    maxCols: colHeaders.length,
    minRows: data.length,
    maxRows: data.length,
    colHeaders: colHeaders,
    columns: columns
  });
}