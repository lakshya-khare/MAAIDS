import cv2
import numpy as np
from PIL import Image

class VisionDetector:
    PRESETS = {
        "healthy": {
            "leaf_species": "Tomato Leaf (Solanum lycopersicum)",
            "disease_name": "Healthy Foliage (No Disease Detected)",
            "disease_score": 0.05,
            "disease_confidence": 97,
            "weeds_found": False,
            "weed_name": "None",
            "weed_score": 0.0,
            "weed_confidence": 0,
            "image": "/static/images/healthy.jpg"
        },
        "early_blight": {
            "leaf_species": "Tomato Leaf (Solanum lycopersicum)",
            "disease_name": "Tomato Early Blight (Alternaria solani)",
            "disease_score": 0.88,
            "disease_confidence": 94,
            "weeds_found": False,
            "weed_name": "None",
            "weed_score": 0.0,
            "weed_confidence": 0,
            "image": "/static/images/early_blight.jpg"
        },
        "yellow_curl": {
            "leaf_species": "Tomato Leaf (Solanum lycopersicum)",
            "disease_name": "Tomato Yellow Leaf Curl Virus (TYLCV)",
            "disease_score": 0.92,
            "disease_confidence": 92,
            "weeds_found": False,
            "weed_name": "None",
            "weed_score": 0.0,
            "weed_confidence": 0,
            "image": "/static/images/yellow_curl.jpg"
        },
        "weed_infest": {
            "leaf_species": "Crop Row & Invasive Weed (Chenopodium)",
            "disease_name": "Weed Infestation (Interfering Crop Growth)",
            "disease_score": 0.15,
            "disease_confidence": 89,
            "weeds_found": True,
            "weed_name": "Broadleaf Field Weed (Chenopodium album)",
            "weed_score": 0.86,
            "weed_confidence": 86,
            "image": "/static/images/weed_infest.jpg"
        }
    }

    def __init__(self):
        self.active_key = "yellow_curl"
        self.custom_inference = None

    def set_active_leaf(self, key):
        self.custom_inference = None
        if key in self.PRESETS:
            self.active_key = key
        return self.get_active_inference()

    def analyze_uploaded_image(self, file_path, web_url):
        img_bgr = cv2.imread(str(file_path))
        if img_bgr is None:
            return self.get_active_inference()

        h, w = img_bgr.shape[:2]
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        total_pixels = h * w

        # Plant masks
        green_mask = (hue >= 32) & (hue <= 88) & (sat >= 30)
        yellow_mask = (hue >= 18) & (hue < 32) & (sat >= 50) & (val >= 90)
        brown_mask = (hue < 18) & (sat >= 40) & (val <= 140)

        green_ratio = np.sum(green_mask) / total_pixels
        yellow_ratio = np.sum(yellow_mask) / total_pixels
        brown_ratio = np.sum(brown_mask) / total_pixels

        # Morphological shape estimation
        plant_mask = ((hue >= 10) & (hue <= 90) & (sat >= 30)).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        plant_mask = cv2.morphologyEx(plant_mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(plant_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sig_contours = [c for c in contours if cv2.contourArea(c) > 300]

        leaf_species = "Tomato Leaf (Solanum lycopersicum)"
        is_weed = False

        if len(sig_contours) >= 8:
            leaf_species = "Invasive Broadleaf Weed (Chenopodium / Amaranthus)"
            is_weed = True
        elif sig_contours:
            largest = max(sig_contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            perimeter = cv2.arcLength(largest, True)
            _, (cw, ch), _ = cv2.minAreaRect(largest) if len(largest) >= 5 else (0, (w, h), 0)
            aspect_ratio = max(cw, ch) / (min(cw, ch) + 1e-5)
            circularity = (4 * np.pi * area) / ((perimeter ** 2) + 1e-5) if perimeter > 0 else 0

            # Species classification rules based on agronomic morphology
            if aspect_ratio > 3.0:
                leaf_species = "Corn / Maize Blade (Zea mays)"
            elif circularity > 0.75:
                leaf_species = "Bell Pepper Leaf (Capsicum annuum)"
            else:
                leaf_species = "Tomato Leaf (Solanum lycopersicum)"

        # Pathology classification
        if is_weed:
            diagnosis = "Weed Infestation Detected (Competition Stress)"
            d_score = 0.20
            confidence = 88
        elif brown_ratio > 0.12:
            diagnosis = f"{leaf_species.split(' (')[0]} Yellow Leaf Curl Virus (TYLCV)"
            d_score = min(0.75 + (brown_ratio * 1.2), 0.95)
            confidence = int(d_score * 100)
        elif brown_ratio >= 0.02:
            diagnosis = f"{leaf_species.split(' (')[0]} Early Blight (Alternaria solani)"
            d_score = min(0.72 + (brown_ratio * 2.5), 0.94)
            confidence = int(d_score * 100)
        elif green_ratio > 0.20:
            diagnosis = f"Healthy {leaf_species.split(' (')[0]} Foliage"
            d_score = 0.05
            confidence = 96
        else:
            diagnosis = f"{leaf_species.split(' (')[0]} Leaf Specimen (Evaluating)"
            d_score = 0.30
            confidence = 82

        self.custom_inference = {
            "leaf_species": leaf_species,
            "disease_name": diagnosis,
            "disease_score": round(d_score, 2),
            "disease_confidence": confidence,
            "weeds_found": is_weed,
            "weed_name": "Field Weed (Chenopodium)" if is_weed else "None",
            "weed_score": 0.85 if is_weed else 0.0,
            "weed_confidence": 85 if is_weed else 0,
            "image": web_url,
            "key": "custom"
        }
        return self.custom_inference

    def get_active_inference(self):
        if self.custom_inference:
            return self.custom_inference
        info = dict(self.PRESETS[self.active_key])
        info["key"] = self.active_key
        return info

detector = VisionDetector()
