(function() {
  var callWithJQuery;

  callWithJQuery = function(pivotModule) {
    if (typeof exports === "object" && typeof module === "object") {
      return pivotModule(require("jquery"), require("plotly"));
    } else if (typeof define === "function" && define.amd) {
      return define(["jquery", "plotly"], pivotModule);
    } else {
      return pivotModule(jQuery, Plotly);
    }
  };

  callWithJQuery(function($, Plotly) {
    var makePlotlyChart;
    makePlotlyChart = function(chartType, chartOpts) {
      if (chartOpts == null) {
        chartOpts = {};
      }
      return function(pivotData, opts) {
        var agg, attrs, base, base1, base2, base3, base4, base5, colKey, colKeys, columns, dataColumns, defaults, defaultTrace, fullAggName, groupByTitle, h, hAxisTitle, headers, hx, i, j, k, l, layout, len, len1, len2, len3, len4, m, numCharsInHAxis, numSeries, params, ref, ref1, ref2, ref3, renderArea, result, rotationAngle, row, rowHeader, rowKey, rowKeys, s, scatterData, series, stackedArea, title, titleText, trace, traces, traceName, vAxisTitle, val, vals, x, xs, y;
        defaults = {
          localeStrings: {
            vs: "vs",
            by: "by"
          },
          plotly: {}
        };
        
        layout = {}
        
        switch(chartType) {
          case 'line':
            defaultTrace = {
              type: 'scatter'          
            };
            break;
          case 'bar':
            defaultTrace = {
              type: 'bar'
            }
            if (chartOpts.stacked) {
              layout.barmode = 'stack'
            } else {
              layout.barmode = 'group'
            }
            break;
          case 'area':
            defaultTrace = {
              fill: 'tonexty'
            };
            if (chartOpts.stacked && !stackedArea) {
              stackedArea = function(traces) {
                  for(var i=1; i<traces.length; i++) {
                      for(var j=0; j<(Math.min(traces[i]['y'].length, traces[i-1]['y'].length)); j++) {
                          traces[i]['y'][j] += traces[i-1]['y'][j];
                      }
                  }
                  return traces;
              };
            }
            break;
          default:
            defaultTrace = {
              type: 'scatter'          
            };
            break;
        }        
        
        opts = $.extend(true, defaults, opts);
        if ((base = opts.plotly).width == null) {
          base.width = window.innerWidth / 1.4;
        }
        if ((base1 = opts.plotly).height == null) {
          base1.height = window.innerHeight / 1.4 - 50;
        }
        rowKeys = pivotData.getRowKeys();
        if (rowKeys.length === 0) {
          rowKeys.push([]);
        }
        colKeys = pivotData.getColKeys();
        if (colKeys.length === 0) {
          colKeys.push([]);
        }

        headers = (function() {
          var i, len, results;
          results = [];
          for (i = 0, len = rowKeys.length; i < len; i++) {
            h = rowKeys[i];
            results.push(h.join("-"));
          }
          return results;
        })();
        headers.unshift("");
        fullAggName = pivotData.aggregatorName;
        if (pivotData.valAttrs.length) {
          fullAggName += "(" + (pivotData.valAttrs.join(", ")) + ")";
        }
        //numCharsInHAxis = 0;
        
        //scatter chart
        if (chartOpts.type === "scatter") {
          scatterData = {
            x: {},
            y: {},
            t: {}
          };
          attrs = pivotData.rowAttrs.concat(pivotData.colAttrs);
          vAxisTitle = (ref = attrs[0]) != null ? ref : "";
          hAxisTitle = (ref1 = attrs[1]) != null ? ref1 : "";
          groupByTitle = attrs.slice(2).join("-");
          titleText = vAxisTitle;
          if (hAxisTitle !== "") {
            titleText += " " + opts.localeStrings.vs + " " + hAxisTitle;
          }
          if (groupByTitle !== "") {
            titleText += " " + opts.localeStrings.by + " " + groupByTitle;
          }
          for (i = 0, len = rowKeys.length; i < len; i++) {
            rowKey = rowKeys[i];
            for (j = 0, len1 = colKeys.length; j < len1; j++) {
              colKey = colKeys[j];
              agg = pivotData.getAggregator(rowKey, colKey);
              if (agg.value() != null) {
                vals = rowKey.concat(colKey);
                series = vals.slice(2).join("-");
                if (series === "") {
                  series = "series";
                }
                if ((base3 = scatterData.x)[series] == null) {
                  base3[series] = [];
                }
                if ((base4 = scatterData.y)[series] == null) {
                  base4[series] = [];
                }
                if ((base5 = scatterData.t)[series] == null) {
                  base5[series] = [];
                }
                scatterData.y[series].push((ref2 = vals[0]) != null ? ref2 : 0);
                scatterData.x[series].push((ref3 = vals[1]) != null ? ref3 : 0);
                scatterData.t[series].push(agg.format(agg.value()));
              }
            }
          }
          
        //non-scatter chart
        } else {
          //numCharsInHAxis = 0;
          for (k = 0, len2 = headers.length; k < len2; k++) {
            hx = headers[k];
            //numCharsInHAxis += hx.length;
          }
          traces = [];
          for (j = 0, len1 = rowKeys.length; j < len1; j++) {
            rowKey = rowKeys[j];
            traceName = rowKey.join("-");
            x = [];
            y = [];
            for (i = 0, len = colKeys.length; i < len; i++) {
              colKey = colKeys[i];
              x.push(colKey.join("-"));
              //numCharsInHAxis += x[0].length;

              agg = pivotData.getAggregator(rowKey, colKey);
              if (agg.value() != null) {
                val = agg.value();
                if ($.isNumeric(val)) {
                  if (val < 1) {
                    y.push(parseFloat(val.toPrecision(3)));
                  } else {
                    y.push(parseFloat(val.toFixed(3)));
                  }
                } else {
                  y.push(val);
                }
              } else {
                y.push(null);
              }
            }
            
            trace = $.extend(true, {}, defaultTrace, {
              x: x,
              y: y,
              name: traceName
            });
            if (chartType === 'area') {
              if (j === 0) {
                trace.fill = 'tozeroy';             
              }
            }
            
            traces.push(trace);
          }
          if (chartType === 'area' && chartOpts.stacked === true) {
            traces = stackedArea(traces);
          }
          
          vAxisTitle = pivotData.aggregatorName + (pivotData.valAttrs.length ? "(" + (pivotData.valAttrs.join(", ")) + ")" : "");
          hAxisTitle = pivotData.colAttrs.join("-");
          titleText = fullAggName;
          if (hAxisTitle !== "") {
            titleText += " " + opts.localeStrings.vs + " " + hAxisTitle;
          }
          groupByTitle = pivotData.rowAttrs.join("-");
          if (groupByTitle !== "") {
            titleText += " " + opts.localeStrings.by + " " + groupByTitle;
          }
        }
        
        //plotly-specific parameters
        title = $("<p>", {
          style: "text-align: center; font-weight: bold"
        });
        title.text(titleText);
        layout = $.extend(true, layout, {
          title: titleText,     
          width: base.width,
          height: base1.height
        });
        
        //$.extend(true, layout, opts.plotly);
        
        //scatter plot
        if (chartOpts.type === "scatter") {
        } else {
          //numSeries = 0;
          //data = []
          //for (s in scatterData.x) {
            //numSeries += 1;
            //trace = {
              //x: scatterData.x[s],
              //y: scatterData.t[s],
              //mode: 'markers',
              //type: 'scatter'
            //}
            //data.push(trace)
          //}
          //if (numSeries === 1) {
            //params.legend = {
              //show: false
            //};
          //}
          
        //if (chartOpts.stacked != null) {
          //groups = [
            //(function() {
              //var len5, n, results;
              //results = [];
              //for (n = 0, len5 = rowKeys.length; n < len5; n++) {
                //x = rowKeys[n];
                //results.push(x.join("-"));
              //}
              //return results;
            //})()
          //];
        }

        if ($("#plot").length) {
          Plotly.purge('plot');
          result = $("#plot").empty();
        } else {
          result = $("<div>")
            .css({width: "100%", height: "100%"})
            .attr('id', 'plot')
            .appendTo($("body"));
        }
        Plotly.plot(result[0], traces, layout, {showLink: false}); // create plot here
        return result
      };
    };
    return $.pivotUtilities.plotly_renderers = {
      "Line Chart": makePlotlyChart("line"),
      "Bar Chart": makePlotlyChart("bar"),
      "Stacked Bar Chart": makePlotlyChart("bar", {
        stacked: true
      }),
      "Overlaid Area Chart": makePlotlyChart("area"),
      "Stacked Area Chart": makePlotlyChart("area", {
        stacked: true
      }),
      "Scatter Chart": makePlotlyChart({
        type: "scatter"
      })
    };
  });

}).call(this);

//# sourceMappingURL=c3_renderers.js.map
