<script>
    import * as echarts from 'echarts';
    import { onMount } from 'svelte';

    function formatDateForInput(date) {

       const year = date.getFullYear();
       const month = String(date.getMonth() + 1).padStart(2, "0");
       const day = String(date.getDate()).padStart(2, "0");
       const hours = String(date.getHours()).padStart(2, "0");
       const minutes = String(date.getMinutes()).padStart(2, "0");
       return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    function formatDateForISO(dateString) {
    return new Date(dateString).toISOString().replace("Z","+00:00"); // ISO-Format sicherstellen
  }

    const now = new Date();
    const twoWeeksAgo = new Date(new Date().setDate(new Date().getDate() - 14));

    let dtFrom = formatDateForInput(twoWeeksAgo);
    let dtUntil = formatDateForInput(now);

    console.log("dtFrom: ",dtFrom);

    let data_fill = [];
    let chartDiv;
    let cConfig;
    let mpName;
    let chartInstances = {};

    let isLoading = true;

    let selectedMpName = '';
    let mpNameOptions = [];



    onMount(async () => {
        loadCharts();
    });

    async function loadCharts() {
        await loadFillChart();
        await loadTimeChart();
    }

    async function loadTimeChart() {
        console.log("Loading time chart");
        console.log("From: ", dtFrom);
        console.log("Until: ", dtUntil);
        const loadedApiTimeData = await loadTimeDataFromAPI();
        await updateTimeChart(loadedApiTimeData, 'values',  'timeChart', 'value');
        await updateTimeChart(loadedApiTimeData, 'deriv',  'derivChart', 'deriv');

        chartInstances['timeChart'].on('dataZoom', function (event) {
            console.log(event)

            if (event.dataZoomId === '\u0000series\u00000\u00000') {
                console.log("Zoom xAxis 0");
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
                console.log("Zoom xAxis 1");
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

    async function loadTimeDataFromAPI() {

        try {
            const response = await fetch(cConfig['APIUrl'].concat('get/'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify (
                    {
                        'dt_begin': formatDateForISO(dtFrom),
                        'dt_end': formatDateForISO(dtUntil),
                    }
                ),
            });
            if (!response.ok) {
                throw new Error("Invalid Network response!");
            }
            var data_t = await response.json();
            data_t = JSON.parse(data_t);
            //console.log('Data fetched:', JSON.stringify(data_f,null,2));
            const data_time = data_t[mpName];

            return data_time
        } catch (error) {
            console.error('Error while fetching time data from API:',error);
        }
    }

    async function updateTimeChart(loadedApiTimeData, dDict, divName, bPrintLines) {
        console.log("updating Time chart", loadedApiTimeData);

        if (chartInstances[divName]) {
            echarts.dispose(chartInstances[divName]);
        }
        chartInstances[divName] = echarts.init(document.getElementById(divName),'dark');

        if (loadedApiTimeData == null) {
            return
        }

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
               text: chart.sensor_name,
               //left: `${5+ index * (100.0/countOfSubplots)}%`,
               top:'25',
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
                  yAxisIndex:0,
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
                  yAxisIndex: 0,
                  start: 0,
                  end: 100,
                });
            }
        });

        const chartOptions = {
          grid: gridConfigs,
          backgroundColor:'rgba(255,255,255,0)',
          /*title: loadedApiTimeData.map((chart, index) => ({
            text: chart.sensorId,
            left: 'center',
            top: `${5 + index * 35}%`,
            gridIndex: index,
            textStyle: { fontSize: 14, fontWeight: 'bold' },
          })),*/
          title: titleConfigs,
          xAxis: xAxisConfigs,
          yAxis: yAxisConfigs,
          series: seriesConfigs,
          dataZoom: dataZoomConfigs,
          tooltip: tooltipConfigs,
          /*graphic: [
            {
              type: 'group',
              rotation: Math.PI / 4,
              bounding: 'raw',
              right: 110,
              bottom: 110,
              z: 100,
              children: [
                {
                  type: 'rect',
                  left: 'center',
                  top: 'center',
                  z: 100,
                  shape: {
                    width: 400,
                    height: 50
                  },
                  style: {
                    fill: 'rgba(0,0,0,0.3)'
                  }
                },
                {
                  type: 'text',
                  left: 'center',
                  top: 'center',
                  z: 100,
                  style: {
                    fill: '#fff',
                    text: 'ECHARTS LINE CHART',
                    font: 'bold 26px sans-serif'
                  }
                }
              ]
            }
          ]*/
        };
        console.log("gridConfigs", chartOptions);
        chartInstances[divName].setOption(chartOptions);
    }

    async function loadFillChart() {
        console.log("Loading fill chart");
        //const [loadedColors, loadedApiData] = await Promise.all([
        //      loadFillDataFromAPI()
        //    ]);

        const loadedApiFillData = await loadFillDataFromAPI();
        updateFillChart(data_fill);
    }

    async function loadFillDataFromAPI () {
        try {
            cConfig = await fetchChartConfig();

            const response = await fetch(cConfig['APIUrl'].concat('get_latest/'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error("Invalid Network response!");
            }
            var data_f = await response.json();
            data_f = JSON.parse(data_f);
            //console.log('Data fetched:', JSON.stringify(data_f,null,2));
            mpNameOptions = Object.keys(data_f);
            mpName = mpName || mpNameOptions[0];
            //mpName = "raspi2";
            //console.log('mpName', mpName);
            data_fill = data_f[mpName];
            //console.log('Data selected:', data_fill);
        } catch (error) {
            console.error('Error while fetching data from API:',error);
        }

    }

    async function fetchChartConfig() {
        try {
            const response_cConfig = await fetch('http://localhost:5173/chartConfig.json');
            if (!response_cConfig.ok) {
                throw new Error ("No response from cConfig-JSON");
            }
            const cConfig = await response_cConfig.json();
            return cConfig;
            //console.log('Color Gradients:',colorGradients);
        } catch(error) {
            console.error('Error while fetching colors!',error);
        }

    }

    function getLinearGradient(colorString) {
        //console.log("Gradients from File:", colorGradients);
        //console.log("Color String:",colorString);
        const gradient = cConfig['colors'][colorString];
        //console.log("Gradient: ", gradient);
        if(gradient) {
            return new echarts.graphic.LinearGradient(0, 0, 0, 1, gradient);
        }
        return "blue";
    }

    async function updateFillChart(chartData) {
        //console.log("chartData:",chartData);
        const sensorIDs = data_fill.sensor_name;
        console.log ('Sensor IDs:',sensorIDs);
        const values = data_fill.value;
        const colors = data_fill.color;
        const chartCols = colors.map(getLinearGradient);
        const maxVal = data_fill.max_val;
        const thWarn = data_fill.warn;
        const thAlarm = data_fill.alarm;

        const chart = echarts.init(document.getElementById('myChart'),'dark');

        //console.log ('Colors c1:',chartCols);

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
                  type: 'inside'
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
</script>

<main>
    <h1  class="text-3xl font-bold underline">Wassermonitor</h1>
    <select bind:value={mpName} on:change={loadCharts} class="w-6 h-6 ms-2 text-white dark:text-black" >
        {#each mpNameOptions as option}
           <option value={option}>{option}</option>
        {/each}
    </select>
    <div id='myChart' style='width: 100%;'></div>
    <div class="datetime-container">
      <!-- DateTime Picker: "From" -->
      <div class="datetime-picker">
        <label for="from-picker">From</label>
        <input
          id="from-picker"
          type="datetime-local"
          class="input input-lg bg-neutral text-neutral-content"
          bind:value={dtFrom}
          on:blur={loadTimeChart}
        />
      </div>

      <!-- DateTime Picker: "Until" -->
      <div class="datetime-picker">
        <label for="until-picker">Until</label>
        <input
          id="until-picker"
          type="datetime-local"
          bind:value={dtUntil}
          on:blur={loadTimeChart}
        />
      </div>
</div>
    <div id='timeChart' style='width:100%;'>TimeChart</div>
    <div id='derivChart' style='width:100%;'>DerivChart</div>
</main>

<style>
    div{
        width: 100%;
        height: 600px;
    }
    main {
        text-align: center;
    }

   .datetime-container {
    display: flex;
    gap: 1rem;
    align-items: center;
    height: 100%;
  }

  .datetime-picker {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  label {
    font-weight: bold;
    margin-bottom: 0.25rem;
  }
</style>

