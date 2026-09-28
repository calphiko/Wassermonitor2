<script>
    import { onMount, tick } from 'svelte';
    import { getAvailableMeasPointsFromApi } from './api';
    import { formatDateForInput, fetchChartConfig } from './utils';
    import { loadEvaluationCharts, loadFillChart, loadTimeChart } from './charts';

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
    let heading = 'Hallo';
    let mpName = '';
    let activeTab = 'current';
    let cycleAggregation = 'day';
    const cycleAggregationOptions = [
        { value: 'day', label: 'Tag' },
        { value: 'week', label: 'Woche' },
        { value: 'month', label: 'Monat' }
    ];
    const tabs = [
        { id: 'current', label: 'Aktuell' },
        { id: 'history', label: 'Verlauf' },
        { id: 'evaluation', label: 'Auswertung' }
    ];
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

    /**
     * @returns {ChartMount[]}
     */
    function getEvaluationChartMounts() {
        const cycleDeviationChart = document.getElementById('cycleDeviationChart');
        const dailyCycleCountChart = document.getElementById('dailyCycleCountChart');
        const intervalHistChart = document.getElementById('intervalHistChart');
        if (!(cycleDeviationChart instanceof HTMLElement) || !(dailyCycleCountChart instanceof HTMLElement) || !(intervalHistChart instanceof HTMLElement)) {
            throw new Error('Evaluation chart container not found.');
        }

        return [
            { name: 'cycleDeviationChart', divName: cycleDeviationChart },
            { name: 'dailyCycleCountChart', divName: dailyCycleCountChart },
            { name: 'intervalHistChart', divName: intervalHistChart }
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
        if (!chartConfig || !mpName || timeChartsLoading || activeTab !== 'history') {
            return;
        }

        timeChartsLoading = true;
        try {
            await tick();
            const timeChartMounts = getTimeChartMounts();
            await loadTimeChart(timeChartMounts, charts, chartConfig, dtFrom, dtUntil, mpName);
        } finally {
            timeChartsLoading = false;
        }
    }

    async function loadEvaluationChartsSection() {
        if (!chartConfig || !mpName || timeChartsLoading || activeTab !== 'evaluation') {
            return;
        }

        timeChartsLoading = true;
        try {
            await tick();
            const evalChartMounts = getEvaluationChartMounts();
            await loadEvaluationCharts(evalChartMounts, charts, chartConfig, dtFrom, dtUntil, mpName, cycleAggregation);
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
        await tick();
        await loadFillChartSection();
        if (activeTab === 'history') {
            await loadTimeChartsSection();
        } else if (activeTab === 'evaluation') {
            await loadEvaluationChartsSection();
        }
        startFillAutoRefresh();
    }

    async function handleMeasurementPointChange() {
        stopFillAutoRefresh();
        await tick();
        if (activeTab === 'current') {
            await loadFillChartSection();
        } else if (activeTab === 'history') {
            await loadTimeChartsSection();
        } else {
            await loadEvaluationChartsSection();
        }
        startFillAutoRefresh();
    }

    /** @param {MediaQueryListEvent} _event */
    async function handleDarkModeChange(_event) {
        stopFillAutoRefresh();
        await tick();
        await loadFillChartSection();
        if (activeTab === 'history') {
            await loadTimeChartsSection();
        } else if (activeTab === 'evaluation') {
            await loadEvaluationChartsSection();
        }
        startFillAutoRefresh();
    }

    async function handleTabChange(nextTab) {
        activeTab = nextTab;
        await tick();

        if (nextTab === 'current') {
            await loadFillChartSection();
            return;
        }

        if (nextTab === 'history') {
            await loadTimeChartsSection();
            return;
        }

        await loadEvaluationChartsSection();
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

<header class="topbar">
    <nav class="navbar" aria-label="Dashboard navigation">
        <div class="brand" aria-label="Wassermonitor logo">
            <img src="/Logo.png" alt="Wassermonitor Logo" class="brand-logo" />
        </div>

        <div class="nav-controls">
            <div class="station-control">
                <label class="station-label" for="measurement-point-select">Station:</label>
                <select
                    id="measurement-point-select"
                    bind:value={mpName}
                    on:change={handleMeasurementPointChange}
                    class="mp-select"
                >
                    {#each mpNameOptions as option}
                        <option value={option.value}>{option.label}</option>
                    {/each}
                </select>
            </div>

            <div class="tab-list" role="tablist" aria-label="Dashboard tabs">
                {#each tabs as tab}
                    <button
                        type="button"
                        class:active={activeTab === tab.id}
                        class="tab-button"
                        role="tab"
                        aria-selected={activeTab === tab.id}
                        aria-controls={`${tab.id}-panel`}
                        on:click={() => void handleTabChange(tab.id)}
                    >
                        {tab.label}
                    </button>
                {/each}
            </div>
        </div>
    </nav>
</header>

<main>

    {#if infoMessage}
    <p class="text-rose-300 font-semibold my-3">{infoMessage}</p>
    {/if}

    {#if activeTab === 'current'}
        <div id="current-panel" role="tabpanel" aria-label="Aktueller Verbrauch">
            <div class="chart-container">
                {#if fillChartLoading}
                    <div class="chart-loading-overlay" aria-busy="true" aria-live="polite">
                        <div class="spinner"></div>
                    </div>
                {/if}
                <div id='fillChart' class='chartDiv'></div>
            </div>
        </div>
    {:else if activeTab === 'history'}
        <div id="history-panel" role="tabpanel" aria-label="Verlauf">
            <div class="controls-row my-10">
              <div class="control-field">
                <label for="from-picker" class="dark:text-white text-gray-600">From</label>
                <input
                  id="from-picker"
                  type="datetime-local"
                  class="bg-slate-900/80 border border-slate-700 text-slate-100 text-sm rounded-xl focus:ring-cyan-400 focus:border-cyan-400 block w-full p-2.5 h-10 my-5 shadow-md shadow-slate-950/30"
                  bind:value={dtFrom}
                />
              </div>

              <div class="control-field">
                <label for="until-picker" class="dark:text-white text-gray-600">Until</label>
                <input
                  id="until-picker"
                  type="datetime-local"
                  class = "bg-slate-900/80 border border-slate-700 text-slate-100 text-sm rounded-xl focus:ring-cyan-400 focus:border-cyan-400 block w-full p-2.5 h-10 my-5 shadow-md shadow-slate-950/30"
                  bind:value={dtUntil}
                />
              </div>

              <button
                type="button"
                class="refresh-button bg-cyan-500 hover:bg-cyan-400 disabled:bg-cyan-700 text-slate-950 font-semibold py-2 px-4 rounded-xl h-10 shadow-md shadow-cyan-950/30"
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
        </div>
    {:else if activeTab === 'evaluation'}
        <div id="eval-panel" role="tabpanel" aria-label="Auswertung">
            <div class="controls-row my-10">
              <div class="control-field">
                <label for="from-picker" class="dark:text-white text-gray-600">From</label>
                <input
                  id="from-picker"
                  type="datetime-local"
                  class="bg-slate-900/80 border border-slate-700 text-slate-100 text-sm rounded-xl focus:ring-cyan-400 focus:border-cyan-400 block w-full p-2.5 h-10 my-5 shadow-md shadow-slate-950/30"
                  bind:value={dtFrom}
                />
              </div>

              <div class="control-field">
                <label for="until-picker" class="dark:text-white text-gray-600">Until</label>
                <input
                  id="until-picker"
                  type="datetime-local"
                  class = "bg-slate-900/80 border border-slate-700 text-slate-100 text-sm rounded-xl focus:ring-cyan-400 focus:border-cyan-400 block w-full p-2.5 h-10 my-5 shadow-md shadow-slate-950/30"
                  bind:value={dtUntil}
                />
              </div>

              <button
                type="button"
                class="refresh-button bg-cyan-500 hover:bg-cyan-400 disabled:bg-cyan-700 text-slate-950 font-semibold py-2 px-4 rounded-xl h-10 shadow-md shadow-cyan-950/30"
                on:click={loadEvaluationChartsSection}
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
               <div class="chart-header-row">
                   <h3 class="chart-section-title">Steigung der Zyklen</h3>
               </div>
               <div id='cycleDeviationChart' class='chartDiv'></div>
            </div>

            <div class="aggregation-toolbar">
               <div class="aggregation-toggle-group" role="group" aria-label="Aggregation">
                 {#each cycleAggregationOptions as option}
                   <button
                     type="button"
                     class:active={cycleAggregation === option.value}
                     class="aggregation-button"
                     on:click={() => {
                       cycleAggregation = option.value;
                       void loadEvaluationChartsSection();
                     }}
                   >
                     {option.label}
                   </button>
                 {/each}
               </div>
            </div>

            <div class="chart-container">
               {#if timeChartsLoading}
                  <div class="chart-loading-overlay" aria-busy="true" aria-live="polite">
                      <div class="spinner"></div>
                  </div>
               {/if}
               <div id='dailyCycleCountChart' class='chartDiv'></div>
            </div>
            <div class="chart-container">
               {#if timeChartsLoading}
                  <div class="chart-loading-overlay" aria-busy="true" aria-live="polite">
                      <div class="spinner"></div>
                  </div>
               {/if}
               <div id='intervalHistChart' class='chartDiv'></div>
            </div>
        </div>
    {/if}
</main>

<style>
    main {
        text-align: center;
        overflow-x: hidden;
    }

    .chart-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: 0 0 0.75rem;
        padding: 0 0.25rem;
        width: 100%;
        box-sizing: border-box;
    }

    .chart-section-title {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: #e2e8f0;
    }

    .aggregation-toolbar {
        display: flex;
        justify-content: flex-end;
        margin: -0.5rem 0 1rem;
        padding: 0 0.25rem;
        width: 100%;
        box-sizing: border-box;
    }

    .aggregation-toggle-group {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem;
        border-radius: 0.75rem;
        border: 1px solid rgba(148, 163, 184, 0.35);
        background: rgba(15, 23, 42, 0.7);
        box-shadow: 0 4px 12px rgba(2, 6, 23, 0.2);
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .aggregation-button {
        border: 1px solid transparent;
        background: transparent;
        color: #cbd5e1;
        border-radius: 0.65rem;
        padding: 0.45rem 0.8rem;
        min-width: 4.25rem;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
    }

    .aggregation-button.active {
        background: rgba(34, 211, 238, 0.18);
        border-color: rgba(34, 211, 238, 0.65);
        color: #a5f3fc;
        box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.15);
    }

  label {
    font-weight: bold;
    margin-bottom: 0.25rem;
  }

.topbar {
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 0 0 0.5rem;
  }

  .navbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      width: 100%;
      margin: 0;
      padding: 0.75rem 1rem;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(148, 163, 184, 0.35);
      border-left: none;
      border-right: none;
      box-shadow: 0 10px 20px rgba(2, 6, 23, 0.25);
      backdrop-filter: blur(8px);
      box-sizing: border-box;
  }

  .brand {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 0;
      flex-shrink: 0;
  }

  .brand-logo {
      display: block;
      max-height: 3.25rem;
      width: auto;
      object-fit: contain;
  }

  .nav-controls {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 1rem;
      flex: 1;
      flex-wrap: wrap;
      min-width: 0;
  }

  .station-control {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      min-width: 0;
  }

  .station-label {
      font-weight: 700;
      color: #e2e8f0;
      white-space: nowrap;
  }

  .mp-select {
      min-width: 12rem;
      max-width: 100%;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(148, 163, 184, 0.4);
      color: #f8fafc;
      border-radius: 0.85rem;
      padding: 0.65rem 1rem;
      font-size: 0.875rem;
      box-shadow: 0 8px 20px rgba(2, 6, 23, 0.2);
      flex: 1 1 12rem;
  }

  .tab-list {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin: 0;
      padding: 0;
  }

  .tab-button {
      border: 1px solid rgba(148, 163, 184, 0.3);
      border-bottom: none;
      background: rgba(15, 23, 42, 0.75);
      color: #e2e8f0;
      border-radius: 0.75rem 0.75rem 0 0;
      padding: 0.65rem 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.15);
      white-space: nowrap;
  }

  .tab-button.active {
      background: linear-gradient(180deg, rgba(34, 211, 238, 0.22), rgba(15, 23, 42, 0.96));
      color: #f8fafc;
      border-color: rgba(34, 211, 238, 0.7);
      box-shadow: 0 -2px 12px rgba(34, 211, 238, 0.12);
  }

  @media (max-width: 760px) {
      .brand {
          display: none;
      }

      .navbar {
          padding-top: 0.5rem;
          padding-bottom: 0.5rem;
      }

      .nav-controls {
          justify-content: space-between;
      }

      .station-control {
          flex: 1 1 12rem;
      }

      .chart-header-row,
      .aggregation-toolbar,
      .controls-row {
          flex-direction: column;
          align-items: stretch;
      }

      .aggregation-toggle-group {
          width: 100%;
          justify-content: center;
      }

      .chart-container,
      .chartDiv {
          min-width: 0;
          max-width: 100%;
      }
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

  @media (max-width: 760px) {
      .controls-row {
          display: flex;
          flex-direction: column;
          align-items: stretch;
          gap: 0.5rem;
      }

      .control-field {
          width: 100%;
          flex: 1 1 auto;
          display: flex;
          align-items: center;
          gap: 0.75rem;
      }

      .control-field label {
          min-width: 3.5rem;
          margin-bottom: 0;
      }

      .control-field input {
          flex: 1;
      }

      .refresh-button {
          width: 100%;
          margin-bottom: 0.75rem;
      }
  }

  .chart-container {
    position: relative;
    width: 100%;
    min-height: 600px;
    margin-bottom: 1.5rem;
    background: rgba(15, 23, 42, 0.35);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 1rem;
    overflow: hidden;
    box-shadow: 0 12px 24px rgba(2, 6, 23, 0.25);
    display: block;
    box-sizing: border-box;
  }

  .chart-container + .chart-container {
    margin-top: 1.25rem;
  }

  .chartDiv {
    width: 100%;
    height: 600px;
    z-index: 0;
    max-width: 100%;
    box-sizing: border-box;
  }

  .chart-loading-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(15, 23, 42, 0.6);
    z-index: 5;
  }

  .spinner {
    width: 3rem;
    height: 3rem;
    border: 0.35rem solid rgba(34, 211, 238, 0.2);
    border-top-color: #22d3ee;
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

</style>
