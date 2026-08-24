<script>
    import { onMount } from 'svelte';
    import { getAvailableMeasPointsFromApi } from './api';
    import { formatDateForInput, fetchChartConfig } from './utils';
    import { loadFillChart, loadTimeChart } from './charts';

    const cConfigUrl = '/chartConfig.json';
    const apiUrlFallback = 'http://localhost:8012/';
    const fillRefreshIntervalMs = 60 * 1000;

    const now = new Date();
    const twoWeeksAgo = new Date(new Date().setDate(new Date().getDate() - 14));
    const beginOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);

    /**
     * @typedef {{ value: string, label: string }} MeasurementPointOption
     * @typedef {{ APIUrl: string, title: string, plotTheme?: string, plotThemeDark?: string }} ChartConfig
     * @typedef {{ name: string, divName: HTMLElement }} ChartMount
     */

    let dtFrom = formatDateForInput(beginOfDay);
    let dtUntil = formatDateForInput(now);

    let charts = {};
    let heading = 'Wassermonitor2';
    let mpName = '';
    /** @type {MeasurementPointOption[]} */
    let mpNameOptions = [];
    let infoMessage = '';
    let fillChartLoading = true;
    let timeChartsLoading = true;
    let apiUrl = apiUrlFallback;
    /** @type {ChartConfig | null} */
    let chartConfig = null;
    /** @type {number | undefined} */
    let fillRefreshTimer;

    /**
     * @param {string | undefined} configApiUrl
     * @returns {string}
     */
    function resolveApiUrl(configApiUrl) {
        try {
            const base = new URL(configApiUrl || apiUrlFallback);
            if (base.hostname === '127.0.0.1' || base.hostname === 'localhost') {
                base.hostname = window.location.hostname;
            }
            return base.toString();
        } catch {
            return apiUrlFallback;
        }
    }

    /**
     * @returns {ChartMount}
     */
    function getFillChartMount() {
        const fillChart = document.getElementById('fillChart');
        if (!(fillChart instanceof HTMLElement)) {
            throw new Error('Fill chart container not found.');
        }

        return { name: 'fillChart', divName: fillChart };
    }

    /**
     * @returns {ChartMount[]}
     */
    function getTimeChartMounts() {
        const timeChart = document.getElementById('timeChart');
        const derivChart = document.getElementById('derivChart');

        if (!(timeChart instanceof HTMLElement) || !(derivChart instanceof HTMLElement)) {
            throw new Error('Time chart container not found.');
        }

        return [
            { name: 'timeChart', divName: timeChart },
            { name: 'derivChart', divName: derivChart }
        ];
    }

    function stopFillAutoRefresh() {
        if (fillRefreshTimer) {
            window.clearInterval(fillRefreshTimer);
            fillRefreshTimer = undefined;
        }
    }

    function startFillAutoRefresh() {
        stopFillAutoRefresh();
        fillRefreshTimer = window.setInterval(() => {
            void loadFillChartSection();
        }, fillRefreshIntervalMs);
    }

    async function loadDashboardConfig() {
        const loadedChartConfig = await fetchChartConfig(cConfigUrl);
        if (!loadedChartConfig) {
            chartConfig = null;
            heading = 'Wassermonitor2';
            infoMessage = 'Konfiguration konnte nicht geladen werden.';
            return false;
        }

        chartConfig = /** @type {ChartConfig} */ (loadedChartConfig);
        heading = chartConfig.title;
        apiUrl = resolveApiUrl(chartConfig.APIUrl);
        return true;
    }

    async function refreshMeasurementPointOptions() {
        mpNameOptions = /** @type {MeasurementPointOption[]} */ (await getAvailableMeasPointsFromApi(apiUrl) || []);
        if (mpNameOptions.length === 0) {
            infoMessage = `API nicht erreichbar (${apiUrl}). Bitte API-Server starten.`;
            return false;
        }

        infoMessage = '';
        const currentOptionExists = mpNameOptions.some((option) => option.value === mpName);
        if (!currentOptionExists) {
            mpName = mpNameOptions[0].value;
        }

        return true;
    }

    async function loadFillChartSection() {
        if (!chartConfig || !mpName || fillChartLoading) {
            return;
        }

        fillChartLoading = true;
        try {
            const fillChartMount = getFillChartMount();
            await loadFillChart(fillChartMount.divName, charts, chartConfig, mpName);
        } finally {
            fillChartLoading = false;
        }
    }

    async function loadTimeChartsSection() {
        if (!chartConfig || !mpName || timeChartsLoading) {
            return;
        }

        timeChartsLoading = true;
        try {
            const timeChartMounts = getTimeChartMounts();
            await loadTimeChart(timeChartMounts, charts, chartConfig, dtFrom, dtUntil, mpName);
        } finally {
            timeChartsLoading = false;
        }
    }

    async function initializeDashboard() {
        stopFillAutoRefresh();
        fillChartLoading = true;
        timeChartsLoading = true;

        const configLoaded = await loadDashboardConfig();
        if (!configLoaded) {
            fillChartLoading = false;
            timeChartsLoading = false;
            return;
        }

        const measurementPointsLoaded = await refreshMeasurementPointOptions();
        if (!measurementPointsLoaded) {
            fillChartLoading = false;
            timeChartsLoading = false;
            return;
        }

        fillChartLoading = false;
        timeChartsLoading = false;
        await loadFillChartSection();
        await loadTimeChartsSection();
        startFillAutoRefresh();
    }

    async function handleMeasurementPointChange() {
        stopFillAutoRefresh();
        await loadFillChartSection();
        await loadTimeChartsSection();
        startFillAutoRefresh();
    }

    /** @param {MediaQueryListEvent} _event */
    async function handleDarkModeChange(_event) {
        stopFillAutoRefresh();
        await loadFillChartSection();
        await loadTimeChartsSection();
        startFillAutoRefresh();
    }

    onMount(() => {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        void initializeDashboard();
        darkModeQuery.addEventListener('change', handleDarkModeChange);

        return () => {
            stopFillAutoRefresh();
            darkModeQuery.removeEventListener('change', handleDarkModeChange);
        };
    });
