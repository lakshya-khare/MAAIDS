import time
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from core.db import init_db, log_telemetry, get_recent_telemetry, log_action, get_recent_actions
from core.simulator import read_sensor_data, simulator
from core.detector import detector
from core.fusion import fusion_engine
from core.actuator import actuator

app = Flask(__name__)

# Pre-seed initial database state
init_db()
if not get_recent_telemetry(1):
    for _ in range(15):
        s = read_sensor_data()
        log_telemetry(s["temperature"], s["humidity"], s["soil_moisture"], s["light_lux"], s["soil_ph"], s["scenario"])
        time.sleep(0.01)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    sensor_data = read_sensor_data()
    log_telemetry(
        sensor_data["temperature"],
        sensor_data["humidity"],
        sensor_data["soil_moisture"],
        sensor_data["light_lux"],
        sensor_data["soil_ph"],
        sensor_data["scenario"]
    )

    vision = detector.get_active_inference()
    decision = fusion_engine.evaluate(sensor_data, vision)

    # Update actuator with automated decision rule
    actuator.apply_auto_action(decision["action"], decision["composite_score"])
    log_action(decision["action"], decision["composite_score"], decision["reason"])

    history = get_recent_telemetry(limit=25)
    action_history = get_recent_actions(limit=8)

    return jsonify({
        "status": "online",
        "current": sensor_data,
        "vision": vision,
        "fusion": decision,
        "actuators": actuator.get_state(),
        "history": history,
        "actions": action_history
    })

@app.route("/api/scenario", methods=["POST"])
def update_scenario():
    data = request.get_json(silent=True) or {}
    scen = data.get("scenario", "normal")
    simulator.set_scenario(scen)
    return jsonify({"success": True, "active_scenario": scen})

@app.route("/api/leaf", methods=["POST"])
def update_leaf():
    data = request.get_json(silent=True) or {}
    leaf_key = data.get("leaf", "yellow_curl")
    result = detector.set_active_leaf(leaf_key)
    return jsonify({"success": True, "vision": result})

@app.route("/api/actuators", methods=["POST"])
def toggle_actuator():
    data = request.get_json(silent=True) or {}
    device = data.get("device")
    state = bool(data.get("state", False))

    if device == "pump":
        state_dict = actuator.set_pump(state)
    elif device == "sprayer":
        state_dict = actuator.set_sprayer(state)
    else:
        return jsonify({"error": "Unknown actuator device"}), 400

    return jsonify({"success": True, "actuators": state_dict})

@app.route("/api/upload", methods=["POST"])
def upload_leaf():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = f"leaf_{int(time.time())}.jpg"
    filepath = Path(__file__).resolve().parent / "static" / "uploads" / filename
    file.save(filepath)

    web_url = f"/static/uploads/{filename}"
    result = detector.analyze_uploaded_image(filepath, web_url)
    return jsonify({"success": True, "vision": result})

@app.route("/api/calibrate", methods=["POST"])
def calibrate_weights():
    data = request.get_json(silent=True) or {}
    model_key = data.get("model")
    updated = fusion_engine.calibrate(model_key)
    return jsonify({"success": True, "weights": updated})

@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify({"actions": get_recent_actions(limit=20)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
