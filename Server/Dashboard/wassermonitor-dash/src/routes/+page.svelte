<script>
    import { onMount, onDestroy } from 'svelte';
    import { Toggle } from 'flowbite-svelte';
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

    let hasUserModifiedUntil = false;
    let hasUserModifiedFrom = false;



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

        if (!hasUserModifiedUntil) {
            dtUntil = formatDateForInput(now);
        }

        if (!hasUserModifiedFrom) {
            dtFrom = formatDateForInput(twoWeeksAgo);
        }
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
        console.log("Toggle autoUpdate", autoUpdateEnabled);

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

    function handleFromChange () {
        dtFrom = event.target.value
        hasUserModifiedFrom = true;
        loadCharts();
    }

    function handleUntilChange () {
        dtUntil = event.target.value
        hasUserModifiedUntil = true;
        loadCharts();
    }

    onDestroy(() => {
        stopAutoUpdate();
    });

 </script>

<header class="px-0 mx-0">
    <nav class="fill-yellow-50  dark:fill-gray-600 text-gray-900 dark:text-gray-50 text-center px-0 mx-0 w-full">
        <div class="heading bg-sky-300 dark:bg-gray-600 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white rounded-b-lg m-px p-px w-full">
            <h1 class="w-full">
                {heading}
            </h1>
        </div>
	</nav>

</header>

<main class="">
    <div class="grid place-items-center" >
        <select bind:value={mpName} on:change={loadCharts}  class='bg-sky-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-5/2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5 w-8/8' >
            {#each mpNameOptions as option}
               <option value={option.value}>{option.label}</option>
            {/each}
        </select>

        <Toggle class="" on:click={toggleAutoUpdate} checked={autoUpdateEnabled} size="small" color="blue">auto update</Toggle>

        <div id='fillChart' class="fillChartDiv"></div>
        <div class="flex flex-row ">
          <!-- DateTime Picker: "From" -->
          <div class="picker w-full sm:w-auto">
            <label for="from-picker" class="dark:text-white text-gray-600">From</label>
            <input
              id="from-picker"
              type="datetime-local"
              class="bg-sky-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
              bind:value={dtFrom}
              on:blur={handleFromChange}
            />
          </div>

          <!-- DateTime Picker: "Until" -->
          <div class="picker w-full sm:w-auto">
            <label for="until-picker" class="dark:text-white text-gray-600">Until</label>
            <input
              id="until-picker"
              type="datetime-local"
              class = "bg-sky-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
              bind:value={dtUntil}
              on:blur={handleUntilChange}
            />
          </div>
        </div>
        <div id='timeChart' class='timeChartDiv mx-2'>TimeChart</div>
        <div id='derivChart' class='timeChartDiv mx-2'>DerivChart</div>
    </div>
</main>

<style>
    .picker{
        width: 90%;
        height: 600%;
        padding: 1rem;
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
    width:auto;
    z-index: 10;
  }

  nav {
		display: flex;
		justify-content: center;
        width:100%;
  }

  .fillChartDiv {
    z-index:0;
    min-width:100%;
    height: 500px;
  }

  .timeChartDiv {
    z-index:0;
    min-width:100%;
    height: 700px;
  }

  .flex {
    display: flex;
    flex-direction: row; /* Nebeneinander */
    gap: 1rem; /* Abstand zwischen den Elementen */
  }

  @media (max-width: 500px) {
    .flex {
      flex-direction: column; /* Untereinander */
    }
  }

  .heading {
    width:100%;
  }

</style>

