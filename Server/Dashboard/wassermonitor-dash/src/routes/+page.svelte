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
    <h1  class="text-3xl font-bold underline">Wassermonitor</h1>
    <select bind:value={mpName} on:change={loadCharts}  >
        {#each mpNameOptions as option}
           <option value={option}>{option}</option>
        {/each}
    </select>
    <div id='fillChart' style='width: 100%;'></div>
    <div class="datetime-container">
      <!-- DateTime Picker: "From" -->
      <div class="datetime-picker">
        <label for="from-picker">From</label>
        <input
          id="from-picker"
          type="datetime-local"
          class="input input-lg bg-neutral text-neutral-content"
          bind:value={dtFrom}
          on:blur={loadCharts}
        />
      </div>

      <!-- DateTime Picker: "Until" -->
      <div class="datetime-picker">
        <label for="until-picker">Until</label>
        <input
          id="until-picker"
          type="datetime-local"
          bind:value={dtUntil}
          on:blur={loadCharts}
        />
      </div>
</div>
    <div id='timeChart' style='width:100%;padding-left:20px;padding-right:20px; padding-top:20px;'>TimeChart</div>
    <div id='derivChart' style='width:100%;padding-left:20px; padding-right:20px; padding-bottom:20px;'>DerivChart</div>
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

