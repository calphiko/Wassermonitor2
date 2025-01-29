<script>
    import { onMount, onDestroy } from 'svelte';
    import { getAvailableMeasPointsFromApi } from './api';
    import { formatDateForInput, formatDateForISO, fetchChartConfig } from './utils';
    import { loadFillChart, loadTimeChart } from './charts';

    const cConfigUrl = '/chartConfig.json';
    //const apiUrl = 'http://localhost:8012/'
    let apiUrl;
    let intervalId = null;

    let now;
    let twoWeeksAgo;
    let dtFrom;
    let dtUntil;

    let autoUpdateEnabled = true;

    let chartInstances = [];

    //const fillChart = document.getElementById('fillChart');

    let charts = {};
    let heading;

    let mpName;
    let isLoading = true;

    let selectedMpName = '';
    let mpNameOptions;
    let DarkMode = false;



    function handleDarkModeChange(event) {
        DarkMode = event.matches; // Dark Mode Status aktualisieren
        loadCharts();              // Charts neu laden
    }

    async function loadPage() {
        if (typeof window === "undefined") {
            return;
        }
        now = new Date();
        twoWeeksAgo = new Date(new Date().setDate(new Date().getDate() - 2));

        dtFrom = formatDateForInput(twoWeeksAgo);
        dtUntil = formatDateForInput(now);

        await loadCharts();


    }


    onMount(async () => {
        await loadPage();
        const darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");
        DarkMode = darkModeQuery.matches;
        // Register event listener
        darkModeQuery.addEventListener("change", handleDarkModeChange);
        startAutoUpdate()
    });


    async function loadCharts() {
        const chartConfig = await fetchChartConfig(cConfigUrl);
	    apiUrl = chartConfig.APIUrl;
        heading = chartConfig.title;
        mpNameOptions = await getAvailableMeasPointsFromApi(apiUrl);
        if (!mpName) {
            mpName = mpNameOptions[0].value;
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

    function toggleAutoUpdate() {
        autoUpdateEnabled = !autoUpdateEnabled;

        if (autoUpdateEnabled) {
            startAutoUpdate(); // Timer starten
        } else {
            stopAutoUpdate(); // Timer stoppen
        }
    }

    function startAutoUpdate() {
        if (!intervalId) {
            intervalId = setInterval(async () => {
                await loadPage();
            }, 60000); // Alle 60 Sekunden aktualisieren
        }
    }

    function stopAutoUpdate() {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    }

    onDestroy(() => {
        stopAutoUpdate();
    });

 </script>

<header>
    <nav class="fill-yellow-50  dark:fill-gray-600 text-gray-900 dark:text-gray-50 text-center">
        <div class="bg-yellow-50 dark:bg-gray-600 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white rounded-b-lg m-0">
		    <h1 class="align-center">
		        {heading}
		    </h1>
		    <button on:click={toggleAutoUpdate} class={autoUpdateEnabled ? " border rounded dark:border-gray-800 dark:text-red-400 text-red-700" : "border rounded dark:border-gray-400 text-gray-400"}>↻ <small>toggle auto refresh</small></button>
		</div>
	</nav>
</header>

<main>
    <div style="width:100%;">
        <select bind:value={mpName} on:change={loadCharts}  class='bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5'>
            {#each mpNameOptions as option}
               <option value={option.value}>{option.label}</option>
            {/each}
        </select>
        <div id='fillChart' class="chartDiv"></div>
        <div class="flex flex-row gap-5 h-12 my-10">
          <!-- DateTime Picker: "From" -->
          <div class="">
            <label for="from-picker" class="dark:text-white text-gray-600">From</label>
            <input
              id="from-picker"
              type="datetime-local"
              class="bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
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
              class = "bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
              bind:value={dtUntil}
              on:blur={loadCharts}
            />
          </div>
        </div>
        <div id='timeChart' class='chartDiv' >TimeChart</div>
        <div id='derivChart' class='chartDiv' >DerivChart</div>
    </div>
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


  header {
    position: sticky;
    top:0;
    padding: -2px 16px;
    z-index: 10;
  }

  nav {
		display: flex;
		justify-content: center;

  }

  .chartDiv {
    z-index:0;
    width: 100%;
    min-height: 400px;
    aspect-ratio: 16/9;
  }

</style>

