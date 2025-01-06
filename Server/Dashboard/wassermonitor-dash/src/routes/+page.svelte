<script>
    import { onMount } from 'svelte';
    import { getAvailableMeasPointsFromApi } from './api';
    import { formatDateForInput, formatDateForISO, fetchChartConfig } from './utils';
    import { loadFillChart, loadTimeChart } from './charts';

    const cConfigUrl = 'http://localhost:5173/chartConfig.json';
    const apiUrl = 'http://localhost:8012/'

    const now = new Date();
    const twoWeeksAgo = new Date(new Date().setDate(new Date().getDate() - 14));

    let dtFrom = formatDateForInput(twoWeeksAgo);
    let dtUntil = formatDateForInput(now);

    let chartInstances = [];

    //const fillChart = document.getElementById('fillChart');

    let charts = {};

    let mpName;
    let isLoading = true;

    let selectedMpName = '';
    let mpNameOptions;



    onMount(async () => {
        await loadCharts();
    });

    async function loadCharts() {
        const chartConfig = await fetchChartConfig(cConfigUrl);
        mpNameOptions = await getAvailableMeasPointsFromApi(apiUrl);
        if (!mpName) {
            mpName = mpNameOptions[0];
        };
        chartInstances = [
         {'name':'fillChart', 'divName': document.getElementById('fillChart')},
         {'name':'timeChart', 'divName': document.getElementById('timeChart')},
         {'name':'derivChart', 'divName': document.getElementById('derivChart')},
        ];
        //charts = chartInstances.map( item => reInitEchart(item.name, item.divName));
        await loadFillChart(chartInstances[0].divName, charts, chartConfig, mpName);
        await loadTimeChart(chartInstances, charts, chartConfig, dtFrom, dtUntil, mpName);
    }

 </script>

<main>
    <h1  class="text-3xl font-bold text-gray-800 dark:text-white h-12">Wassermonitor</h1>
    <select bind:value={mpName} on:change={loadCharts}  class='bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5'>
        {#each mpNameOptions as option}
           <option value={option}>{option}</option>
        {/each}
    </select>
    <div id='fillChart' style='width: 100%; height: 600%;'></div>
    <div class="flex flex-row gap-5 h-12 my-10">
      <!-- DateTime Picker: "From" -->
      <div class="">
        <label for="from-picker" class="dark:text-white text-gray-600">From</label>
        <input
          id="from-picker"
          type="datetime-local"
          class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
          bind:value={dtFrom}
          on:blur={loadCharts}
        />
      </div>

      <!-- DateTime Picker: "Until" -->
      <div class="">
        <label for="until-picker" class="dark:text-white text-gray-600">Until</label>
        <input
          id="until-picker"
          type="datetime-local"
          class = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
          bind:value={dtUntil}
          on:blur={loadCharts}
        />
      </div>
    </div>
    <div id='timeChart' style='width: 100%; height: 600%;'>TimeChart</div>
    <div id='derivChart' style='width: 100%; height: 600%;' >DerivChart</div>
</main>

<style>
    div{
        width: 100%;
        height: 600%;
    }

    main {
        text-align: center;
    }

  datetime-picker {
    height:100%;
  }


  label {
    font-weight: bold;
    margin-bottom: 0.25rem;
  }
</style>

