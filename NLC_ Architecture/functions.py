# ───────── adaptive ─────────
def A(x_max, x_min, cl):                 # Eq.(3)
    return x_max - cl * (x_max - x_min)

def A2(x_max, x_min, cl):                # Eq.(5)
    return x_min + cl * (x_max - x_min)

def require(x, name):
    if x is None:
        raise ValueError(f"∆ undefined: {name}")
    return x


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
    tw = A2(require(tw_max, "Tw_max"), require(tw_min, "Tw_min"), cl)   # بالثواني
    return max(1, round(tw * require(fs, "fs")))

def temporal_summation(buf, th_ok, th, n):
    # buf: {"V": [...], "F": [...], "Vel": [...]} والأخير = الدورة الحالية
    if th_ok:
        return False                     # Cancelled. تُعطى False كي لا تؤثر في Eq.(8)
    # ∆1: نافذة خلفية (causal) تنتهي عند الدورة الحالية، أم أمامية؟
    # ∆2: المجموع على الأبعاد الثلاثة بنفس θ (افتراضي هنا)
    return all(np.sum(buf[d][-n:]) >= th[d] for d in DIMS)

# ───────── refractory ─────────

def refractory_period(cl, tr_max, tr_min):          # T_r(CL), Eq.(6)
    return A(require(tr_max, "Tr_max"), require(tr_min, "Tr_min"), cl)

def rt_possible(t_now, t_fire, tr):
    # tr تُحفظ لحظة الإطلاق (CL دورة الإطلاق) ولا تُعاد حسابها
    return t_fire is None or t_now >= t_fire + tr

# ───────── emergency_override ─────────

def emergency_override(feat, th, margin=1.5):       # Eq.(7)
    return all(feat[d] >= margin * th[d] for d in DIMS)

# ───────── decision_maker ─────────
def decision_maker(th, ts, rt_possible, eo):        # Eq.(8)
    return ((th or ts) and rt_possible) or eo


 # ───────── nlc_controller ─────────
LIMB_GROUP = {                           # ∆6: تأكيد القائمة
    "head": "Axial", "neck": "Axial", "back": "Axial", "hip": "Axial",
    "shoulder": "Hand", "arm": "Hand", "hand": "Hand", "finger": "Hand",
    "thigh": "Foot", "knee": "Foot", "foot": "Foot",
    "device": "Devices",
}

def route(limb):
    return LIMB_GROUP[limb]              # KeyError لو limb غير معروف (مقصود)



