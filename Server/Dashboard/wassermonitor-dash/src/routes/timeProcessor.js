import initTimeProcessor, { transform_time_data } from '../lib/rust-time-processor/pkg/time_processor.js';

/** @type {Promise<void> | undefined} */
let wasmInitPromise;

async function ensureWasmReady() {
    if (!wasmInitPromise) {
        wasmInitPromise = initTimeProcessor();
    }
    await wasmInitPromise;
}

/**
 * @param {Record<string, Array<{sensorID: string, rows: Array<Object>}>> | null | undefined} rawDataByMp
 * @param {string} mpName
 * @returns {Promise<Array<Object>>}
 */
export async function processRawTimeSeries(rawDataByMp, mpName) {
    const mpRows = rawDataByMp?.[mpName];
    if (!Array.isArray(mpRows)) {
        return [];
    }
    await ensureWasmReady();
    return transform_time_data(mpRows);
}
