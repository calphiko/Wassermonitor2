<script>
    import { onMount } from 'svelte';
    import * as echarts from 'echarts';

    let data = [];

    onMount (async () => {
        const token = 'secret_token'
        try{
            const response = await fetch('http://127.0.0.1:8012/get_latest/', {
                method: 'POST',
                headers: {
                    'Authorization':`Bearer ${token}`,
                    'Content-Type':'Application/json'
                }
            });
            if (!response.ok) {
                throw new Error( "Invalid Network Response!");
            }
            data = await response.json();
            createFillPlot();
        } catch (error) {
            console.error('Error while catching data from API:',error);
        }

    });

    function createFillPlot() {
        if (chartDom) {
            const chartDom = document.getElementById('main');
            const myChart = echarts.init(chartDom);

            const xData = data.map(item => item.sensor_id)
            const yData = data.map(item => item.value)

            const option = {
              title: {
                text: 'Wassermonitor',
                subtext: 'Feature Sample: Gradient Color, Shadow, Click Zoom'
              },
              xAxis: {
                data: xData,
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
                max: 150,
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
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: '#83bff6' },
                      { offset: 0.5, color: '#188df0' },
                      { offset: 1, color: '#188df0' }
                    ])
                  },

                  data: yData,
                  barWidth: '90%',
                  markLine: {
                    data: [
                        {
                          yAxis: 60,
                          lineStyle: {
                            color:'red',
                            type: 'dashed'
                          },
                          label:{
                            formatter: 'Alarmschwelle'
                          },
                        },
                        {
                          yAxis: 90,
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
            myChart.setOption(option);
        } else {
            console.error ('Element with id "main" not found!');
        }
    }
</script>

<style>
    #main {
        width: 600px;
        height: 400px;
    }
</style>

<div id="main">Load diagram...</div>