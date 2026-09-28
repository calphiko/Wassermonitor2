use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
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
    evaluation: EvaluationData,
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

#[derive(Serialize)]
struct EvaluationData {
    cycle_deviation: CycleDeviationData,
    daily_cycle_counts: Vec<DailyCycleCount>,
    interval_histogram: Vec<HistogramBin>,
}

#[derive(Serialize)]
struct CycleDeviationData {
    fill_mean_slope_abs: f64,
    drain_mean_slope_abs: f64,
    cycles: Vec<CycleDeviationPoint>,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum CycleType {
    Fill,
    Drain,
}

#[derive(Serialize)]
struct CycleDeviationPoint {
    timestamp: String,
    cycle_type: String,
    mean_slope_abs: f64,
    deviation_abs: f64,
    deviation_pct: f64,
    duration_min: f64,
}

#[derive(Serialize)]
struct DailyCycleCount {
    day: String,
    fill_count: usize,
    drain_count: usize,
}

#[derive(Serialize)]
struct HistogramBin {
    label: String,
    count: usize,
}

fn round_1(v: f64) -> f64 {
    (v * 10.0).round() / 10.0
}

fn round_2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
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

fn average(values: &[f64]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    values.iter().sum::<f64>() / values.len() as f64
}

fn median(values: &[f64]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.total_cmp(b));
    let mid = sorted.len() / 2;
    if sorted.len() % 2 == 0 {
        (sorted[mid - 1] + sorted[mid]) / 2.0
    } else {
        sorted[mid]
    }
}

fn stddev(values: &[f64]) -> f64 {
    if values.len() < 2 {
        return 0.0;
    }
    let mean = average(values);
    let variance = values
        .iter()
        .map(|value| {
            let delta = *value - mean;
            delta * delta
        })
        .sum::<f64>()
        / values.len() as f64;
    variance.sqrt()
}

fn cycle_type_label(cycle_type: CycleType) -> String {
    match cycle_type {
        CycleType::Fill => "fill".to_string(),
        CycleType::Drain => "drain".to_string(),
    }
}

fn to_utc_datetime(ts: &str) -> Option<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(ts)
        .ok()
        .map(|dt| dt.with_timezone(&Utc))
}

fn centered_moving_average(values: &[f64], window: usize) -> Vec<f64> {
    if values.is_empty() || window <= 1 {
        return values.to_vec();
    }
    let half = window / 2;
    let mut out = vec![0.0; values.len()];
    for idx in 0..values.len() {
        let start = idx.saturating_sub(half);
        let end = (idx + half + 1).min(values.len());
        let slice = &values[start..end];
        let avg = average(slice);
        out[idx] = avg;
    }
    out
}

fn median_filter(values: &[f64], window: usize) -> Vec<f64> {
    if values.is_empty() || window <= 1 {
        return values.to_vec();
    }
    let half = window / 2;
    let mut out = vec![0.0; values.len()];
    for idx in 0..values.len() {
        let start = idx.saturating_sub(half);
        let end = (idx + half + 1).min(values.len());
        let mut window_values = values[start..end].to_vec();
        window_values.sort_by(|a, b| a.total_cmp(b));
        out[idx] = window_values[window_values.len() / 2];
    }
    out
}

fn percentile(values: &[f64], quantile: f64) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.total_cmp(b));
    let clamped = quantile.clamp(0.0, 1.0);
    let index = ((sorted.len() as f64 - 1.0) * clamped).round() as usize;
    sorted[index.min(sorted.len() - 1)]
}

