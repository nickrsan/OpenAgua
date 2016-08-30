// make handsontable
function handsontable(divname, data, colHeaders, tableHeight) {

  // some preprocessing
  var colWidths = [70].concat(_.times(colHeaders.length-1, _.constant(80)));
  var timesteps = _.map(data, function(item) {
      return item.date    
  });
  var numeric_cols = _.map(_.tail(colHeaders), function(item) {
    return {data: 'value', editor: 'numeric'}  
  })
  var columns = [{data: 'date', editor: false}].concat(numeric_cols)
  var contextMenu = ['undo', 'redo']
  
  // create the chart
  var container = document.getElementById(divname);
  var hot = new Handsontable(container, {
    data: data,
    colWidths: colWidths,
    manualColumnResize: true,
    manualRowResize: false,
    height: tableHeight,
    stretchH: 'last',
    minCols: colHeaders.length,
    maxCols: colHeaders.length,
    minRows: data.length,
    maxRos: data.length,
    minSpareRows: 0,
    minSpareCols: 0,
    rowHeaders: true,
    colHeaders: colHeaders,
    contextMenu: contextMenu,
    columns: columns
  });
}