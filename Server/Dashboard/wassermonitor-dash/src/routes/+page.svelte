<script>
    import * as echarts from 'echarts';
    import { onMount } from 'svelte';


    let data_fill = [];
    let chartDiv;
    let colorGradients = {};
    let cConfig = {};

    onMount(async () => {
        const [loadedColors, loadedApiData] = await Promise.all([
          fetchChartConfig(),
          loadDataFromAPI()
        ]);
        updateChart();
    });

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
            data_fill  = await response.json();
            console.log('Data fetched:', data_fill);
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
            console.log('Color Gradients:',colorGradients);
        } catch(error) {
            console.error('Error while fetching colors!',error);
        }

    }


    function getLinearGradient(colorString) {
        console.log("Gradients from File:", colorGradients);
        console.log("Color String:",colorString);
        const gradient = colorGradients[colorString];
        console.log("Gradient: ", gradient);
        if(gradient) {
            return new echarts.graphic.LinearGradient(0, 0, 0, 1, gradient);
        }
        return "blue";
    }

    async function updateChart(chartData) {
        const sensorIDs = data_fill.sensor_id;
        const values = data_fill.value;
        const colors = data_fill.color;
        const chartCols = colors.map(getLinearGradient)

        const chart = echarts.init(document.getElementById('myChart'),'dark');
        console.log ('Sensor IDs:',sensorIDs);
        console.log ('Colors c1:',chartCols);

        const chartOptions = {
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
                  markLine: {
                    data: [
                        {
                          yAxis: cConfig['thresholds']['alarm'],
                          lineStyle: {
                            color:'red',
                            type: 'dashed'
                          },
                          label:{
                            formatter: 'Alarmschwelle'
                          },
                        },
                        {
                          yAxis: cConfig['thresholds']['warning'],
                          lineStyle: {
                            color:'orange',
                            type: 'dashed'
                          },
                          label:{
                            formatter: 'Warnschwelle'
                          },
                        },

                      ]
                  },
                },
              ]
        };
        chart.setOption(chartOptions);
    }
</script>

<main>
    <h1>Wassermonitor</h1>
    <div id='myChart' style='width: 100%;'></div>
</main>

<style>
    div{
        width: 100%;
        height: 600px;
    }
</style>

