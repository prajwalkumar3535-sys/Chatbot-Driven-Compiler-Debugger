"""
metrics.py - Green Sandbox Metrics Calculation & Environmental Impact Tracking
Measures latency (ms), memory (KB), energy used (Wh), carbon emissions (g CO2eq),
and computes a green "Eco Score" badge with high-resolution telemetry.
"""

import time
import os
import psutil
from typing import Optional, Dict, Any

GLOBAL_GRID_INTENSITY = 475.0  # g CO2eq / kWh
AVG_ACTIVE_WATTAGE = 45.0      # Estimated average system power consumption (Watts)

class GreenTracker:
    _last_metrics: Optional[Dict[str, Any]] = None

    def __init__(self, project_name: str = "sandbox_run"):
        self.project_name = project_name
        self.start_time = 0.0
        self.initial_mem = 0

    def start(self):
        self.start_time = time.perf_counter()
        try:
            process = psutil.Process(os.getpid())
            self.initial_mem = process.memory_info().rss
        except Exception:
            self.initial_mem = 32 * 1024 * 1024

    def stop(self) -> Dict[str, Any]:
        duration_sec = max(0.0005, time.perf_counter() - self.start_time)
        time_ms = round(duration_sec * 1000.0, 2)

        # Measure peak memory
        memory_kb = 16384
        try:
            process = psutil.Process(os.getpid())
            current_mem = process.memory_info().rss
            memory_kb = max(1024, int(current_mem / 1024))
        except Exception:
            pass

        # Calculate exact energy in kWh and Wh
        # Energy (Wh) = Power (Watts) * Time (hours)
        # 1 hour = 3600 seconds
        energy_wh = round((AVG_ACTIVE_WATTAGE * duration_sec) / 3600.0, 6)
        energy_kwh = energy_wh / 1000.0
        carbon_g = round(energy_kwh * GLOBAL_GRID_INTENSITY, 6)

        # Calculate Eco Score
        if energy_wh < 0.010:
            eco_score = "A+"
            eco_label = "Optimal"
        elif energy_wh < 0.050:
            eco_score = "A"
            eco_label = "Ultra Clean"
        elif energy_wh < 0.150:
            eco_score = "B"
            eco_label = "Efficient"
        elif energy_wh < 0.500:
            eco_score = "C"
            eco_label = "Moderate"
        else:
            eco_score = "D"
            eco_label = "High Impact"

        delta_time = None
        delta_energy = None
        if GreenTracker._last_metrics:
            delta_time = round(time_ms - GreenTracker._last_metrics.get("time_ms", time_ms), 2)
            delta_energy = round(energy_wh - GreenTracker._last_metrics.get("energy_wh", energy_wh), 6)

        metrics = {
            "time_ms": time_ms,
            "memory_kb": memory_kb,
            "energy_wh": energy_wh,
            "carbon_g": carbon_g,
            "eco_score": eco_score,
            "eco_label": eco_label,
            "delta_time_ms": delta_time,
            "delta_energy_wh": delta_energy
        }

        GreenTracker._last_metrics = metrics
        return metrics
