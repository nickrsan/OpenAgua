// make handsontable
function handsontable(divname, data, colHeaders, tableHeight) {
  var container = document.getElementById(divname);
  var hot = new Handsontable(container, {
    data: data,
    colWidths:[70].concat(_.times(colHeaders.length-1, _.constant(80))),
    manualColumnResize: true,
    manualRowResize: false,
    height: tableHeight,
    stretchH: 'last',
    minCols: colHeaders.length,
    maxCols: colHeaders.length,
    minRows: data.length,
    minSpareRows: 0,
    minSpareCols: 0,
    rowHeaders: true,
    colHeaders: colHeaders,
    contextMenu: true,
    //columns: [{data: 'Month', editor: false}, {editor: 'numeric'}]
  });
}