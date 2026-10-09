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
import { loadFillDataFromAPI, loadMeasurementStdDevFromAPI, loadRawTimeDataFromAPI, loadTimeDataFromAPI } from './api';
import { processRawTimeSeries } from './timeProcessor';

let firstLineColor;
let plotBackGround;

const evaluationDataCache = new Map();

const SENSOR_COLOR_PALETTE = ['#f59e0b', '#f97316', '#fb7185', '#facc15', '#a78bfa', '#38bdf8', '#34d399', '#60a5fa'];

function buildEvaluationDataCacheKey(apiUrl, dtFrom, dtUntil, mpName) {
    return `${apiUrl}|${dtFrom}|${dtUntil}|${mpName}`;
}

async function loadEvaluationDataSet(chartConfig, dtFrom, dtUntil, mpName) {
    const cacheKey = buildEvaluationDataCacheKey(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
    const cachedEntry = evaluationDataCache.get(cacheKey);
    if (cachedEntry) {
        return cachedEntry;
    }

    const rawData = await loadRawTimeDataFromAPI(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
    const dataset = {
        rawData: rawData && typeof rawData === 'object' ? rawData : null,
        stdDevData: null,
    };
    evaluationDataCache.set(cacheKey, dataset);
    return dataset;
}

function getSensorColor(sensorName) {
    const value = String(sensorName ?? '').trim();
    let hash = 0;
    for (let index = 0; index < value.length; index += 1) {
        hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
    }
    return SENSOR_COLOR_PALETTE[hash % SENSOR_COLOR_PALETTE.length];
}

function padDateValue(value) {
    return String(value).padStart(2, '0');
}

function formatLocalDateTime(value) {
    const date = value instanceof Date ? value : new Date(value);
    return `${date.getFullYear()}-${padDateValue(date.getMonth() + 1)}-${padDateValue(date.getDate())} ${padDateValue(date.getHours())}:${padDateValue(date.getMinutes())}`;
}

function formatLocalizedFillDateTime(timestamp, templateLabel) {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    const template = String(templateLabel ?? '');

    if (template.includes(' um ') && template.endsWith(' Uhr')) {
        return `${padDateValue(date.getDate())}.${padDateValue(date.getMonth() + 1)}.${date.getFullYear()} um ${padDateValue(date.getHours())}:${padDateValue(date.getMinutes())} Uhr`;
    }

    if (template.includes(' at ')) {
        return `${padDateValue(date.getMonth() + 1)}-${padDateValue(date.getDate())}-${date.getFullYear()} at ${padDateValue(date.getHours())}:${padDateValue(date.getMinutes())}`;
    }

    return formatLocalDateTime(date);
}

function formatFillChartLabel(sensorName, timestamp) {
    const baseSensorName = String(sensorName ?? '').split('\n')[0];
    const timestampLabel = String(sensorName ?? '').split('\n')[1];
    if (!timestamp) {
        return baseSensorName;
    }

    return `${baseSensorName}\n${formatLocalizedFillDateTime(timestamp, timestampLabel)}`;
}

function formatPeakTooltip(params) {
    const data = Array.isArray(params?.data) ? params.data : [];
    if (data.length < 2 || typeof data[1] !== 'number' || !Number.isFinite(data[1])) {
        return '';
    }

    return `${formatLocalDateTime(data[0])}<br>${params.seriesName}: ${data[1]} cm/h`;
}



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
    const theme = plotThemeDark || plotTheme || 'dark';
    firstLineColor = '#67e8f9';
    plotBackGround = 'transparent';
    if (charts[name]) {
        //console.log("reinit: ", name);
        echarts.dispose(charts[name]);
    }
    const c = echarts.init(divName, theme, { height: 600, renderer: 'canvas', useDirtyRect: true });
    charts[name] = c;
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
    const chartObj = reInitEchart('fillChart', chartDiv, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]);
    if (!chartData) {
        chartObj.clear();
        return;
    }
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
    const sensorTimestamps = Array.isArray(chartData.dt) ? chartData.dt : [];
    const sensorLabels = sensorIDs.map((sensorName, index) => formatFillChartLabel(sensorName, sensorTimestamps[index]));
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
          backgroundColor: plotBackGround,
          textStyle: {
            color: '#e2e8f0'
          },
          xAxis: {
            data: sensorLabels,
            axisLabel: {
              inside: true,
              color: '#cbd5e1'
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
              color: '#cbd5e1'
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
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            borderColor: 'rgba(148, 163, 184, 0.4)',
            textStyle: {
              color: '#e2e8f0'
            }
          },
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
              barWidth: '90%',
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
              barWidth: '90%',
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
 * @param {Array<{name: string, divName: HTMLElement}>} chartDivs - The chart mount descriptors.
 * @param {Object} charts - A dictionary of existing chart instances.
 * @param {Object} chartConfig - The configuration object for the chart.
 * @param {string} dtFrom - Start date for the data range.
 * @param {string} dtUntil - End date for the data range.
 * @param {string} mpName - The name of the measurement point.
 * @returns {Promise<void>}
 */
export async function loadTimeChart(chartDivs, charts, chartConfig, dtFrom, dtUntil, mpName) {
    const loadedApiTimeData = await loadTimeDataFromAPI(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
    const timeChartMount = chartDivs.find((chartDiv) => chartDiv.name === 'timeChart');
    const derivChartMount = chartDivs.find((chartDiv) => chartDiv.name === 'derivChart');

    if (!timeChartMount || !derivChartMount) {
        throw new Error('Time chart mounts are incomplete.');
    }

    const chartInstances  =  {
        'timeChart': reInitEchart('timeChart', timeChartMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
        'derivChart': reInitEchart('derivChart', derivChartMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
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
                    xAxisIndex: 0,
                    start: event.start,
                    end: event.end
                });

            } else if (event.dataZoomId === '\u0000series\u00002\u00000') {
                chartInstances['derivChart'].dispatchAction({
                    type: 'dataZoom',
                    dataZoomId: event.dataZoomId,
                    gridIndex:1,
                    xAxisIndex: 1,
                    start: event.start,
                    end: event.end
                });
            }
        });
        return true;
    }

    const gridConfigs = [];
    const xAxisConfigs = [];
    const yAxisConfigs = [];
    const seriesConfigs = [];
    const dataZoomConfigs = [];
    const titleConfigs = [];
    const chartOptions = {
        grid: gridConfigs,
        backgroundColor: plotBackGround,
        textStyle: {
          color: '#e2e8f0'
        },
        animation: false,
        animationDuration: 0,
        animationDurationUpdate: 0,
        title: titleConfigs,
        xAxis: xAxisConfigs,
        yAxis: yAxisConfigs,
        series: seriesConfigs,
        dataZoom: dataZoomConfigs,
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.94)',
          borderColor: 'rgba(148, 163, 184, 0.4)',
          textStyle: {
            color: '#e2e8f0'
          }
        },
        legend:{},
        toolbox: {
          show: true,
          orient: 'horizontal',
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            dataView: { readOnly: false },
            restore: {},
            saveAsImage: {}
          },
          iconStyle: {
            borderColor: '#cbd5e1'
          },
          emphasis: {
            iconStyle: {
              borderColor: '#67e8f9'
            }
          }
        }
    };
    chartInstances['timeChart'].clear();
    chartInstances['derivChart'].clear();
    chartInstances['timeChart'].setOption(chartOptions);
    chartInstances['derivChart'].setOption(chartOptions);
    return false;
}

