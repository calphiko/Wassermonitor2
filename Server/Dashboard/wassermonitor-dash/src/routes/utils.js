/**
 * Utility functions for date formatting, chart initialization, and configuration fetching.
 *
 * This module contains helper functions to:
 * - Format dates for input fields or ISO strings.
 * - Retrieve references to chart instances in the DOM.
 * - Fetch chart configuration data from a remote source.
 *
 * These utilities are designed to streamline operations involving dates, charts, and configurations.
 *
 * @module utils
 */

/**
 * Formats a JavaScript Date object into a string suitable for input fields.
 *
 * Converts a Date object into a string formatted as `YYYY-MM-DDTHH:mm`,
 * which is compatible with HTML datetime-local input fields.
 *
 * @function formatDateForInput
 * @param {Date} date - The JavaScript Date object to format.
 * @returns {string} - A formatted date string in the form `YYYY-MM-DDTHH:mm`.
 */
export function formatDateForInput(date) {
   const year = date.getFullYear();
   const month = String(date.getMonth() + 1).padStart(2, "0");
   const day = String(date.getDate()).padStart(2, "0");
   const hours = String(date.getHours()).padStart(2, "0");
   const minutes = String(date.getMinutes()).padStart(2, "0");
   return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Converts a date string into an ISO 8601 formatted string.
 *
 * This function takes a date string, parses it into a JavaScript Date object,
 * and converts it to an ISO 8601 string with a timezone offset of `+00:00`.
 *
 * @function formatDateForISO
 * @param {string} dateString - A date string to convert.
 * @returns {string} - An ISO 8601 formatted date string.
 */
export function formatDateForISO(dateString) {
    return new Date(dateString).toISOString().replace("Z","+00:00"); // ISO-Format sicherstellen
 }

/**
 * Retrieves references to chart instances in the DOM.
 *
 * This asynchronous function finds and returns DOM elements corresponding
 * to specific charts identified by their IDs.
 *
 * @async
 * @function getChartIntances
 * @returns {Promise<Object>} - A dictionary containing DOM elements for charts:
 *                               - `fillChart`: Element for the fill chart.
 *                               - `timeChart`: Element for the time chart.
 *                               - `derivChart`: Element for the derivative chart.
 */
export async function getChartIntances() {
    let chartInstances = {
         'fillChart': document.getElementById('fillChart'),
         'timeChart': document.getElementById('TimeChart'),
         'derivChart':  document.getElementById('derivChart')
        };
    return chartInstances;
}

/**
 * Fetches chart configuration data from the JSON.
 *
 * This asynchronous function sends a GET request to the provided URL
 * and retrieves JSON data representing the chart configuration.
 *
 * @async
 * @function fetchChartConfig
 * @param {string} url - The URL to fetch the chart configuration from.
 * @returns {Promise<Object|null>} - The chart configuration as a JSON object,
 *                                    or null if an error occurs.
 * @throws {Error} If the response is invalid or the fetch fails.
 */
export async function fetchChartConfig(url) {
    try {
        const response_cConfig = await fetch(url);
        if (!response_cConfig.ok) {
            throw new Error ("No response from cConfig-JSON");
        }
        const cConfig = await response_cConfig.json();
        return cConfig;
        //console.log('Color Gradients:',colorGradients);
    } catch(error) {
        console.error('Error while fetching colors!',error);
    }
}