// make amchart
function amchart(title, timeseries, dateFormat, divname, log) {

    // replace empty values with null
    while(_.find(timeseries, {'value':''})){
        (_.find(timeseries, {'value':''})).value = null;
    }
  
  var chart = AmCharts.makeChart(divname, {
      "type": "serial",
      "theme": "light",
      "marginRight": 60,
      "autoMarginOffset": 40,
      "mouseWheelZoomEnabled":false,
      "dataDateFormat": dateFormat,
      "valueAxes": [{
          "id": "v1",
          "axisAlpha": 0,
          "position": "left",
          "ignoreAxisWidth":true
      }],
      "balloon": {
          "cornerRadius": 5,
          "horizontalPadding": 5,
          "verticalPadding": 5,
          //"drop": true
      },
      "graphs": [{
          "id": "g1",
          "balloon":{
            "cornerRadius": 0,
            "adjustBorderColor":false,
            "color":"#ffffff"
          },
          "bullet": "round",
          "bulletBorderAlpha": 1,
          "bulletColor": "#FFFFFF",
          "bulletSize": 5,
          "hideBulletsCount": 50,
          "lineThickness": 2,
          "title": "red line",
          "useLineColorForBulletBorder": true,
          "valueField": "value",
          "balloonText": "<span style='font-size:11px;'>[[value]]</span>"
      }],
      "chartScrollbar": {
          "graph": "g1",
          "oppositeAxis":false,
          "offset":30,
          "scrollbarHeight": 80,
          "backgroundAlpha": 0,
          "selectedBackgroundAlpha": 0.1,
          "selectedBackgroundColor": "#888888",
          "graphFillAlpha": 0,
          "graphLineAlpha": 0.8,
          "selectedGraphFillAlpha": 0,
          "selectedGraphLineAlpha": 1,
          "autoGridCount":true,
          "color":"#AAAAAA"
      },
      "chartCursor": {
          "pan": true,
          "valueLineEnabled": true,
          "valueLineBalloonEnabled": true,
          "cursorAlpha":1,
          "cursorColor":"#258cbb",
          "limitToGraph":"g1",
          "valueLineAlpha":0.5,
          "valueZoomable":true,
          "categoryBalloonDateFormat": "MMM YYYY",
          "cursorAlpha": 0.5,
          "fullWidth": true
      },
      "valueAxes":[{
        logarithmic: log,
      }],
      "valueScrollbar":{
        "oppositeAxis":false,
        "offset": 50,
        "scrollbarHeight":5
      },
      "categoryField": "date",
      "categoryAxis": {
          "parseDates": true,
          "dashLength": 1,
          "minorGridEnabled": false
      },
      "export": {
          "enabled": true
      },
      "dataProvider": timeseries,
      "precision": 2
  });

  chart.addListener("rendered", zoomChart);
  
  zoomChart();
  
  function zoomChart() {
      chart.zoomToIndexes(0, 11);
  }

}