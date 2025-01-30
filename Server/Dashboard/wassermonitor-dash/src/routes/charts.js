/**
 * ECharts-based visualization utilities for creating and updating charts.
 *
 * This module provides functions to:
 * - Initialize and update bar and line charts using ECharts.
 * - Load data from APIs and integrate it into chart visualizations.
 * - Apply custom styling, themes, and interactions to charts.
 *
 * It is designed for flexible and dynamic chart generation, enabling seamless integration
 * with external data sources and user interactions.
 *
 * @module charts
 */

import * as echarts from 'echarts';
import { loadFillDataFromAPI, loadTimeDataFromAPI } from './api';

let firstLineColor;
let plotBackGround;



/**
 * Re-initializes an EChart instance.
 *
 * This function disposes of an existing EChart instance, if present, and creates a new one
 * with the specified theme and container.
 *
 * @function reInitEchart
 * @param {string} name - The name of the chart instance.
 * @param {HTMLElement} divName - The DOM element to initialize the chart in.
 * @param {Object} charts - A dictionary of existing chart instances.
 * @param {string} plotTheme - The theme to apply to the chart.
 * @returns {Object} - The newly created EChart instance.
 */

function reInitEchart(name, divName, charts, plotTheme, plotThemeDark) {

    const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = isDarkMode ? plotThemeDark : plotTheme;
    firstLineColor = isDarkMode ? 'lightblue' : '#3F83F8';
    plotBackGround = isDarkMode ? '#1F2937':'#FDFDEA'
    // MAYBE DELETABLE
    console.log("reinit charts with theme:", theme);

    console.log(charts)

    if (name in charts && charts[name]) {
        //console.log("reinit: ", name);
        charts[name].clear();
    } else {
        const c = echarts.init(divName,theme);
        charts[name] = c
    }



    if (!window.echartsResizeListenerAdded) {
        window.echartsResizeListenerAdded = true; // Markierung setzen
        window.addEventListener("resize", () => {
            console.log("Window resized – resizing all charts");
            Object.values(charts).forEach(chart => {
                if (chart) {
                    chart.resize();
                }
            });
        });

        // Direkt nach der Initialisierung einmal `resize` triggern
        setTimeout(() => {
            console.log("Trigger initial resize");
            Object.values(charts).forEach(chart => {
                if (chart) {
                    chart.resize();
                }
            });
        }, 200);
    }

    return charts[name]
}

/**
 * Retrieves a linear gradient color for chart items.
 *
 * The function looks up a color gradient configuration by name and creates an ECharts linear gradient.
 * If no gradient is found, a default color is returned.
 *
 * @function getLinearGradient
 * @param {string} colorString - The name of the color gradient to retrieve.
 * @param {Object} cConfig - The chart configuration object containing color gradients.
 * @returns {string|Object} - The gradient object or a default color if not found.
 */
function getLinearGradient(colorString, cConfig) {
    const gradient = cConfig['colors'][colorString];
    if(gradient) {
        return new echarts.graphic.LinearGradient(0, 0, 0, 1, gradient);
    }
    return "blue";
}

/**
 * Loads and initializes the fill chart.
 *
 * This function fetches chart data from an API, initializes the fill chart,
 * and updates its visualization.
 *
 * @async
 * @function loadFillChart
 * @param {HTMLElement} chartDiv - The DOM element to render the chart in.
 * @param {Object} charts - A dictionary of existing chart instances.
 * @param {Object} chartConfig - The configuration object for the chart.
 * @param {string} mpName - The name of the measurement point.
 * @returns {Promise<void>}
 */
export async function loadFillChart(chartDiv, charts, chartConfig, mpName) {
    const chartData = await loadFillDataFromAPI(chartConfig['APIUrl'], mpName);
    const chartObj = reInitEchart('fillChart', chartDiv, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]);
    //console.log("chartData:", chartData);
    updateFillChart(chartObj, chartData, chartConfig, mpName);
}

/**
 * Updates the fill chart with new data.
 *
 * Configures and updates the chart visualization using the provided data and settings.
 *
 * @async
 * @function updateFillChart
 * @param {Object} chart - The EChart instance to update.
 * @param {Object} chartData - The data object containing chart values and thresholds.
 * @param {Object} cConfig - The configuration object for the chart.
 * @param {string} mpName - The name of the measurement point.
 * @returns {Promise<void>}
 */