</script>

<header>
    <nav class="fill-yellow-50  dark:fill-gray-600 text-gray-900 dark:text-gray-50 text-center">
        <div class="bg-yellow-50 dark:bg-gray-600 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white rounded-b-lg m-0">
		    <h1>{heading}</h1>
		</div>
	</nav>
</header>

<main>

    {#if infoMessage}
        <p class="text-red-600 dark:text-red-400 font-semibold my-3">{infoMessage}</p>
    {/if}

    <select bind:value={mpName} on:change={handleMeasurementPointChange}  class='bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5'>
        {#each mpNameOptions as option}
           <option value={option.value}>{option.label}</option>
        {/each}
    </select>
    <div class="chart-container">
        {#if fillChartLoading}
            <div class="chart-loading-overlay" aria-busy="true" aria-live="polite">
                <div class="spinner"></div>
            </div>
        {/if}
        <div id='fillChart' class='chartDiv'></div>
    </div>
    <div class="controls-row my-10">
      <div class="control-field">
        <label for="from-picker" class="dark:text-white text-gray-600">From</label>
        <input
          id="from-picker"
          type="datetime-local"
          class="bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
          bind:value={dtFrom}
        />
      </div>

      <div class="control-field">
        <label for="until-picker" class="dark:text-white text-gray-600">Until</label>
        <input
          id="until-picker"
          type="datetime-local"
          class = "bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-10 my-5"
          bind:value={dtUntil}
        />
      </div>

      <button
        type="button"
        class="refresh-button bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2 px-4 rounded-lg h-10"
        on:click={loadTimeChartsSection}
        disabled={timeChartsLoading || !mpName}
      >
        aktualisieren
      </button>
    </div>
    <div class="chart-container">
        {#if timeChartsLoading}
            <div class="chart-loading-overlay" aria-busy="true" aria-live="polite">
                <div class="spinner"></div>
            </div>
        {/if}
        <div id='timeChart' class='chartDiv'></div>
    </div>
    <div class="chart-container">
        {#if timeChartsLoading}
            <div class="chart-loading-overlay" aria-busy="true" aria-live="polite">
                <div class="spinner"></div>
            </div>
        {/if}
        <div id='derivChart' class='chartDiv'></div>
    </div>
</main>

<style>
    main {
        text-align: center;
    }

  label {
    font-weight: bold;
    margin-bottom: 0.25rem;
  }

  .controls-row {
    display: flex;
    gap: 1.25rem;
    align-items: flex-end;
    flex-wrap: wrap;
  }

  .control-field {
    flex: 1 1 18rem;
    text-align: left;
  }

  .refresh-button {
    margin-bottom: 1.25rem;
  }

  .chart-container {
    position: relative;
    width: 100%;
    min-height: 600px;
  }

  .chartDiv {
    width: 100%;
    height: 600px;
    z-index: 0;
  }

  .chart-loading-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(253, 253, 234, 0.65);
    z-index: 5;
  }

  :global(.dark) .chart-loading-overlay {
    background: rgba(31, 41, 55, 0.65);
  }

  .spinner {
    width: 3rem;
    height: 3rem;
    border: 0.35rem solid rgba(59, 130, 246, 0.25);
    border-top-color: #2563eb;
    border-radius: 9999px;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }

    to {
      transform: rotate(360deg);
    }
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
</style>