/**
 * Loads evaluation charts (event detection and measurement regularity) from raw API data
 * and computes metrics in Rust/WASM in the browser.
 *
 * @async
 * @function loadEvaluationCharts
 * @param {Array<{name: string, divName: HTMLElement}>} chartDivs
 * @param {Object} charts
 * @param {Object} chartConfig
 * @param {string} dtFrom
 * @param {string} dtUntil
 * @param {string} mpName
 * @returns {Promise<void>}
 */
export async function loadEvaluationCharts(
   chartDivs,
   charts,
   chartConfig,
   dtFrom,
   dtUntil,
   mpName,
   aggregation = 'auto',
   forceReload = false,
   onPrimaryLoadingState = null,
   onStdDevLoadingState = null
) {
   if (typeof onPrimaryLoadingState === 'function') {
       onPrimaryLoadingState(true);
   }
   if (typeof onStdDevLoadingState === 'function') {
       onStdDevLoadingState(false);
   }

   const cycleDeviationMount = chartDivs.find((chartDiv) => chartDiv.name === 'cycleDeviationChart');
   const dailyCycleCountMount = chartDivs.find((chartDiv) => chartDiv.name === 'dailyCycleCountChart');
   const dailyDrainCycleCountMount = chartDivs.find((chartDiv) => chartDiv.name === 'dailyDrainCycleCountChart');
   const stdDevMount = chartDivs.find((chartDiv) => chartDiv.name === 'stdDevChart');
   const intervalHistMount = chartDivs.find((chartDiv) => chartDiv.name === 'intervalHistChart');
   if (!cycleDeviationMount || !dailyCycleCountMount || !dailyDrainCycleCountMount || !stdDevMount || !intervalHistMount) {
       if (typeof onPrimaryLoadingState === 'function') {
           onPrimaryLoadingState(false);
       }
       if (typeof onStdDevLoadingState === 'function') {
           onStdDevLoadingState(false);
       }
       throw new Error('Evaluation chart mounts are incomplete.');
   }

   const chartInstances = {
       cycleDeviationChart: reInitEchart('cycleDeviationChart', cycleDeviationMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
       dailyCycleCountChart: reInitEchart('dailyCycleCountChart', dailyCycleCountMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
       dailyDrainCycleCountChart: reInitEchart('dailyDrainCycleCountChart', dailyDrainCycleCountMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
       stdDevChart: reInitEchart('stdDevChart', stdDevMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
       intervalHistChart: reInitEchart('intervalHistChart', intervalHistMount.divName, charts, chartConfig["plotTheme"], chartConfig["plotThemeDark"]),
   };

   const cacheKey = buildEvaluationDataCacheKey(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
   if (forceReload) {
       evaluationDataCache.delete(cacheKey);
   }

   const parseInputDate = (value) => {
       const date = new Date(value);
       if (!Number.isFinite(date.getTime())) {
           return null;
       }
       return date;
   };

   const toBucketStart = (dateValue, mode) => {
       const date = new Date(dateValue);
       if (mode === 'week') {
           const start = new Date(date);
           const dayNumber = start.getDay();
           const diff = (dayNumber + 6) % 7;
           start.setDate(start.getDate() - diff);
           start.setHours(0, 0, 0, 0);
           return start;
       }
       if (mode === 'month') {
           const start = new Date(date);
           start.setDate(1);
           start.setHours(0, 0, 0, 0);
           return start;
       }
       const start = new Date(date);
       start.setHours(0, 0, 0, 0);
       return start;
   };

   const toBucketEnd = (dateValue, mode) => {
       const date = new Date(dateValue);
       if (mode === 'week') {
           const end = new Date(date);
           end.setDate(end.getDate() + 6);
           end.setHours(23, 59, 59, 999);
           return end;
       }
       if (mode === 'month') {
           const end = new Date(date);
           end.setMonth(end.getMonth() + 1, 0);
           end.setHours(23, 59, 59, 999);
           return end;
       }
       const end = new Date(date);
       end.setHours(23, 59, 59, 999);
       return end;
   };

   const rangeStart = parseInputDate(dtFrom);
   const rangeEnd = parseInputDate(dtUntil);
   if (!rangeStart || !rangeEnd || rangeStart > rangeEnd) {
       chartInstances.cycleDeviationChart.clear();
       chartInstances.dailyCycleCountChart.clear();
       chartInstances.dailyDrainCycleCountChart.clear();
       chartInstances.stdDevChart.clear();
       chartInstances.intervalHistChart.clear();
       return 'day';
   }

   const rangeMs = rangeEnd.getTime() - rangeStart.getTime();
   const rangeDays = rangeMs / (1000 * 60 * 60 * 24);
   const autoAggregation = rangeDays < 14
       ? 'day'
       : rangeDays < 60
           ? 'week'
           : 'month';
   const isManualAggregation = aggregation === 'day' || aggregation === 'week' || aggregation === 'month';
   const effectiveAggregation = isManualAggregation ? aggregation : autoAggregation;
   const bucketStarts = [];
   let cursor = toBucketStart(new Date(rangeStart), effectiveAggregation);
   while (cursor <= rangeEnd) {
       bucketStarts.push(new Date(cursor));
       if (effectiveAggregation === 'week') {
           cursor.setDate(cursor.getDate() + 7);
       } else if (effectiveAggregation === 'month') {
           cursor.setMonth(cursor.getMonth() + 1);
       } else {
           cursor.setDate(cursor.getDate() + 1);
       }
   }
   const dataset = await loadEvaluationDataSet(chartConfig, dtFrom, dtUntil, mpName);
   const rawData = dataset?.rawData;
   let stdDevData = dataset?.stdDevData ?? null;
   let stdDevPromise = null;
   const sensorGroups = Array.isArray(rawData?.[mpName]) ? rawData[mpName] : [];
   if (sensorGroups.length === 0) {
       if (typeof onPrimaryLoadingState === 'function') {
           onPrimaryLoadingState(false);
       }
       if (typeof onStdDevLoadingState === 'function') {
           onStdDevLoadingState(false);
       }
       chartInstances.cycleDeviationChart.clear();
       chartInstances.dailyCycleCountChart.clear();
       chartInstances.dailyDrainCycleCountChart.clear();
       chartInstances.stdDevChart.clear();
       chartInstances.intervalHistChart.clear();
       return false;
   }

   if (!stdDevData) {
       stdDevPromise = loadMeasurementStdDevFromAPI(chartConfig['APIUrl'], dtFrom, dtUntil, mpName);
       if (typeof onStdDevLoadingState === 'function') {
           onStdDevLoadingState(true);
       }
   }

   const sensorStates = sensorGroups.map((sensor) => {
       const rows = Array.isArray(sensor?.rows) ? [...sensor.rows] : [];
       rows.sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
       const rowTimestamps = rows.map((row) => new Date(row.timestamp).getTime());
       return {
           sensorMeta: { ...sensor, rows: undefined },
           rows,
           rowTimestamps,
           nextRowIndex: 0,
           cumulativeRows: [],
       };
   });

   const nextPaint = () => new Promise((resolve) => {
       if (typeof requestAnimationFrame === 'function') {
           requestAnimationFrame(() => resolve());
           return;
       }
       setTimeout(resolve, 0);
   });

   let bucketsWithData = 0;
   let renderedFirstBucket = false;

   for (const bucketStart of bucketStarts) {
       const bucketEnd = toBucketEnd(bucketStart, effectiveAggregation);
       const clampedBucketEnd = new Date(Math.min(bucketEnd.getTime(), rangeEnd.getTime()));
       if (bucketStart > clampedBucketEnd) {
           continue;
       }

       const bucketEndTs = clampedBucketEnd.getTime();
       sensorStates.forEach((state) => {
           while (state.nextRowIndex < state.rows.length) {
               const rowTs = state.rowTimestamps[state.nextRowIndex];
               if (!Number.isFinite(rowTs) || rowTs > bucketEndTs) {
                   break;
               }
               state.cumulativeRows.push(state.rows[state.nextRowIndex]);
               state.nextRowIndex += 1;
           }
       });

       const partialSensors = sensorStates.map((state) => ({
           ...state.sensorMeta,
           rows: state.cumulativeRows,
       }));
       const partialRowCount = partialSensors.reduce((sum, sensor) => sum + (Array.isArray(sensor?.rows) ? sensor.rows.length : 0), 0);
       if (partialRowCount === 0) {
           continue;
       }
       bucketsWithData += 1;

       const partialProcessed = await processRawTimeSeries({ [mpName]: partialSensors }, mpName);
       if (!Array.isArray(partialProcessed) || partialProcessed.length === 0) {
           continue;
       }

       await updateCycleDeviationChart(chartInstances.cycleDeviationChart, partialProcessed);
       await updateDailyCycleCountChart(chartInstances.dailyCycleCountChart, partialProcessed, effectiveAggregation, 'fill');
       await updateDailyCycleCountChart(chartInstances.dailyDrainCycleCountChart, partialProcessed, effectiveAggregation, 'drain');
       await updateIntervalHistogramChart(chartInstances.intervalHistChart, partialProcessed);

       if (!renderedFirstBucket && typeof onPrimaryLoadingState === 'function') {
           onPrimaryLoadingState(false);
           renderedFirstBucket = true;
       }

       await nextPaint();
   }

   if (bucketStarts.length === 0 || bucketsWithData === 0) {
       if (typeof onPrimaryLoadingState === 'function') {
           onPrimaryLoadingState(false);
       }
       if (typeof onStdDevLoadingState === 'function') {
           onStdDevLoadingState(false);
       }
       chartInstances.cycleDeviationChart.clear();
       chartInstances.dailyCycleCountChart.clear();
       chartInstances.dailyDrainCycleCountChart.clear();
       chartInstances.stdDevChart.clear();
       chartInstances.intervalHistChart.clear();
       return false;
   }

   if (!renderedFirstBucket && typeof onPrimaryLoadingState === 'function') {
       onPrimaryLoadingState(false);
   }

   if (!stdDevData && stdDevPromise) {
       stdDevData = await stdDevPromise;
       const cachedEntry = evaluationDataCache.get(cacheKey);
       if (cachedEntry) {
           cachedEntry.stdDevData = stdDevData ?? null;
           evaluationDataCache.set(cacheKey, cachedEntry);
       }
   }

   if (stdDevData) {
       if (typeof onStdDevLoadingState === 'function') {
           onStdDevLoadingState(true);
       }
       await updateStdDevChart(chartInstances.stdDevChart, stdDevData, mpName, effectiveAggregation);
       chartInstances.stdDevChart.resize();
       if (typeof onStdDevLoadingState === 'function') {
           onStdDevLoadingState(false);
       }
   }

   return true;
}

function createSharedTimeAxis(index) {
   return {
       type: 'time',
       boundaryGap: false,
       axisLine: { onZero: false, lineStyle: { color: '#94a3b8' } },
       axisLabel: {
           formatter: (value) => formatLocalDateTime(value),
           rotate: 45,
           color: '#cbd5e1'
       },
       axisPointer: {
           label: {
               formatter: ({ value }) => formatLocalDateTime(value),
               color: '#e2e8f0',
               backgroundColor: 'rgba(15, 23, 42, 0.95)'
           }
       },
       splitLine: {
           lineStyle: { color: 'rgba(148, 163, 184, 0.18)' }
       },
       gridIndex: index
   };
}

function createSharedChartChrome(chartOptions) {
   return {
       ...chartOptions,
       backgroundColor: plotBackGround,
       textStyle: {
           color: '#e2e8f0'
       },
       animation: false,
       animationDuration: 0,
       animationDurationUpdate: 0,
       toolbox: {
           show: true,
           orient: 'horizontal',
           feature: {
               dataZoom: {
                   yAxisIndex: 'none'
               },
               dataView: { readOnly: false },
               restore: {},
               saveAsImage: {}
           },
           iconStyle: {
               borderColor: '#cbd5e1'
           },
           emphasis: {
               iconStyle: {
                   borderColor: '#67e8f9'
               }
           }
       }
   };
}

async function updateCycleDeviationChart(chartObj, processedData) {
   const gridConfigs = [];
   const xAxisConfigs = [];
   const yAxisConfigs = [];
    const seriesConfigs = [];
    const dataZoomConfigs = [];
    const titleConfigs = [];
    const tooltipConfigs = [];
    const countOfSubplots = processedData.length;

    processedData.forEach((chart, index) => {
        const cycleData = chart?.evaluation?.cycle_deviation || {};
        const fillMean = Number(cycleData.fill_mean_slope_abs || 0).toFixed(2);
        const drainMean = Number(cycleData.drain_mean_slope_abs || 0).toFixed(2);
        const cycles = Array.isArray(cycleData.cycles) ? cycleData.cycles : [];
        const levelSeries = Array.isArray(chart.values)
            ? chart.values.map((point) => [new Date(point.timestamp).getTime(), point.value])
            : [];
        const levelByTimestamp = new Map(levelSeries.map((point) => [point[0], point[1]]));
        const fillCycles = cycles
            .filter((cycle) => cycle.cycle_type === 'fill')
            .map((cycle) => {
                const timestamp = new Date(cycle.timestamp).getTime();
                const level = levelByTimestamp.get(timestamp);
                if (typeof level !== 'number') {
                    return null;
                }
                return [timestamp, level, cycle.mean_slope_abs, cycle.duration_min];
            })
            .filter(Boolean);
        const drainCycles = cycles
            .filter((cycle) => cycle.cycle_type === 'drain')
            .map((cycle) => {
                const timestamp = new Date(cycle.timestamp).getTime();
                const level = levelByTimestamp.get(timestamp);
                if (typeof level !== 'number') {
                    return null;
                }
                return [timestamp, level, cycle.mean_slope_abs, cycle.duration_min];
            })
            .filter(Boolean);
        const fillAreas = cycles
            .filter((cycle) => cycle.cycle_type === 'fill')
            .map((cycle) => {
                const mid = new Date(cycle.timestamp).getTime();
                const halfDurationMs = Math.max(0, Number(cycle.duration_min || 0)) * 30 * 1000;
                return [{ xAxis: mid - halfDurationMs }, { xAxis: mid + halfDurationMs }];
            });
        const drainAreas = cycles
            .filter((cycle) => cycle.cycle_type === 'drain')
            .map((cycle) => {
                const mid = new Date(cycle.timestamp).getTime();
                const halfDurationMs = Math.max(0, Number(cycle.duration_min || 0)) * 30 * 1000;
                return [{ xAxis: mid - halfDurationMs }, { xAxis: mid + halfDurationMs }];
            });

        titleConfigs.push({
            text: `${chart.sensorID} | Ø ↑: ${fillMean} cm/h | Ø ↓: ${drainMean} cm/h`,
            left: `${(index + 0.5) * (100.0 / countOfSubplots)}%`,
            top: '7%',
            textAlign: 'center',
            textStyle: {
                fontSize: 14,
                fontWeight: 'bold',
                color: '#e2e8f0'
            },
            gridIndex: index
        });

        gridConfigs.push({
            left: `${5 + index * (100.0 / countOfSubplots)}%`,
            right: '2%',
            top: '10%',
            bottom: '35%',
            height: '65%',
            width: `${86.0 / countOfSubplots}%`
        });

        xAxisConfigs.push(createSharedTimeAxis(index));

        yAxisConfigs.push({
            type: 'value',
            min: 0,
            max: Number.isFinite(chart?.y_max) ? chart.y_max : undefined,
            name: 'Füllstand [cm]',
            nameLocation: 'middle',
            nameGap: 45,
            gridIndex: index,
            axisLabel: {
                color: '#cbd5e1'
            },
            axisLine: {
                lineStyle: { color: '#94a3b8' }
            },
            splitLine: {
                lineStyle: { color: 'rgba(148, 163, 184, 0.18)' }
            }
        });

        seriesConfigs.push({
            name: 'Füllstand',
            type: 'line',
            smooth: true,
            data: levelSeries,
            xAxisIndex: index,
            yAxisIndex: index,
            animation: false,
            symbol: 'none',
            sampling: 'lttb',
            progressive: 2000,
            progressiveThreshold: 3000,
            lineStyle: {
                color: '#cbd5e1',
                width: 2
            },
        });

        seriesConfigs.push({
            name: 'Befüll-Phase',
            type: 'line',
            data: [],
            xAxisIndex: index,
            yAxisIndex: index,
            showSymbol: false,
            lineStyle: { opacity: 0 },
            markArea: {
                silent: true,
                itemStyle: {
                    color: 'rgba(34, 211, 238, 0.10)'
                },
                data: fillAreas
            }
        });

        seriesConfigs.push({
            name: 'Ablauf-Phase',
            type: 'line',
            data: [],
            xAxisIndex: index,
            yAxisIndex: index,
            showSymbol: false,
            lineStyle: { opacity: 0 },
            markArea: {
                silent: true,
                itemStyle: {
                    color: 'rgba(248, 113, 113, 0.10)'
                },
                data: drainAreas
            }
        });

        dataZoomConfigs.push({
            type: 'slider',
            show: true,
            xAxisIndex: index,
            start: 0,
            end: 100,
            height: '8%',
            bottom: '3%'
        });
        dataZoomConfigs.push({
            type: 'inside',
            yAxisIndex: index,
            start: 0,
            end: 100
        });
    });

    const chartOptions = createSharedChartChrome({
        grid: gridConfigs,
        title: titleConfigs,
        xAxis: xAxisConfigs,
        yAxis: yAxisConfigs,
        series: seriesConfigs,
        dataZoom: dataZoomConfigs,
        tooltip: {
            trigger: 'axis',
            formatter: (params) => {
                const tooltipParams = Array.isArray(params) ? params : [params];
                const point = tooltipParams.find((param) => Array.isArray(param?.data) && param.data.length > 1);
                if (!point || !Array.isArray(point.data)) {
                    return '';
                }

                const lines = [formatLocalDateTime(point.data[0])];
                tooltipParams.forEach((param) => {
                    if (!Array.isArray(param?.data)) {
                        return;
                    }
                    if (param.seriesName === 'Füllstand' && typeof param.data[1] === 'number') {
                        lines.push(`${param.seriesName}: ${param.data[1].toFixed(2)} cm`);
                    }
                    if (typeof param.data[2] === 'number') {
                        lines.push(`Steigung: ${param.data[2].toFixed(2)} cm/h`);
                    }
                    if (typeof param.data[3] === 'number') {
                        lines.push(`Dauer: ${param.data[3].toFixed(1)} min`);
                    }
                });
                return lines.join('<br>');
            }
        },
        legend: {
            top: '0%',
            textStyle: {
                color: '#e2e8f0'
            }
        }
    });

    chartObj.setOption(chartOptions, {
        notMerge: false,
        replaceMerge: ['series', 'title', 'xAxis', 'yAxis', 'grid', 'dataZoom'],
        lazyUpdate: true,
        silent: true
    });
}

async function updateDailyCycleCountChart(chartObj, processedData, aggregation = 'day', cycleType = 'fill') {
    const countField = cycleType === 'drain' ? 'drain_count' : 'fill_count';
    const cycleTypeLabel = cycleType === 'drain' ? 'Drain-Zyklen' : 'Befüllungen';
    const chartTitlePrefix = cycleType === 'drain'
        ? 'Steigung der Drain-Zyklen und Anzahl pro'
        : 'Steigung der Zyklen und Befüllungen pro';

    const bucketKey = (timestamp, mode) => {
        const date = new Date(timestamp);
        if (mode === 'week') {
            const start = new Date(date);
            const day = start.getDay();
            const diff = (day + 6) % 7;
            start.setDate(start.getDate() - diff);
            start.setHours(0, 0, 0, 0);
            return start.toISOString().slice(0, 10);
        }
        if (mode === 'month') {
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        }
        return date.toISOString().slice(0, 10);
    };

    const labelForBucket = (bucket, mode) => {
        if (!bucket) {
            return '—';
        }
        const parseBucketDateUtc = (dateString) => {
            const date = new Date(`${dateString}T00:00:00Z`);
            return Number.isFinite(date.getTime()) ? date : null;
        };
        const formatDayLabel = (date) => {
            const day = String(date.getUTCDate()).padStart(2, '0');
            const month = String(date.getUTCMonth() + 1).padStart(2, '0');
            const year = date.getUTCFullYear();
            return `${day}.${month}.${year}`;
        };
        const getIsoWeekAndYear = (date) => {
            const utcDate = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
            const day = utcDate.getUTCDay() || 7;
            utcDate.setUTCDate(utcDate.getUTCDate() + 4 - day);
            const yearStart = new Date(Date.UTC(utcDate.getUTCFullYear(), 0, 1));
            const week = Math.ceil((((utcDate - yearStart) / 86400000) + 1) / 7);
            return { week, year: utcDate.getUTCFullYear() };
        };

        if (mode === 'month') {
            const [year, month] = bucket.split('-').map(Number);
            if (!Number.isFinite(year) || !Number.isFinite(month) || month < 1 || month > 12) {
                return bucket;
            }
            return `${String(month).padStart(2, '0')}-${year}`;
        }
        if (mode === 'week') {
            const date = parseBucketDateUtc(bucket);
            if (!date) {
                return bucket;
            }
            const { week, year } = getIsoWeekAndYear(date);
            return `${week}-${year}`;
        }
        const date = parseBucketDateUtc(bucket);
        if (!date) {
            return bucket;
        }
        return formatDayLabel(date);
    };

    const categoriesSet = new Set();
    processedData.forEach((chart) => {
        const cycles = Array.isArray(chart?.evaluation?.cycle_deviation?.cycles) ? chart.evaluation.cycle_deviation.cycles : [];
        cycles.forEach((entry) => {
            if (entry?.timestamp && entry?.cycle_type === cycleType) {
                categoriesSet.add(bucketKey(entry.timestamp, aggregation));
            }
        });
    });
    const categories = Array.from(categoriesSet).sort();
    if (categories.length === 0) {
        chartObj.clear();
        return;
    }

    const quantile = (values, q) => {
        if (!Array.isArray(values) || values.length === 0) {
            return 0;
        }
        const sorted = [...values].sort((a, b) => a - b);
        const pos = (sorted.length - 1) * q;
        const lo = Math.floor(pos);
        const hi = Math.ceil(pos);
        if (lo === hi) {
            return sorted[lo];
        }
        const weight = pos - lo;
        return sorted[lo] * (1 - weight) + sorted[hi] * weight;
    };

    const series = [];
    const useBoxplotForSlope = categories.length < 15;
    processedData.forEach((chart) => {
        const cycles = Array.isArray(chart?.evaluation?.cycle_deviation?.cycles)
            ? chart.evaluation.cycle_deviation.cycles.filter((entry) => entry?.cycle_type === cycleType)
            : [];
        const dailyCounts = Array.isArray(chart?.evaluation?.daily_cycle_counts) ? chart.evaluation.daily_cycle_counts : [];
        const mapByDay = new Map(dailyCounts.map((entry) => [entry.day, entry]));
        const byBucket = new Map();

        cycles.forEach((entry) => {
            const bucket = bucketKey(entry.timestamp, aggregation);
            if (!byBucket.has(bucket)) {
                byBucket.set(bucket, []);
            }
            byBucket.get(bucket).push(Number(entry.mean_slope_abs || 0));
        });

        const medianData = categories.map((bucket) => {
            const values = byBucket.get(bucket) || [];
            if (!values.length) {
                return null;
            }
            return quantile([...values].sort((a, b) => a - b), 0.5);
        });

        const boxplotData = categories.map((bucket) => {
            const values = byBucket.get(bucket) || [];
            if (!values.length) {
                return null;
            }
            const sorted = [...values].sort((a, b) => a - b);
            return [
                sorted[0],
                quantile(sorted, 0.25),
                quantile(sorted, 0.5),
                quantile(sorted, 0.75),
                sorted[sorted.length - 1],
            ];
        });

        const fillCountData = categories.map((bucket) => {
            if (aggregation === 'day') {
                return mapByDay.get(bucket)?.[countField] ?? 0;
            }
            if (aggregation === 'week' || aggregation === 'month') {
                let total = 0;
                for (const [day, entry] of mapByDay.entries()) {
                    const dayBucket = bucketKey(`${day}T00:00:00Z`, aggregation);
                    if (dayBucket === bucket) {
                        total += entry?.[countField] || 0;
                    }
                }
                return total;
            }
            return 0;
        });

        const sensorColor = getSensorColor(chart.sensorID || 'Sensor');
        if (useBoxplotForSlope) {
            series.push({
                name: `${chart.sensorID} Boxplot`,
                type: 'boxplot',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: boxplotData,
                itemStyle: {
                    color: `${sensorColor}66`,
                    borderColor: sensorColor,
                    borderWidth: 1.5
                },
                tooltip: {
                    formatter: (params) => {
                        const value = params?.value || [];
                        if (!Array.isArray(value) || value.length < 5) {
                            return `${params.seriesName}`;
                        }
                        return `${params.seriesName}<br>Min: ${Number(value[0]).toFixed(2)}<br>Q1: ${Number(value[1]).toFixed(2)}<br>Median: ${Number(value[2]).toFixed(2)}<br>Q3: ${Number(value[3]).toFixed(2)}<br>Max: ${Number(value[4]).toFixed(2)} cm/h`;
                    }
                }
            });
        } else {
            series.push({
                name: `${chart.sensorID} Median`,
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: medianData,
                smooth: true,
                symbol: 'none',
                lineStyle: { color: sensorColor, width: 2.5 },
                itemStyle: { color: sensorColor },
                tooltip: {
                    formatter: (params) => `${params.seriesName}<br>${params.name}: ${Number(params.value).toFixed(2)} cm/h`
                }
            });
        }

        series.push({
            name: `${chart.sensorID} ${cycleTypeLabel}`,
            type: 'bar',
            data: fillCountData,
            xAxisIndex: 1,
            yAxisIndex: 1,
            barWidth: '32%',
            itemStyle: {
                color: `${sensorColor}33`,
                borderColor: sensorColor,
                borderWidth: 1
            },
            tooltip: {
                formatter: (params) => `${params.name}<br>${cycleTypeLabel}: ${params.value}`
            }
        });
    });

    const chartTitle = aggregation === 'week'
        ? `${chartTitlePrefix} Woche`
        : aggregation === 'month'
            ? `${chartTitlePrefix} Monat`
            : `${chartTitlePrefix} Tag`;

    const chartOptions = createSharedChartChrome({
        title: {
            text: chartTitle,
            left: 'center',
            top: '2%',
            textStyle: { color: '#e2e8f0' }
        },
        grid: [
            { left: '6%', right: '4%', top: '14%', bottom: '52%', height: '32%' },
            { left: '6%', right: '4%', top: '58%', bottom: '12%', height: '24%' }
        ],
        xAxis: [
            {
                type: 'category',
                gridIndex: 0,
                data: categories.map(labelForBucket),
                axisLabel: { color: '#cbd5e1', rotate: 45, show: false },
                axisLine: { lineStyle: { color: '#94a3b8' } },
                axisTick: { show: false }
            },
            {
                type: 'category',
                gridIndex: 1,
                data: categories.map(labelForBucket),
                axisLabel: { color: '#cbd5e1', rotate: 45 },
                axisLine: { lineStyle: { color: '#94a3b8' } },
                axisTick: { show: false }
            }
        ],
        yAxis: [
            {
                type: 'value',
                gridIndex: 0,
                name: 'Steigung [cm/h]',
                axisLabel: { color: '#cbd5e1' },
                axisLine: { lineStyle: { color: '#94a3b8' } },
                splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } }
            },
            {
                type: 'value',
                gridIndex: 1,
                name: `${cycleTypeLabel} / Eintrag`,
                axisLabel: { color: '#cbd5e1' },
                axisLine: { lineStyle: { color: '#94a3b8' } },
                splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } }
            }
        ],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        legend: {
            top: '8%',
            textStyle: { color: '#e2e8f0' }
        },
        series
    });

    chartObj.setOption(chartOptions, {
        notMerge: true,
        replaceMerge: ['series', 'xAxis', 'yAxis', 'grid', 'title'],
        lazyUpdate: true,
        silent: true
    });
}

async function updateStdDevChart(chartObj, stdDevData, mpName, aggregation = 'day') {
    const bucketKey = (timestamp, mode) => {
        const date = new Date(timestamp);
        if (mode === 'week') {
            const start = new Date(date);
            const day = start.getDay();
            const diff = (day + 6) % 7;
            start.setDate(start.getDate() - diff);
            start.setHours(0, 0, 0, 0);
            return start.toISOString().slice(0, 10);
        }
        if (mode === 'month') {
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        }
        return date.toISOString().slice(0, 10);
    };

    const labelForBucket = (bucket, mode) => {
        if (!bucket) {
            return '—';
        }
        if (mode === 'month' || mode === 'week') {
            return bucket.slice(5);
        }
        return bucket.slice(5);
    };

    const sensorGroups = stdDevData && typeof stdDevData === 'object' ? (stdDevData[mpName] || []) : [];
    if (!Array.isArray(sensorGroups) || sensorGroups.length === 0) {
        chartObj.clear();
        return;
    }

    const categories = Array.from(new Set(sensorGroups.flatMap((sensor) => Array.isArray(sensor.rows) ? sensor.rows.map((row) => bucketKey(row.timestamp, aggregation)).filter(Boolean) : []))).sort();
    const series = sensorGroups.map((sensor) => {
        const byBucket = new Map();
        for (const row of Array.isArray(sensor.rows) ? sensor.rows : []) {
            const timestamp = row?.timestamp;
            if (!timestamp) {
                continue;
            }
            const bucket = bucketKey(timestamp, aggregation);
            if (!byBucket.has(bucket)) {
                byBucket.set(bucket, []);
            }
            const stdValue = Number(row?.meas_val_std ?? 0);
            if (Number.isFinite(stdValue)) {
                byBucket.get(bucket).push(stdValue);
            }
        }

        const data = categories.map((bucket) => {
            const values = byBucket.get(bucket) || [];
            if (!values.length) {
                return null;
            }
            const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
            return Number(mean.toFixed(3));
        });

        const sensorName = sensor.sensorID || 'Sensor';
        return {
            name: sensorName,
            type: 'bar',
            data,
            xAxisIndex: 0,
            yAxisIndex: 0,
            barWidth: '32%',
            itemStyle: {
                color: `${getSensorColor(sensorName)}33`,
                borderWidth: 1,
                borderColor: getSensorColor(sensorName)
            },
            tooltip: {
                formatter: (params) => `${params.seriesName}<br>${params.name}: ${Number(params.value).toFixed(3)} cm`
            }
        };
    });
    const chartTitle = aggregation === 'week'
        ? 'Standardabweichung pro Woche'
        : aggregation === 'month'
            ? 'Standardabweichung pro Monat'
            : 'Standardabweichung pro Tag';

    const chartOptions = createSharedChartChrome({
        title: {
            text: chartTitle,
            left: 'center',
            top: '2%',
            textStyle: { color: '#e2e8f0' }
        },
        grid: {
            left: '6%',
            right: '4%',
            bottom: '16%',
            top: '16%'
        },
        xAxis: {
            type: 'category',
            data: categories.map((bucket) => labelForBucket(bucket, aggregation)),
            axisLabel: { color: '#cbd5e1', rotate: 30 },
            axisLine: { lineStyle: { color: '#94a3b8' } }
        },
        yAxis: {
            type: 'value',
            name: 'Std. [cm]',
            axisLabel: { color: '#cbd5e1' },
            axisLine: { lineStyle: { color: '#94a3b8' } },
            splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        legend: {
            top: '8%',
            textStyle: { color: '#e2e8f0' }
        },
        series
    });

    chartObj.setOption(chartOptions, {
        notMerge: false,
        replaceMerge: ['series', 'xAxis', 'yAxis'],
        lazyUpdate: true,
        silent: true
    });
}

async function updateIntervalHistogramChart(chartObj, processedData) {
    const categories = ['0-5', '5-10', '10-15', '15-30', '30-60', '>60'];
    const series = processedData.map((chart) => {
        const histogram = Array.isArray(chart?.evaluation?.interval_histogram) ? chart.evaluation.interval_histogram : [];
        const mapped = categories.map((label) => {
            const bin = histogram.find((entry) => entry.label === label);
            return bin ? bin.count : 0;
        });
        return {
            name: chart.sensorID,
            type: 'bar',
            barGap: 0.12,
            data: mapped,
            itemStyle: {
                color: `${getSensorColor(chart.sensorID || 'Sensor')}33`,
                borderWidth: 1,
                borderColor: getSensorColor(chart.sensorID || 'Sensor')
            }
        };
    });

    const chartOptions = createSharedChartChrome({
        title: {
            text: 'Datenverteilung nach Aufnahmeintervall [min]',
            left: 'center',
            top: '2%',
            textStyle: { color: '#e2e8f0' }
        },
        grid: {
            left: '6%',
            right: '4%',
            bottom: '16%',
            top: '16%'
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: { color: '#cbd5e1' },
            axisLine: { lineStyle: { color: '#94a3b8' } }
        },
        yAxis: {
            type: 'value',
            name: 'Anzahl Intervalle',
            axisLabel: { color: '#cbd5e1' },
            axisLine: { lineStyle: { color: '#94a3b8' } },
            splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
        },
        legend: {
            top: '8%',
            textStyle: { color: '#e2e8f0' }
        },
        series
    });

    chartObj.setOption(chartOptions, {
        notMerge: false,
        replaceMerge: ['series', 'xAxis', 'yAxis'],
        lazyUpdate: true,
        silent: true
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
            color: '#e2e8f0'
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
            axisLine: { onZero: false, lineStyle: { color: '#94a3b8' } },
            axisLabel: {
                formatter: (value) => formatLocalDateTime(value),
                rotate: 45,
                color: '#cbd5e1'
            },
            axisPointer: {
                label: {
                    formatter: ({ value }) => formatLocalDateTime(value),
                    color: '#e2e8f0',
                    backgroundColor: 'rgba(15, 23, 42, 0.95)'
                }
            },
            splitLine: {
                lineStyle: { color: 'rgba(148, 163, 184, 0.18)' }
            },
            gridIndex: index,
        });
        if (bPrintLines == 'value') {
            yAxisConfigs.push({
               type: 'value',
               min: 0,
               max: chart.y_max,
               gridIndex: index,
               axisLabel: {
                 color: '#cbd5e1'
               },
               axisLine: {
                 lineStyle: { color: '#94a3b8' }
               },
               splitLine: {
                 lineStyle: { color: 'rgba(148, 163, 184, 0.18)' }
               }
            });
        } else if (bPrintLines == 'deriv') {
            yAxisConfigs.push({
               type: 'value',
               min: chart.deriv_y_min,
               max: chart.deriv_y_max,
               gridIndex: index,
               axisLabel: {
                 color: '#cbd5e1'
               },
               axisLine: {
                 lineStyle: { color: '#94a3b8' }
               },
               splitLine: {
                 lineStyle: { color: 'rgba(148, 163, 184, 0.18)' }
               }
               // logBase:1024,
            });
        }
        if (bPrintLines == 'value') {
            const smoothedValueSeries = chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value_savgol ?? item.value]);
            const rawValueSeries = chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value_raw ?? item.value]);
            const maxSeries = chart.values.map(item => [new Date(item.timestamp).getTime(), item.max_val]);
            const warnSeries = chart.values.map(item => [new Date(item.timestamp).getTime(), item.warn]);
            const alarmSeries = chart.values.map(item => [new Date(item.timestamp).getTime(), item.alarm]);
            tooltipConfigs.push(
                {
                    trigger: 'axis',
                    formatter: function(params) {
                        let tooltipContent = '';
                        tooltipContent += `${formatLocalDateTime(params[0].data[0])}<br>`;
                        tooltipContent += `Value: ${params[0].data[1]} cm<br>`;
                        return tooltipContent;
                    }
                }
            );
            seriesConfigs.push(
              {
                name: 'Geglättet',
                type: 'line',
                smooth: true,
                data: smoothedValueSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                sampling: 'lttb',
                progressive: 2000,
                progressiveThreshold: 3000,
                animation: false,
                lineStyle:{
                    color:firstLineColor,
                    width:3
                },
                showSymbol: false,
              },
              {
                name: 'Rohdaten',
                type: 'line',
                smooth: false,
                data: rawValueSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                sampling: 'lttb',
                progressive: 2000,
                progressiveThreshold: 3000,
                animation: false,
                lineStyle:{
                    color:'rgba(148, 163, 184, 0.8)',
                    width:1
                },
                showSymbol: false,
                emphasis: { focus: 'series' },
                tooltip: {
                    formatter: function(params) {
                        const value = Array.isArray(params?.data) ? params.data[1] : params?.value;
                        return `${formatLocalDateTime(params.data[0])}<br>Rohdaten: ${value} cm`;
                    }
                }
              },

              {
                name: 'Max',
                type: 'line',
                smooth: true,
                data: maxSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                sampling: 'lttb',
                progressive: 2000,
                progressiveThreshold: 3000,
                animation: false,
                lineStyle:{
                    color:'#7dd3fc',
                    type:'dashed',
                    width:1
                },
                symbol: 'none',

              },
              {
                name: 'Warn',
                type: 'line',
                smooth: true,
                data: warnSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                sampling: 'lttb',
                progressive: 2000,
                progressiveThreshold: 3000,
                animation: false,
                lineStyle:{
                    color:'#fbbf24',
                    type:'dashed',
                    width:1
                },
                symbol: 'none',

              },
              {
                name: 'Alarm',
                type: 'line',
                smooth: true,
                data: alarmSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                sampling: 'lttb',
                progressive: 2000,
                progressiveThreshold: 3000,
                animation: false,
                lineStyle:{
                    color:'#f87171',
                    type:'dashed',
                    width:1,
                },
                symbol: 'none',

              },
            );
        } else {
            const derivSeries = chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value]);
            const deriv10Series = chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.value_10]);
            const peakPosSeries = chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.peaks_pos]);
            const peakNegSeries = chart[dDict].map(item => [new Date(item.timestamp).getTime(), item.peaks_neg]);
            seriesConfigs.push(
              {
                name: 'Derivation [cm/h]',
                type: 'line',
                smooth: true,
                data: derivSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                silent:true,
                sampling: 'lttb',
                show: false,
                lineStyle:{
                    color:'#cbd5e1',
                    width:1
                },
              },
              {
                name: 'Avg of 10 of Derivation [cm/h]',
                type: 'line',
                smooth: true,
                data: deriv10Series,
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'none',
                sampling: 'lttb',
                lineStyle:{
                    color:'#fbbf24',
                    width:3
                },
              },
              {
                name: 'Positive Peaks',
                type: 'scatter',
                data: peakPosSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'triangle',
                symbolSize: 15,
                symbolColor: 'red',
                sampling: 'lttb',
                tooltip: {
                    formatter: (params) => formatPeakTooltip(params)
                }

              },
              {
                name: 'Negative Peaks',
                type: 'scatter',
                data: peakNegSeries,
                xAxisIndex: index,
                yAxisIndex: index,
                symbol: 'triangle',
                symbolSize: 15,
                symbolColor: 'red',
                sampling: 'lttb',
                tooltip: {
                    formatter: (params) => formatPeakTooltip(params)
                }

              },
            );
            tooltipConfigs.push(
                {
                    trigger: 'axis',
                    formatter: function(params) {
                        const tooltipParams = Array.isArray(params) ? params : [params];
                        const pointWithTimestamp = tooltipParams.find((param) => Array.isArray(param?.data) && param.data.length > 1);
                        if (!pointWithTimestamp) {
                            return '';
                        }

                        const lines = [formatLocalDateTime(pointWithTimestamp.data[0])];
                        tooltipParams.forEach((param) => {
                            const data = Array.isArray(param?.data) ? param.data : [];
                            const value = data[1];
                            if (typeof value === 'number' && Number.isFinite(value)) {
                                lines.push(`${param.seriesName}: ${value} cm/h`);
                            }
                        });

                        return lines.join('<br>');
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
      backgroundColor: plotBackGround,
      textStyle: {
        color: '#e2e8f0'
      },
      animation: false,
      animationDuration: 0,
      animationDurationUpdate: 0,
      title: titleConfigs,
      xAxis: xAxisConfigs,
      yAxis: yAxisConfigs,
      series: seriesConfigs,
      dataZoom: dataZoomConfigs,
      tooltip: tooltipConfigs,
      legend: {
        ...legendConfig,
        textStyle: {
          color: '#e2e8f0'
        }
      },
      toolbox: {
        show: true,
        orient: 'horizontal',
        feature: {
          dataZoom: {
            yAxisIndex: 'none'
          },
          dataView: { readOnly: false },
          restore: {},
          saveAsImage: {}
        },
        iconStyle: {
          borderColor: '#cbd5e1'
        },
        emphasis: {
          iconStyle: {
            borderColor: '#67e8f9'
          }
        }
      }
    }

    chartObj.setOption(chartOptions,{ notMerge: true, replaceMerge: ['series'] });
}