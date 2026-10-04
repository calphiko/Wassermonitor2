import { formatDateForISO } from './utils';
import { processRawTimeSeries } from './timeProcessor';


/**
 * Fetches the list of available measurement points from the API.
 *
 * This asynchronous function sends a POST request to the API to retrieve
 * a list of available measurement points. The response data is parsed and returned.
 *
 * @async
 * @function getAvailableMeasPointsFromApi
 * @param {string} apiUrl - The base URL of the API.
 * @returns {Promise<Object[]|null>} - Returns an array of available measurement points,
 *                                     or null if an error occurs.
 * @throws {Error} If the network response is not valid.
 */
export async function getAvailableMeasPointsFromApi(apiUrl) {
    try {
        const response = await fetch(apiUrl.concat('get_available_meas_points/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
        });
        if (!response.ok) {
            throw new Error("Invalid Network response!");
        }
        let mPs = await response.json();
        if (typeof mPs === 'string') {
            mPs = JSON.parse(mPs);
        }
        //console.log('Available Meas Points fetched:', JSON.stringify(mPs,null,2));
        const output = Object.entries(mPs).map(([key, values]) => {
            return {'value':key, 'label':`${key} ${values.join(" ")}`};
        });
        return output
    } catch (error) {
        console.error('Error while fetching measurement points from API:',error);
        return null;
    }
}

/**
 * Fetches time-series data from the API within a specified date range.
 *
 * This asynchronous function sends a POST request to the API to retrieve
 * time-series data for a specific measurement point within a defined time range.
 * The date range is passed as parameters, and the response data is processed and returned.
 *
 * @async
 * @function loadTimeDataFromAPI
 * @param {string} dtFrom - The start date in ISO format.
 * @param {string} dtUntil - The end date in ISO format.
 * @param {Object} cConfig - Configuration object containing the API URL.
 * @param {string} mpName - Name of the measurement point to fetch data for.
 * @returns {Promise<Object|null>} - Returns the parsed time-series data for the measurement point,
 *                                    or null if an error occurs.
 * @throws {Error} If the network response is not valid.
 */

export async function loadTimeDataFromAPI(apiUrl, dtFrom, dtUntil, mpName) {
    try {
        const rawData = await loadRawTimeDataFromAPI(apiUrl, dtFrom, dtUntil, mpName);
        if (!rawData || typeof rawData !== 'object') {
            return null;
        }

        const processed = await processRawTimeSeries(rawData, mpName);
        if (!Array.isArray(processed) || processed.length === 0) {
            return null;
        }
        return processed;
    } catch (error) {
        console.error('Error while fetching and processing time data in the browser:', error);
        return null;
    }
}

/**
 * Fetches raw time-series rows from the API within a specified date range.
 *
 * @async
 * @function loadRawTimeDataFromAPI
 * @param {string} apiUrl - The base API URL.
 * @param {string} dtFrom - Start datetime string.
 * @param {string} dtUntil - End datetime string.
 * @param {string} mpName - Measurement point name.
 * @returns {Promise<Record<string, Array<Object>>|null>}
 */
export async function loadRawTimeDataFromAPI(apiUrl, dtFrom, dtUntil, mpName) {
    const startedAt = performance.now();
    const requestMeta = { apiUrl, dtFrom, dtUntil, mpName };
    console.log('[API] loadRawTimeDataFromAPI start', requestMeta);

    try {
        const response = await fetch(apiUrl.concat('get/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(
                {
                    'dt_begin': formatDateForISO(dtFrom),
                    'dt_end': formatDateForISO(dtUntil),
                    'mp_name': mpName,
                }
            ),
        });
        if (!response.ok) {
            throw new Error("Invalid Network response!");
        }
        let data = await response.json();
        if (typeof data === 'string') {
            data = JSON.parse(data);
        }
        const elapsedMs = Math.round(performance.now() - startedAt);
        console.log('[API] loadRawTimeDataFromAPI ready in', elapsedMs, 'ms', { rows: Array.isArray(data?.[mpName]) ? data[mpName].reduce((sum, sensor) => sum + (Array.isArray(sensor?.rows) ? sensor.rows.length : 0), 0) : 'n/a' });
        return data;
    } catch (error) {
        const elapsedMs = Math.round(performance.now() - startedAt);
        console.error('[API] loadRawTimeDataFromAPI failed after', elapsedMs, 'ms', error);
        return null;
    }
}

export async function loadMeasurementStdDevFromAPI(apiUrl, dtFrom, dtUntil, mpName) {
    const startedAt = performance.now();
    const requestMeta = { apiUrl, dtFrom, dtUntil, mpName };
    console.log('[API] loadMeasurementStdDevFromAPI start', requestMeta);

    try {
        const response = await fetch(apiUrl.concat('get_stddev/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'dt_begin': formatDateForISO(dtFrom),
                'dt_end': formatDateForISO(dtUntil),
                'mp_name': mpName,
            }),
        });
        if (!response.ok) {
            throw new Error("Invalid Network response!");
        }
        let data = await response.json();
        if (typeof data === 'string') {
            data = JSON.parse(data);
        }
        const elapsedMs = Math.round(performance.now() - startedAt);
        console.log('[API] loadMeasurementStdDevFromAPI ready in', elapsedMs, 'ms', { rows: Array.isArray(data?.[mpName]) ? data[mpName].reduce((sum, sensor) => sum + (Array.isArray(sensor?.rows) ? sensor.rows.length : 0), 0) : 'n/a' });
        return data;
    } catch (error) {
        const elapsedMs = Math.round(performance.now() - startedAt);
        console.error('[API] loadMeasurementStdDevFromAPI failed after', elapsedMs, 'ms', error);
        return null;
    }
}


/**
 * Fetches the latest fill data from the API.
 *
 * This asynchronous function sends a POST request to the API to retrieve
 * the latest fill data. It also initializes dropdown options for measurement
 * point selection based on the response.
 *
 * @async
 * @function loadFillDataFromAPI
 * @param {Object} cConfig - Configuration object containing the API URL.
 * @returns {Promise<Object|null>} - Returns the parsed fill data for the selected
 *                                    measurement point, or null if an error occurs.
 * @throws {Error} If the network response is not valid.
 */
export async function loadFillDataFromAPI (apiUrl, mpName) {
        try {
            const response = await fetch(apiUrl.concat('get_latest/'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error("Invalid Network response!");
            }
            let data_f = await response.json();
            if (typeof data_f === 'string') {
                data_f = JSON.parse(data_f);
            }
            //console.log('Data fetched:', JSON.stringify(data_f,null,2));
            const mpNameOptions = Object.keys(data_f);
            const mPN = mpName || mpNameOptions[0];
            const data_fill = data_f[mPN];
            return data_fill
        } catch (error) {
            console.error('Error while fetching data from API:',error);
            return null;
        }

    }