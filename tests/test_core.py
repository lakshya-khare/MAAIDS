import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import init_db, log_telemetry, get_recent_telemetry, get_weights, set_weights
from core.simulator import simulator
from core.detector import detector
from core.fusion import fusion_engine
from core.actuator import actuator

def test_pipeline():
    init_db()

    # 1. Weights and normalization
    set_weights(0.40, 0.20, 0.25, 0.15)
    w = get_weights()
    assert round(w["disease"] + w["weed"] + w["env"] + w["temporal"], 2) == 1.0

    # 2. Simulator & Scenarios
    simulator.set_scenario("drought")
    d_data = simulator.tick()
    assert d_data["scenario"] == "drought"

    simulator.set_scenario("blight")
    b_data = simulator.tick()
    assert b_data["scenario"] == "blight"

    # 3. Vision Detection
    v_blight = detector.set_active_leaf("early_blight")
    assert v_blight["disease_confidence"] > 90
    assert not v_blight["weeds_found"]

    v_weed = detector.set_active_leaf("weed_infest")
    assert v_weed["weeds_found"] is True

    # 4. Fusion Engine calculation & thresholds
    # High risk test (blight + blight scenario should trigger SPRAY)
    eval_spray = fusion_engine.evaluate(b_data, v_blight)
    assert eval_spray["action"] in ("SPRAY", "ALERT")
    assert eval_spray["composite_score"] > 0.40

    # Healthy test (healthy leaf + normal conditions should MONITOR)
    simulator.set_scenario("normal")
    n_data = simulator.tick()
    v_healthy = detector.set_active_leaf("healthy")
    eval_monitor = fusion_engine.evaluate(n_data, v_healthy)
    assert eval_monitor["action"] == "MONITOR"
    assert eval_monitor["composite_score"] < 0.40

    # 5. Actuator control
    state = actuator.set_pump(True)
    assert state["water_pump"] is True
    state = actuator.set_pump(False)
    assert state["water_pump"] is False

    # 6. Weight calibration adjustment
    initial_d = get_weights()["disease"]
    fusion_engine.calibrate("disease")
    updated_d = get_weights()["disease"]
    assert updated_d >= initial_d

    print("ALL RUNNABLE SELF-CHECKS PASSED.")

if __name__ == "__main__":
    test_pipeline()
