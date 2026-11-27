import random
import time

class SensorSimulator:
    def __init__(self):
        self.scenario = "blight"  # default to match demo report snapshot if desired, or normal
        self.state = {
            "temp": 26.2,
            "humidity": 98.0,
            "soil_moisture": 74.5,
            "light_lux": 204.0,
            "soil_ph": 6.17
        }
        self.last_tick = time.time()

    def set_scenario(self, scenario_name):
        valid = {"normal", "drought", "blight", "ph_stress"}
        if scenario_name in valid:
            self.scenario = scenario_name

    def tick(self):
        now = time.time()
        dt = min(now - self.last_tick, 5.0)
        self.last_tick = now

        targets = {
            "normal": {
                "temp": 24.5, "humidity": 65.0, "soil_moisture": 68.0,
                "light_lux": 450.0, "soil_ph": 6.5
            },
            "drought": {
                "temp": 36.5, "humidity": 28.0, "soil_moisture": 22.0,
                "light_lux": 750.0, "soil_ph": 6.9
            },
            "blight": {
                "temp": 26.2, "humidity": 98.0, "soil_moisture": 74.5,
                "light_lux": 204.0, "soil_ph": 6.17
            },
            "ph_stress": {
                "temp": 25.0, "humidity": 60.0, "soil_moisture": 62.0,
                "light_lux": 380.0, "soil_ph": 4.85
            }
        }[self.scenario]

        # Smooth drift towards scenario target with realistic sensor noise
        for key in self.state:
            drift = (targets[key] - self.state[key]) * 0.15
            noise = random.uniform(-0.1, 0.1)
            if key == "light_lux":
                noise *= 3.0
            elif key == "soil_ph":
                noise *= 0.02

            self.state[key] = round(self.state[key] + drift + noise, 2)

        return self.get_readings()

    def get_readings(self):
        return {
            "temperature": round(self.state["temp"], 1),
            "humidity": round(self.state["humidity"], 1),
            "soil_moisture": round(self.state["soil_moisture"], 1),
            "light_lux": int(self.state["light_lux"]),
            "soil_ph": round(self.state["soil_ph"], 2),
            "scenario": self.scenario
        }

# Global instance for app lifecycle
simulator = SensorSimulator()

def read_sensor_data():
    """Returns telemetry data. Points to simulator now; swap here for real hardware reads."""
    return simulator.tick()
