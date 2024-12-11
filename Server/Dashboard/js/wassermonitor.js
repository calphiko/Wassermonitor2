import * as echarts from './echarts.min.js';

async function getData() {
    const url = 'http://127.0.0.1:8012/get_latest/';
    const token = 'secret_token'

    try {
        const response = await fetch( url, {
            method:'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type':'application/json',
            }
        });
        if (!response.ok) {
            throw new Error('Invalid network repsonse!');
        }
        const data = await response.json()
        console.log(data);

    } catch (error) {
        console.error('There was an error with fetch-operation', error)
    }
};

async function getFillPlot() {

    const data = await getData();

    const xAxisData = data.map(item => 'sensor_id');
    const yAxisData = data.map(item => 'value');

    const chartDom = document.getElementById('main');
    const FillPlot = echarts.init(chartDom);

    const option = option = {
        title: {
        text: 'Wassermonitor',
        subtext: 'Feature Sample: Gradient Color, Shadow, Click Zoom'
    },
    xAxis: {
        data: xAxisData,
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
            data: data,
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
    // Enable data zoom when user click bar.
    const zoomSize = 4;
    myChart.on('click', function (params) {
      console.log(dataAxis[Math.max(params.dataIndex - zoomSize / 2, 0)]);
      myChart.dispatchAction({
        type: 'dataZoom',
        startValue: dataAxis[Math.max(params.dataIndex - zoomSize / 2, 0)],
        endValue:
          dataAxis[Math.min(params.dataIndex + zoomSize / 2, data.length - 1)]
      });
    });
};

getFillPlot;