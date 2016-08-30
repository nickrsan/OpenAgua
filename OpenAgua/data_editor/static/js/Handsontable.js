// make handsontable
function handsontable(divname, data, colHeaders, tableHeight) {
  var container = document.getElementById(divname);
  var hot = new Handsontable(container, {
    data: data,
    height: tableHeight,
    minCols: colHeaders.length,
    maxCols: colHeaders.length,
    minRows: data.length,
    minSpareRows: 0,
    minSpareCols: 0,
    rowHeaders: true,
    colHeaders: colHeaders,
    contextMenu: true
  });
}