fn build_evaluation_with_deriv(values: &[ValuePoint], _deriv: &[f64]) -> EvaluationData {
    struct RawCycle {
        cycle_type: CycleType,
        timestamp: String,
        mean_slope_abs: f64,
        duration_min: f64,
    }

    let empty = EvaluationData {
        cycle_deviation: CycleDeviationData {
            fill_mean_slope_abs: 0.0,
            drain_mean_slope_abs: 0.0,
            cycles: Vec::new(),
        },
        daily_cycle_counts: Vec::new(),
        interval_histogram: vec![
            HistogramBin { label: "0-5".to_string(), count: 0 },
            HistogramBin { label: "5-10".to_string(), count: 0 },
            HistogramBin { label: "10-15".to_string(), count: 0 },
            HistogramBin { label: "15-30".to_string(), count: 0 },
            HistogramBin { label: "30-60".to_string(), count: 0 },
            HistogramBin { label: ">60".to_string(), count: 0 },
        ],
    };

    if values.len() < 2 {
        return empty;
    }

    let mut times_h: Vec<f64> = values
        .iter()
        .enumerate()
        .map(|(idx, point)| {
            to_utc_datetime(&point.timestamp)
                .map(|dt| dt.timestamp_millis() as f64 / 3_600_000.0)
                .unwrap_or(idx as f64)
        })
        .collect();
    if times_h.len() != values.len() {
        return empty;
    }
    for idx in 1..times_h.len() {
        if times_h[idx] <= times_h[idx - 1] {
            times_h[idx] = times_h[idx - 1] + (1.0 / 60.0);
        }
    }

    let mut level_rate_signal: Vec<f64> = Vec::with_capacity(values.len());
    for idx in 0..values.len() {
        let value = values[idx].value;
        if idx == 0 {
            level_rate_signal.push(0.0);
            continue;
        }
        let previous_time = times_h[idx - 1];
        let current_time = times_h[idx];
        let delta_time_h = current_time - previous_time;
        let delta_level = value - values[idx - 1].value;
        let rate = if delta_time_h > 0.0 && delta_time_h.is_finite() {
            delta_level / delta_time_h
        } else {
            0.0
        };
        level_rate_signal.push(rate);
    }
    let slope_signal = centered_moving_average(&level_rate_signal, 7);
    if slope_signal.len() < 2 {
        return empty;
    }

    let neutral_floor = 0.06;
    let mut slope_abs: Vec<f64> = slope_signal
        .iter()
        .copied()
        .filter(|s| s.is_finite())
        .map(|s| s.abs())
        .filter(|s| *s > neutral_floor)
        .collect();
    if slope_abs.is_empty() {
        return empty;
    }
    slope_abs.sort_by(|a, b| a.total_cmp(b));
    let median_abs_slope = median(&slope_abs);
    let p90_abs_slope = percentile(&slope_abs, 0.9);
    let std_slope = stddev(&slope_abs);
    let threshold_hi = (median_abs_slope * 0.75)
        .max(std_slope * 0.5)
        .max(0.18)
        .max((p90_abs_slope * 0.28).min(0.75));
    let threshold_lo = (threshold_hi * 0.55).max(0.12);
    let near_zero_threshold = (threshold_lo * 0.5).max(neutral_floor);

    let mut raw_cycles: Vec<RawCycle> = Vec::new();
    let mut daily_counts: BTreeMap<String, (usize, usize)> = BTreeMap::new();

    // 1 = fill, -1 = drain, 0 = neutral
    let mut states = vec![0i8; slope_signal.len()];
    let mut prev_state = 0i8;
    for (idx, slope) in slope_signal.iter().enumerate() {
        let abs_slope = slope.abs();
        let next_state = if *slope >= threshold_hi {
            1
        } else if *slope <= -threshold_hi {
            -1
        } else if prev_state == 1 && *slope >= threshold_lo {
            1
        } else if prev_state == -1 && *slope <= -threshold_lo {
            -1
        } else if abs_slope <= near_zero_threshold {
            0
        } else {
            0
        };
        states[idx] = next_state;
        prev_state = next_state;
    }

    // Remove very short signed runs (noise bursts) without pushing transitions later.
    let min_run_points = 5usize;
    let mut run_start = 0usize;
    while run_start < states.len() {
        let run_state = states[run_start];
        let mut run_end = run_start + 1;
        while run_end < states.len() && states[run_end] == run_state {
            run_end += 1;
        }
        if run_state != 0 && (run_end - run_start) < min_run_points {
            let left_state = if run_start > 0 { states[run_start - 1] } else { 0 };
            let right_state = if run_end < states.len() { states[run_end] } else { 0 };
            let replacement = if left_state == right_state { left_state } else { 0 };
            for idx in run_start..run_end {
                states[idx] = replacement;
            }
        }
        run_start = run_end;
    }

    // Bridge only tiny neutral gaps between same-signed runs; do not extend the cycle start
    // beyond the true state transition. This preserves onset timing, unlike recursive smoothing.
    let max_neutral_gap = 3usize;
    let mut idx = 1usize;
    while idx + 1 < states.len() {
        if states[idx] != 0 {
            idx += 1;
            continue;
        }
        let gap_start = idx;
        while idx < states.len() && states[idx] == 0 {
            idx += 1;
        }
        let gap_end = idx;
        if gap_end - gap_start <= max_neutral_gap
            && gap_start > 0
            && gap_end < states.len()
            && states[gap_start - 1] != 0
            && states[gap_start - 1] == states[gap_end]
        {
            for fill_idx in gap_start..gap_end {
                states[fill_idx] = states[gap_start - 1];
            }
        }
    }

    // Recompute the sign-state sequence using hysteresis with separate thresholds.
    // The system must cross the high threshold to enter a cycle and stay above the lower threshold,
    // but very small slopes are explicitly treated as neutral to avoid overnight false positives.
    let mut hysteresis = vec![0i8; states.len()];
    let mut prev_hysteresis = 0i8;
    for (idx, slope) in slope_signal.iter().enumerate() {
        let abs_slope = slope.abs();
        let next_state = if *slope >= threshold_hi {
            1
        } else if *slope <= -threshold_hi {
            -1
        } else if prev_hysteresis == 1 && *slope >= threshold_lo {
            1
        } else if prev_hysteresis == -1 && *slope <= -threshold_lo {
            -1
        } else if abs_slope <= near_zero_threshold {
            0
        } else {
            0
        };
        hysteresis[idx] = next_state;
        prev_hysteresis = next_state;
    }

    // Drop any short sign runs that remain after hysteresis filtering.
    let mut run_start_h = 0usize;
    while run_start_h < hysteresis.len() {
        let run_state = hysteresis[run_start_h];
        let mut run_end_h = run_start_h + 1;
        while run_end_h < hysteresis.len() && hysteresis[run_end_h] == run_state {
            run_end_h += 1;
        }
        if run_state != 0 && (run_end_h - run_start_h) < min_run_points {
            let left_state = if run_start_h > 0 { hysteresis[run_start_h - 1] } else { 0 };
            let right_state = if run_end_h < hysteresis.len() { hysteresis[run_end_h] } else { 0 };
            let replacement = if left_state == right_state { left_state } else { 0 };
            for idx in run_start_h..run_end_h {
                hysteresis[idx] = replacement;
            }
        }
        run_start_h = run_end_h;
    }
    let states = hysteresis;

    let finalize_cycle = |cycle_type: CycleType, start_idx: usize, end_idx: usize, raw_cycles: &mut Vec<RawCycle>, daily_counts: &mut BTreeMap<String, (usize, usize)>| {
        if end_idx <= start_idx || end_idx >= values.len() || end_idx >= slope_signal.len() {
            return;
        }
        let point_count = end_idx - start_idx + 1;
        if point_count < min_run_points {
            return;
        }

        let start_dt = match to_utc_datetime(&values[start_idx].timestamp) {
            Some(dt) => dt,
            None => return,
        };
        let end_dt = match to_utc_datetime(&values[end_idx].timestamp) {
            Some(dt) => dt,
            None => return,
        };

        let duration_min = (end_dt.timestamp_millis() - start_dt.timestamp_millis()) as f64 / 60000.0;
        if !duration_min.is_finite() || duration_min < 15.0 {
            return;
        }

        let level_delta = values[end_idx].value - values[start_idx].value;
        let is_direction_ok = match cycle_type {
            CycleType::Fill => level_delta > 0.5,
            CycleType::Drain => level_delta < -0.5,
        };
        if !is_direction_ok {
            return;
        }

        let level_delta = values[end_idx].value - values[start_idx].value;
        let cycle_rate_cm_per_h = if duration_min > 0.0 {
            (level_delta.abs() / duration_min) * 60.0
        } else {
            0.0
        };
        let mean_slope_abs = cycle_rate_cm_per_h;
        if mean_slope_abs <= 0.0 || !mean_slope_abs.is_finite() {
            return;
        }

        let mid_idx = start_idx + point_count / 2;
        let mid_ts = values[mid_idx].timestamp.clone();
        let day = start_dt.format("%Y-%m-%d").to_string();

        raw_cycles.push(RawCycle {
            cycle_type,
            timestamp: mid_ts,
            mean_slope_abs: round_2(mean_slope_abs),
            duration_min: round_2(duration_min),
        });

        let entry = daily_counts.entry(day).or_insert((0usize, 0usize));
        match cycle_type {
            CycleType::Fill => entry.0 += 1,
            CycleType::Drain => entry.1 += 1,
        }
    };

    let mut current_type: Option<CycleType> = None;
    let mut cycle_start_idx: usize = 0;
    for (index, state) in states.iter().enumerate() {
        let mapped = match *state {
            1 => Some(CycleType::Fill),
            -1 => Some(CycleType::Drain),
            _ => None,
        };
        match (current_type, mapped) {
            (None, Some(next_type)) => {
                current_type = Some(next_type);
                cycle_start_idx = index;
            }
            (Some(active_type), Some(next_type)) if active_type != next_type => {
                finalize_cycle(active_type, cycle_start_idx, index.saturating_sub(1), &mut raw_cycles, &mut daily_counts);
                current_type = Some(next_type);
                cycle_start_idx = index;
            }
            (Some(active_type), None) => {
                finalize_cycle(active_type, cycle_start_idx, index.saturating_sub(1), &mut raw_cycles, &mut daily_counts);
                current_type = None;
            }
            _ => {}
        }
    }
    if !slope_signal.is_empty() {
        if let Some(active_type) = current_type {
            finalize_cycle(active_type, cycle_start_idx, slope_signal.len() - 1, &mut raw_cycles, &mut daily_counts);
        }
    }

    let fill_means: Vec<f64> = raw_cycles
        .iter()
        .filter(|cycle| cycle.cycle_type == CycleType::Fill)
        .map(|cycle| cycle.mean_slope_abs)
        .collect();
    let drain_means: Vec<f64> = raw_cycles
        .iter()
        .filter(|cycle| cycle.cycle_type == CycleType::Drain)
        .map(|cycle| cycle.mean_slope_abs)
        .collect();

    let fill_global = average(&fill_means);
    let drain_global = average(&drain_means);

    let cycles = raw_cycles
        .iter()
        .map(|cycle| {
            let type_global = if cycle.cycle_type == CycleType::Fill {
                fill_global
            } else {
                drain_global
            };
            let deviation_abs = cycle.mean_slope_abs - type_global;
            let deviation_pct = if type_global.abs() < 1e-6 {
                0.0
            } else {
                (cycle.mean_slope_abs / type_global - 1.0) * 100.0
            };

            CycleDeviationPoint {
                timestamp: cycle.timestamp.clone(),
                cycle_type: cycle_type_label(cycle.cycle_type),
                mean_slope_abs: round_2(cycle.mean_slope_abs),
                deviation_abs: round_2(deviation_abs),
                deviation_pct: round_2(deviation_pct),
                duration_min: cycle.duration_min,
            }
        })
        .collect::<Vec<CycleDeviationPoint>>();

    let daily_cycle_counts = daily_counts
        .iter()
        .map(|(day, (fill_count, drain_count))| DailyCycleCount {
            day: day.clone(),
            fill_count: *fill_count,
            drain_count: *drain_count,
        })
        .collect::<Vec<DailyCycleCount>>();

    let mut histogram_counts = [0usize; 6];
    for index in 1..values.len() {
        let prev_dt = match to_utc_datetime(&values[index - 1].timestamp) {
            Some(dt) => dt,
            None => continue,
        };
        let curr_dt = match to_utc_datetime(&values[index].timestamp) {
            Some(dt) => dt,
            None => continue,
        };
        let dt_min = (curr_dt.timestamp_millis() - prev_dt.timestamp_millis()) as f64 / 60000.0;
        if !dt_min.is_finite() || dt_min < 0.0 {
            continue;
        }
        if dt_min <= 5.0 {
            histogram_counts[0] += 1;
        } else if dt_min <= 10.0 {
            histogram_counts[1] += 1;
        } else if dt_min <= 15.0 {
            histogram_counts[2] += 1;
        } else if dt_min <= 30.0 {
            histogram_counts[3] += 1;
        } else if dt_min <= 60.0 {
            histogram_counts[4] += 1;
        } else {
            histogram_counts[5] += 1;
        }
    }
    let interval_histogram = vec![
        HistogramBin { label: "0-5".to_string(), count: histogram_counts[0] },
        HistogramBin { label: "5-10".to_string(), count: histogram_counts[1] },
        HistogramBin { label: "10-15".to_string(), count: histogram_counts[2] },
        HistogramBin { label: "15-30".to_string(), count: histogram_counts[3] },
        HistogramBin { label: "30-60".to_string(), count: histogram_counts[4] },
        HistogramBin { label: ">60".to_string(), count: histogram_counts[5] },
    ];

    EvaluationData {
        cycle_deviation: CycleDeviationData {
            fill_mean_slope_abs: round_2(fill_global),
            drain_mean_slope_abs: round_2(drain_global),
            cycles,
        },
        daily_cycle_counts,
        interval_histogram,
    }
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

fn local_peaks(_deriv: &[f64], deriv_10: &[f64]) -> (Vec<Option<f64>>, Vec<Option<f64>>) {
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
        let evaluation = build_evaluation_with_deriv(&values, &deriv);

        out.push(ProcessedSensor {
            sensor_id: sensor.sensor_id.clone(),
            values,
            deriv: deriv_out,
            y_max,
            deriv_y_max: deriv_max,
            deriv_y_min: deriv_min,
            evaluation,
        });
    }

    serde_wasm_bindgen::to_value(&out).map_err(|err| JsValue::from_str(&format!("Failed to serialize output: {err}")))
}
