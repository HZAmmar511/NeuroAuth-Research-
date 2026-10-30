# ───────── adaptive ─────────

def A(x_max, x_min, cl):                 # Eq.(3)
    return x_max - cl * (x_max - x_min)

def A2(x_max, x_min, cl):                # Eq.(5)
    return x_min + cl * (x_max - x_min)

def require(x, name):
    if x is None:
        raise ValueError(f"∆ undefined: {name}")
    return x

# ───────── History ─────────

def record(hist, item, execute, max_len):
    hist["all"].append(item)
    if execute:
        hist["authorized"].append(item)
    if max_len is not None:                 
        hist["all"] = hist["all"][-max_len:]
        hist["authorized"] = hist["authorized"][-max_len:]


# ───────── threshold─────────

DIMS = ("V", "F", "Vel")

def theta(cl, th_max, th_min):           # θ_i(CL), Eq.(4)
    return {d: A(require(th_max[d], f"theta_max[{d}]"),
                 require(th_min[d], f"theta_min[{d}]"), cl) for d in DIMS}

def threshold(feat, th):                 # Th = 1[V≥θV ∧ F≥θF ∧ Vel≥θVel]
    return all(feat[d] >= th[d] for d in DIMS)

# ───────── temporal_summation ─────────

import numpy as np

def window_samples(cl, tw_max, tw_min, fs):
    tw = A2(require(tw_max, "Tw_max"), require(tw_min, "Tw_min"), cl)   # ms
    return max(1, round(tw * require(fs, "fs") / 1000))                 # ms -> samples

def temporal_summation(buf, th_ok, th, n):
    if th_ok:
        return False                        
    return all(np.sum(buf[d][-n:]) >= th[d] for d in DIMS)

# ───────── refractory ─────────

def refractory_period(cl, tr_max, tr_min):          # T_r(CL), Eq.(6)
    return A(require(tr_max, "Tr_max"), require(tr_min, "Tr_min"), cl)

def rt_possible(t_now, t_fire, tr):
        return t_fire is None or t_now >= t_fire + tr

# ───────── emergency_override ─────────

def emergency_override(feat, th, margin=1.5):       # Eq.(7)
    return all(feat[d] >= margin * th[d] for d in DIMS)

# ───────── decision_maker ─────────
def decision_maker(th, ts, rt_possible, eo):        # Eq.(8)
    return ((th or ts) and rt_possible) or eo

