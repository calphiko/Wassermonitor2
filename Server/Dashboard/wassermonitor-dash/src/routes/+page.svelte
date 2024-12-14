<script>
    import * as echarts from 'echarts';
    import { onMount } from 'svelte';
    import { Button, Dropdown, DropdownItem } from 'flowbite-svelte';
    import { ChevronDownOutline } from 'flowbite-svelte-icons';
    import { DatePicker } from '@svelte-plugins/datepicker';



    let data_fill = [];
    let chartDiv;
    let colorGradients = {};
    let cConfig = {};
    let mpName;

    let isLoading = true;

    let selectedMpName = '';
    let mpNameOptions = [];

    onMount(async () => {
        loadCharts();
    });

    async function loadCharts() {
        loadFillChart();
        loadTimeChart();
    }

    async function loadTimeChart() {
        console.log("Loading time chart");
    }

    async function loadFillChart() {
        console.log("Loading fill chart");
        const [loadedColors, loadedApiData] = await Promise.all([
              fetchChartConfig(),
              loadDataFromAPI()
            ]);
            updateFillChart(data_fill);
    }

    async function loadDataFromAPI () {
        try {
            const token = 'secret_token';
            const response = await fetch('http://127.0.0.1:8012/get_latest/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
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
            cConfig = await response_cConfig.json();
            colorGradients = cConfig['colors'];
            //console.log('Color Gradients:',colorGradients);
        } catch(error) {
            console.error('Error while fetching colors!',error);
        }

    }


    function getLinearGradient(colorString) {
        //console.log("Gradients from File:", colorGradients);
        //console.log("Color String:",colorString);
        const gradient = colorGradients[colorString];
        //console.log("Gradient: ", gradient);
        if(gradient) {
            return new echarts.graphic.LinearGradient(0, 0, 0, 1, gradient);
        }
        return "blue";
    }

    async function updateFillChart(chartData) {
        //console.log("chartData:",chartData);
        const sensorIDs = data_fill.mp_name;
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
                subtext: 'bla',
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
    <h1>Wassermonitor</h1>
    <select bind:value={mpName} on:change={loadCharts}>
        {#each mpNameOptions as option}
           <option value={option}>{option}</option>
        {/each}
    </select>
    <div id='myChart' style='width: 100%;'></div>

    <div id='timeChart' style='width:100%;'>TimeChart</div>
</main>

<style>
    div{
        width: 100%;
        height: 600px;
    }
    main {
        text-align: center;
    }
</style>

