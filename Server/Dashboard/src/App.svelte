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
        const chartDom = document.getElementById('main');
        if (chartDom) {

            const myChart = echarts.init(chartDom);

            const xData = data.map(item => item.sensor_id)
            const yData = data.map(item => item.value)


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