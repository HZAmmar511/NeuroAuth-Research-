# config.py : PROVISIONAL values (not calibrated)

def _group():
    return {
        "theta_max": {"V": 5.0, "F": 4.0, "Vel": 3.0},
        "theta_min": {"V": 1.0, "F": 1.0, "Vel": 1.0},
        "tw_max": 200, "tw_min": 50,    # ms
        "tr_max": 40, "tr_min": 20,    # ms
        "fs": 100,                       # Hz
        "hist_max": 20,                  
    }

CFG = {g: _group() for g in ("Axial", "Hand", "Foot", "Devices")}
