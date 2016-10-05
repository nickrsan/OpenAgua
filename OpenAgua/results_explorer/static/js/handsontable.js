// make handsontable
function makeHandsontable(divname, tableHeight) {

  // settings
  //var contextMenu = ['undo', 'redo']
  
  // create the chart
  var container = document.getElementById(divname);
  hot = new Handsontable(container, {
    manualColumnResize: true,
    defaultRowHeight: 60,
    manualRowResize: false,
    height: tableHeight,
    stretchH: 'last',
    minSpareRows: 0,
    minSpareCols: 0,
    rowHeaders: true,
    colHeaders: true,
    //contextMenu: contextMenu,
  });
  
  return hot;

}

// make handsontable
function updateHandsontable(hot, data, colHeaders) {

  // some preprocessing
  var colWidths = [70].concat(_.times(colHeaders.length-1, _.constant(80)));
  
  // create the chart
  hot.updateSettings({
    data: data,
    colWidths: colWidths,
    minCols: colHeaders.length,
    maxCols: colHeaders.length,
    minRows: data.length,
    maxRows: data.length,
    colHeaders: colHeaders,
    //columns: columns
  });
}