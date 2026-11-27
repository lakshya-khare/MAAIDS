import time

class ActuatorController:
    def __init__(self):
        self.water_pump = False
        self.sprayer_valve = True
        self.last_operation = "System initialized in standby mode"

    def set_pump(self, state: bool):
        self.water_pump = state
        self.last_operation = f"Water Pump switched {'ON' if state else 'OFF'}"
        return self.get_state()

    def set_sprayer(self, state: bool):
        self.sprayer_valve = state
        self.last_operation = f"Precision Sprayer Valve switched {'ON' if state else 'OFF'}"
        return self.get_state()

    def apply_auto_action(self, action, score):
        if action == "SPRAY":
            self.sprayer_valve = True
            self.last_operation = f"High priority intervention (Score: {score:.2f}) - Sprayer ON"
        elif action == "ALERT":
            self.last_operation = f"Advisory alert recorded (Score: {score:.2f})"
        else:
            self.last_operation = f"Normal telemetry monitoring (Score: {score:.2f})"

    def get_state(self):
        return {
            "water_pump": self.water_pump,
            "sprayer_valve": self.sprayer_valve,
            "last_operation": self.last_operation
        }

actuator = ActuatorController()