export async function updateFillChart(chart, chartData, cConfig, mpName) {
    const sensorIDs = chartData.sensor_name;
    const values = chartData.value;
    const colors = chartData.color;
    //console.log(colors)
    const chartCols = colors.map(item => getLinearGradient(item,cConfig));
    //console.log(chartCols)
    const maxVal = chartData.max_val;
    const tankHeight= chartData.tank_height;
    const thWarn = chartData.warn;
    const thAlarm = chartData.alarm;
    //console.log(chart)

    //console.log("chart:" ,chart)
    const chartOptions = {
          /*title: {
            text: mpName,
            //subtext: 'bla',
            left: 'center',
          },*/
          backgroundColor:plotBackGround,
          xAxis: {
            data: sensorIDs,
            axisLabel: {
              inside: true,
              color: '#fff'
            },
            axisTick: {
              show: false
            },
            axisLine: {
              show: false
            },
            z: 9
          },
          yAxis: {
            axisLine: {
              show: false
            },
            axisTick: {
              show: false
            },
            axisLabel: {
              color: '#888'
            },
            type: 'value',
            max: 160,
            min: 0,
          },
          dataZoom: [
            {
              type: 'inside',
            }
          ],
          series: [
            {
              type: 'bar',
              showBackground: false,
              itemStyle: {
                color:  (params) => {
                  return chartCols[params.dataIndex % chartCols.length];
                }
              },

              data: values,
              barWidth: '95%',
            },

            {
              name: 'Warn',
              type: 'bar',
              showBackground: false,
              itemStyle: {
                color:  'rgba(0,0,0,0)',
                borderColor: 'orange',
                borderWidth: 1,
                borderType: 'dashed',
              },
              data: thWarn,
              barWidth: '95%',
              barGap: '-100%',
            },
            {
              name: 'Alarm',
              type: 'bar',
              showBackground: false,
              itemStyle: {
                color:  'rgba(0,0,0,0)',
                borderColor: 'red',
                borderWidth: 1,
                borderType: 'dashed',
              },

              data: thAlarm,
              barWidth: '95%',
              barGap: '-100%',
            },
            ,
            {
              name: 'Max',
              type: 'bar',
              showBackground: false,
              itemStyle: {
                color:  'rgba(0,0,0,0)',
                borderColor: 'lightblue',
                borderWidth: 1,
                borderType: 'dashed',
              },

              data: maxVal,
              barWidth: '95%',
              barGap: '-100%',
            },

            {
              name: 'Tank Height',
              type: 'bar',
              showBackground: false,
              itemStyle: {
                color:  'rgba(0,0,0,0)',
                borderColor: 'rgba(0,191,255,255)',
                borderWidth: 1,
                borderStyle: 'solid',
              },

              data: tankHeight,
              barWidth: '95%',
              barGap: '-100%',
            },

          ]
    };
    chart.setOption(chartOptions,{ notMerge: true, replaceMerge: ['series'] });
}

/**
 * Loads and initializes the time and derivative charts.
 *
 * Fetches data from an API, initializes the charts, and synchronizes interactions between them.
 *
 * @async
 * @function loadTimeChart
 * @param {Array<HTMLElement>} chartDivs - An array of DOM elements for the charts.
 * @param {Object} charts - A dictionary of existing chart instances.
 * @param {Object} chartConfig - The configuration object for the chart.
 * @param {string} dtFrom - Start date for the data range.
 * @param {string} dtUntil - End date for the data range.
 * @param {string} mpName - The name of the measurement point.
 * @returns {Promise<void>}
 */
