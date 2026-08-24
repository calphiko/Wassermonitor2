use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

#[derive(Deserialize)]
struct RawSensor {
    #[serde(rename = "sensorID")]
    sensor_id: String,
    rows: Vec<RawPoint>,
}

#[derive(Deserialize)]
struct RawPoint {
    timestamp: String,
    meas_val: f64,
    tank_height: f64,
    max_val: f64,
    warn: f64,
    alarm: f64,
}

#[derive(Serialize)]
struct ProcessedSensor {
    #[serde(rename = "sensorID")]
    sensor_id: String,
    values: Vec<ValuePoint>,
    deriv: Vec<DerivPoint>,
    y_max: f64,
    deriv_y_max: f64,
    deriv_y_min: f64,
}

#[derive(Serialize)]
struct ValuePoint {
    timestamp: String,
    value: f64,
    tank_height: f64,
    max_val: f64,
    warn: f64,
    alarm: f64,
}

#[derive(Serialize)]
struct DerivPoint {
    timestamp: String,
    value: f64,
    value_10: f64,
    peaks_pos: Option<f64>,
    peaks_neg: Option<f64>,
}

fn round_1(v: f64) -> f64 {
    (v * 10.0).round() / 10.0
}

fn parse_hours(ts: &str) -> Option<f64> {
    DateTime::parse_from_rfc3339(ts)
        .ok()
        .map(|dt| dt.with_timezone(&Utc).timestamp_millis() as f64 / 3_600_000.0)
}

fn gradient(values: &[f64]) -> Vec<f64> {
    let n = values.len();
    if n == 0 {
        return Vec::new();
    }
    if n == 1 {
        return vec![0.0];
    }
    let mut out = vec![0.0; n];
    out[0] = values[1] - values[0];
    for i in 1..(n - 1) {
        out[i] = (values[i + 1] - values[i - 1]) / 2.0;
    }
    out[n - 1] = values[n - 1] - values[n - 2];
    out
}

fn rolling_avg_10(values: &[f64]) -> Vec<f64> {
    if values.len() <= 100 {
        return vec![0.0; values.len()];
    }
    let mut out = Vec::with_capacity(values.len());
    let mut sum = 0.0;
    for i in 0..values.len() {
        sum += values[i];
        if i >= 10 {
            sum -= values[i - 10];
            out.push(sum / 10.0);
        } else {
            out.push(sum / (i as f64 + 1.0));
        }
    }
    out
}

fn local_peaks(deriv: &[f64], deriv_10: &[f64]) -> (Vec<Option<f64>>, Vec<Option<f64>>) {
    let n = deriv_10.len();
    let mut pos = vec![None; n];
    let mut neg = vec![None; n];
    if n < 3 {
        return (pos, neg);
    }
    for i in 1..(n - 1) {
        if deriv_10[i] > 10.0 && deriv_10[i] > deriv_10[i - 1] && deriv_10[i] > deriv_10[i + 1] {
            pos[i] = Some(deriv_10[i]);
        }
        if deriv_10[i] < -10.0 && deriv_10[i] < deriv_10[i - 1] && deriv_10[i] < deriv_10[i + 1] {
            neg[i] = Some(deriv_10[i]);
        }
    }
    (pos, neg)
}

#[wasm_bindgen]
pub fn transform_time_data(raw: JsValue) -> Result<JsValue, JsValue> {
    let mut sensors: Vec<RawSensor> = serde_wasm_bindgen::from_value(raw)
        .map_err(|err| JsValue::from_str(&format!("Invalid raw payload: {err}")))?;

    let mut out = Vec::with_capacity(sensors.len());
    for sensor in sensors.iter_mut() {
        sensor.rows.sort_by(|a, b| a.timestamp.cmp(&b.timestamp));
        if sensor.rows.is_empty() {
            continue;
        }

        let meas_vals: Vec<f64> = sensor.rows.iter().map(|r| r.meas_val).collect();
        let times_h: Vec<f64> = sensor
            .rows
            .iter()
            .enumerate()
            .map(|(i, r)| parse_hours(&r.timestamp).unwrap_or(i as f64))
            .collect();
        let slope_val = gradient(&meas_vals);
        let slope_time = gradient(&times_h);
        let deriv: Vec<f64> = slope_val
            .iter()
            .zip(slope_time.iter())
            .map(|(sv, st)| if *st == 0.0 { 0.0 } else { -sv / st })
            .collect();
        let deriv_10 = rolling_avg_10(&deriv);
        let (peaks_pos, peaks_neg) = local_peaks(&deriv, &deriv_10);

        let values: Vec<ValuePoint> = sensor
            .rows
            .iter()
            .map(|r| ValuePoint {
                timestamp: r.timestamp.clone(),
                value: round_1(r.tank_height - r.meas_val),
                tank_height: r.tank_height,
                max_val: r.max_val,
                warn: r.warn,
                alarm: r.alarm,
            })
            .collect();

        let deriv_out: Vec<DerivPoint> = sensor
            .rows
            .iter()
            .enumerate()
            .map(|(i, r)| DerivPoint {
                timestamp: r.timestamp.clone(),
                value: deriv[i],
                value_10: deriv_10[i],
                peaks_pos: peaks_pos[i],
                peaks_neg: peaks_neg[i],
            })
            .collect();

        let y_max = sensor
            .rows
            .iter()
            .map(|r| r.max_val)
            .fold(f64::MIN, f64::max)
            + 10.0;
        let deriv_max = deriv_10.iter().copied().fold(f64::MIN, f64::max).round() + 10.0;
        let deriv_min = deriv_10.iter().copied().fold(f64::MAX, f64::min).round() - 10.0;

        out.push(ProcessedSensor {
            sensor_id: sensor.sensor_id.clone(),
            values,
            deriv: deriv_out,
            y_max,
            deriv_y_max: deriv_max,
            deriv_y_min: deriv_min,
        });
    }

    serde_wasm_bindgen::to_value(&out).map_err(|err| JsValue::from_str(&format!("Failed to serialize output: {err}")))
}
