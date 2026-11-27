from core.db import get_weights, set_weights, log_action

class DecisionFusionEngine:
    def __init__(self):
        self.weights = get_weights()

    def refresh_weights(self):
        self.weights = get_weights()

    def compute_env_risk(self, telemetry):
        temp = telemetry.get("temperature", 25.0)
        hum = telemetry.get("humidity", 60.0)
        moisture = telemetry.get("soil_moisture", 60.0)
        ph = telemetry.get("soil_ph", 6.5)

        risk = 0.1

        # Blight condition: high humidity and warm temperature
        if hum > 85 and 18 <= temp <= 30:
            risk += 0.55
        elif hum > 75:
            risk += 0.25

        # Drought stress
        if moisture < 30 and temp > 32:
            risk += 0.35

        # Soil pH stress (optimal 6.0 - 7.0)
        if ph < 5.5 or ph > 7.5:
            risk += 0.20

        return min(round(risk, 2), 1.0)

    def compute_temporal_risk(self, telemetry, env_risk):
        # Rolling trend prediction: elevated risk if high humidity persists in shaded conditions
        light = telemetry.get("light_lux", 400)
        if env_risk > 0.5 and light < 250:
            return min(round(env_risk * 1.1, 2), 1.0)
        return round(env_risk * 0.75, 2)

    def evaluate(self, telemetry, vision_result):
        self.refresh_weights()

        d_score = vision_result.get("disease_score", 0.0)
        w_score = vision_result.get("weed_score", 0.0)
        e_score = self.compute_env_risk(telemetry)
        t_score = self.compute_temporal_risk(telemetry, e_score)

        wd = self.weights["disease"]
        ww = self.weights["weed"]
        we = self.weights["env"]
        wt = self.weights["temporal"]

        composite = (wd * d_score) + (ww * w_score) + (we * e_score) + (wt * t_score)
        composite = round(composite, 2)

        if composite >= 0.60:
            action = "SPRAY"
            reason = "High composite risk. Precision spraying and alert triggered."
        elif composite >= 0.40:
            action = "ALERT"
            reason = "Elevated risk detected. Advisory notice dispatched."
        else:
            action = "MONITOR"
            reason = "Parameters within safe boundaries. Standard monitoring active."

        return {
            "composite_score": composite,
            "action": action,
            "reason": reason,
            "scores": {
                "disease": d_score,
                "weed": w_score,
                "env": e_score,
                "temporal": t_score
            },
            "weights": {
                "disease": int(wd * 100),
                "weed": int(ww * 100),
                "env": int(we * 100),
                "temporal": int(wt * 100)
            }
        }

    def calibrate(self, model_key):
        w = get_weights()
        if model_key in w:
            # Boost the rewarded model weight by 0.05 and re-normalize
            w[model_key] += 0.05
            set_weights(w["disease"], w["weed"], w["env"], w["temporal"])
            self.refresh_weights()
        return self.weights

fusion_engine = DecisionFusionEngine()
