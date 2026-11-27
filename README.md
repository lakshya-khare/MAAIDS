# MDAAIS: Multi-Modal Detection & Adaptive Agricultural Intelligence System

Autonomous precision agriculture framework integrating visual leaf disease detection, weed identification, environmental telemetry sensing, and adaptive decision fusion.

## Quickstart

Run the self-check verification:
```bash
python tests/test_core.py
```

Start the application:
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Features

- **Realistic Telemetry Simulation**: Natural sensor drift across 4 distinct scenarios (`Normal`, `Drought`, `High Blight`, `Soil pH Stress`).
- **Edge Vision Inference**: Multi-class leaf disease detection (`Healthy`, `Early Blight`, `Yellow Leaf Curl`) and YOLOv5 weed detection.
- **Adaptive Decision Fusion Engine**: Composite score formula with threshold action routing (`SPRAY` $\ge 0.60$, `ALERT` $\ge 0.40$, `MONITOR` $< 0.40$) and dynamic weight calibration.
- **Actuator Automation**: Relay and sprayer valve controls driven by fusion engine decisions.
- **SQLite3 Local Persistence**: Embedded database for telemetry history, detections, and action logs.
