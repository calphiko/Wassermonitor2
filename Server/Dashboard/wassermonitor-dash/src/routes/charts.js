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
function reInitEchart(name, divName, charts, plotTheme) {
        console.log(name);
        if (charts[name]) {
            echarts.dispose(charts[name]);
        }
        const c = echarts.init(divName,plotTheme);
        return c
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
    const chartObj = reInitEchart('fillChart', chartDiv, charts, chartConfig["plotTheme"]);
    console.log("chartData:", chartData);
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
    console.log(colors)
    const chartCols = colors.map(item => getLinearGradient(item,cConfig));
    console.log(chartCols)
    const maxVal = chartData.max_val;
    const thWarn = chartData.warn;
    const thAlarm = chartData.alarm;
    console.log(chart)

    console.log("chart:" ,chart)
    const chartOptions = {
          title: {
            text: mpName,
            //subtext: 'bla',
            left: 'center',
          },
          backgroundColor:'rgba(255,255,255,0)',
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
            z: 10
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
              barWidth: '90%',
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
              barWidth: '90%',
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
              barWidth: '90%',
              barGap: '-100%',
            },

            {
              name: 'Max',
              type: 'bar',
              showBackground: false,
              itemStyle: {
                color:  'rgba(0,0,0,0)',
                borderColor: 'rgba(0,191,255,255)',
                borderWidth: 1,
                borderStyle: 'solid',
              },

              data: maxVal,
              barWidth: '90%',
              barGap: '-100%',
            },

          ]
    };
    chart.setOption(chartOptions);
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
    const loadedApiTimeData = await loadTimeDataFromAPI(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
    console.log ('time data: ', dtFrom, dtUntil);

    const chartInstances  =  {
        'timeChart': reInitEchart('timeChart', chartDivs[1].divName, charts, chartConfig["plotTheme"]),
        'derivChart': reInitEchart('derivChart', chartDivs[2].divName, charts, chartConfig["plotTheme"]),
    };

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

    console.log('Counts of plots:', countOfSubplots);

    loadedApiTimeData.forEach((chart, index) => {
        titleConfigs.push({
           text: chart.sensorID,
           left: `${92.0/countOfSubplots/2 + index * (100.0/countOfSubplots)}%`,
           top:'0',
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
           top: '5%',
           bottom: '35%',
           height: '65%',
           width: `${92.0/countOfSubplots}%`,
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
            });
        }
        if (bPrintLines == 'value') {
            tooltipConfigs.push(
                {
                    trigger: 'axis',
                    formatter: function(params) {
                        let tooltipContent = '';
                        tooltipContent += `Value: ${params[0].data[1]} cm<br>`;
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
                    color:'lightblue',
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
                    color:'blue',
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
                name: chart.name,
                type: 'line',
                smooth: true,
                data: chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value]),
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                lineStyle:{
                    color:'lightblue',
                    width:3
                },
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
              height: '12%',
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
      backgroundColor:'rgba(255,255,255,0)',
      title: titleConfigs,
      xAxis: xAxisConfigs,
      yAxis: yAxisConfigs,
      series: seriesConfigs,
      dataZoom: dataZoomConfigs,
      tooltip: tooltipConfigs,
      legend:{},
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

    chartObj.setOption(chartOptions);
}