export async function loadTimeChart(chartDivs, charts, chartConfig, dtFrom, dtUntil, mpName) {
    //console.log ('chartConfig: ', chartConfig );
    //console.log ('chartConfig: ', mpName );
    const loadedApiTimeData = await loadTimeDataFromAPI(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
    //console.log ('time data: ', loadedApiTimeData );

    const chartInstances  =  {
        'timeChart': reInitEchart('timeChart', chartDivs[1].divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
        'derivChart': reInitEchart('derivChart', chartDivs[2].divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
    };
    if (loadedApiTimeData) {
        await updateTimeChart(chartInstances['timeChart'], loadedApiTimeData, 'values', 'value');
        await updateTimeChart(chartInstances['derivChart'], loadedApiTimeData, 'deriv', 'deriv');

        chartInstances['timeChart'].on('dataZoom', function (event) {
            if (event.dataZoomId === '\u0000series\u00000\u00000') {
                chartInstances['derivChart'].dispatchAction({
                    type: 'dataZoom',
                    dataZoomId: event.dataZoomId,
                    gridIndex: 0,
                    xAxisIndex: 0, // Synchronisiere x-Achse 0
                    xAxisIndex: 0,
                    start: event.start,
                    end: event.end
                });

            } else if (event.dataZoomId === '\u0000series\u00002\u00000') {
                chartInstances['derivChart'].dispatchAction({
                    type: 'dataZoom',
                    dataZoomId: event.dataZoomId,
                    gridIndex:1,
                    xAxisIndex: 1, // Synchronisiere x-Achse 1
                    xAxisIndex: 0,
                    start: event.start,
                    end: event.end
                });
            }
        });
    } else {
        //console.log("Empty Graphes!")
        const tooltipConfigs = [];
        const gridConfigs = [];
        const xAxisConfigs = [];
        const yAxisConfigs = [];
        const seriesConfigs = [];
        const dataZoomConfigs = [];
        const titleConfigs = [];
        const toolboxConfigs = [];
        const chartOptions = {
            grid: gridConfigs,
            //backgroundColor:'#1F2937',
            backgroundColor:plotBackGround,
            title: titleConfigs,
            xAxis: xAxisConfigs,
            yAxis: yAxisConfigs,
            series: seriesConfigs,
            dataZoom: dataZoomConfigs,
            tooltip: tooltipConfigs,
            legend:{top:'4%'},
            toolbox: {
              show: true,
              orient: 'horizontal',
              feature: {
                dataZoom: {
                  yAxisIndex: 'none'
                },
                dataView: { readOnly: false },
                //magicType: { type: ['line', 'bar'] },
                restore: {},
                saveAsImage: {}
              }
            }
        };
        chartInstances['timeChart'].clear();
        chartInstances['derivChart'].clear();
        chartInstances['timeChart'].setOption(chartOptions);
        chartInstances['derivChart'].setOption(chartOptions);
    };
}



/**
 * Updates a time chart with new data.
 *
 * Configures and updates the time chart visualization with series and axes settings.
 *
 * @async
 * @function updateTimeChart
 * @param {Object} chartObj - The EChart instance to update.
 * @param {Array<Object>} loadedApiTimeData - The data object containing chart values.
 * @param {string} dDict - The key for accessing data within the loaded API data.
 * @param {string} bPrintLines - Determines which series to render (e.g., value or deriv).
 * @returns {Promise<void>}
 */
export async function updateTimeChart(chartObj, loadedApiTimeData, dDict, bPrintLines) {
    const tooltipConfigs = [];
    const gridConfigs = [];
    const xAxisConfigs = [];
    const yAxisConfigs = [];
    const seriesConfigs = [];
    const dataZoomConfigs = [];
    const titleConfigs = [];
    const toolboxConfigs = [];
    const countOfSubplots = loadedApiTimeData.length;
    let legendConfig;
    let top;
    if (bPrintLines == 'value' ) {
        legendConfig = {top:'0%'};
        top = '5%';
    } else {
        legendConfig = {top:'0%'};
        top = '7%';
    }
    //console.log ('legenConfig', legendConfig)

    //console.log('Counts of plots:', countOfSubplots);

    loadedApiTimeData.forEach((chart, index) => {
        titleConfigs.push({
           text: chart.sensorID,
           left: `${92.0/countOfSubplots/2 + index * (100.0/countOfSubplots)}%`,
           top:top,
           textStyle: {
            fontSize:14,
            fontWeight: 'bold',
           },
           gridIndex: index,
        });
        toolboxConfigs.push({
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                restore: {},
                saveAsImage: {}
                }
            },
        });
        gridConfigs.push({
           left: `${5+ index * (100.0/countOfSubplots)}%`,
           //left: '5%',
           right: '2%',
           top: top,
           bottom: '35%',
           height: '65%',
           width: `${86.0/countOfSubplots}%`,
           //width: '25%',
        });
        xAxisConfigs.push({
            type: 'time',
            boundaryGap: false,
            axisLine: { onZero: false },
            axisLabel: { formatter: '{yyyy}-{MM}-{dd} {HH}:{mm}', rotate: 45 },
            gridIndex: index,
        });
        if (bPrintLines == 'value') {
            yAxisConfigs.push({
               type: 'value',
               min: 0,
               max: chart.y_max,
               gridIndex: index,
            });
        } else if (bPrintLines == 'deriv') {
            yAxisConfigs.push({
               type: 'value',
               min: chart.deriv_y_min,
               max: chart.deriv_y_max,
               gridIndex: index,
               // logBase:1024,
            });
        }
        if (bPrintLines == 'value') {
            tooltipConfigs.push(
                {
                    trigger: 'axis',
                    formatter: function(params) {
                        let timestamp = params[0].data[0];
                        let formattedDate = new Date(timestamp).toLocaleString();
                        let tooltipContent = '';
                        tooltipContent += `${formattedDate}<br>Value: ${params[0].data[1]} cm<br>`;
                        return tooltipContent;
                    }
                }
            );
            seriesConfigs.push(
              {
                name: chart.name,
                type: 'line',
                smooth: true,
                data: chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value]),
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                lineStyle:{
                    color:firstLineColor,
                    width:3
                },
              },

              {
                name: 'Max',
                type: 'line',
                smooth: true,
                data: chart.values.map(item => [new Date(item.timestamp).getTime(), item.max_val]),
                xAxisIndex: index,
                yAxisIndex: index,
                lineStyle:{
                    color:'lightblue',
                    type:'dashed',
                    width:1
                },
                symbol: 'none',

              },
              {
                name: 'Warn',
                type: 'line',
                smooth: true,
                data: chart.values.map(item => [new Date(item.timestamp).getTime(), item.warn]),
                xAxisIndex: index,
                yAxisIndex: index,
                lineStyle:{
                    color:'orange',
                    type:'dashed',
                    width:1
                },
                symbol: 'none',

              },
              {
                name: 'Alarm',
                type: 'line',
                smooth: true,
                data: chart.values.map(item => [new Date(item.timestamp).getTime(), item.alarm]),
                xAxisIndex: index,
                yAxisIndex: index,
                lineStyle:{
                    color:'red',
                    type:'dashed',
                    width:1,
                },
                symbol: 'none',

              },
            );
        } else {
            seriesConfigs.push(
              {
                name: 'Derivation [cm/h]',
                type: 'line',
                smooth: true,
                data: chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value]),
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                silent:true,
                lineStyle:{
                    color:'grey',
                    width:1
                },
              },
              {
                name: 'Avg of 10 of Derivation [cm/h]',
                type: 'line',
                smooth: true,
                data: chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value_10]),
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                lineStyle:{
                    color:'orange',
                    width:3
                },
              },
              {
                name: 'Positive Peaks',
                type: 'scatter',
                data: chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.peaks_pos]),
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'triangle',
                symbolSize: 15,
                symbolColor: 'red',
                //symbol: 'none',

              },
              {
                name: 'Negative Peaks',
                type: 'scatter',
                data: chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.peaks_neg]),
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'triangle',
                symbolSize: 15,
                symbolColor: 'red',
                //symbol: 'none',

              },
            );
            tooltipConfigs.push(
                {
                    trigger: 'axis',
                    formatter: function(params) {
                        let tooltipContent = '';
                        tooltipContent += `Derivation: <br>${params[0].data[1]} cm/h<br>`;
                        return tooltipContent;
                    }
                }
            );
        }
        if (bPrintLines == 'value') {
            dataZoomConfigs.push({
              type: 'slider',
              show: true,
              xAxisIndex: index,
              start: 0,
              end: 100,
              height: '8%',
              bottom: '3%',
            });
            dataZoomConfigs.push({
              type: 'inside',
              yAxisIndex:index,
              start: 0,
              end: 100,
              show:false
            });
        } else {
            dataZoomConfigs.push({
              type: 'slider',
              show: false,
              xAxisIndex: index
            });
            dataZoomConfigs.push({
              type: 'inside',
              yAxisIndex: index,
              start: 0,
              end: 100,
            });
        }
    });

    const chartOptions = {
      grid: gridConfigs,
      //backgroundColor:'#1F2937',
      backgroundColor:plotBackGround,
      title: titleConfigs,
      xAxis: xAxisConfigs,
      yAxis: yAxisConfigs,
      series: seriesConfigs,
      dataZoom: dataZoomConfigs,
      tooltip: tooltipConfigs,
      legend: legendConfig,
      //legend:{bottom: '12%'},
      toolbox: {
        show: true,
        orient: 'horizontal',
        feature: {
          dataZoom: {
            yAxisIndex: 'none'
          },
          dataView: { readOnly: false },
          //magicType: { type: ['line', 'bar'] },
          restore: {},
          saveAsImage: {}
        }
      }
    }

    chartObj.setOption(chartOptions,{ notMerge: true, replaceMerge: ['series'] });
}