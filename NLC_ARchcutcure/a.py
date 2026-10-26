# ───────── adaptive ─────────
def A(x_max, x_min, cl):                 # Eq.(3)
    return x_max - cl * (x_max - x_min)

def A2(x_max, x_min, cl):                # Eq.(5): الاتجاه معكوس
    return x_min + cl * (x_max - x_min)

def require(x, name):
    if x is None:
        raise ValueError(f"∆ undefined: {name}")
    return x


# ───────── threshold─────────
from adaptive import A, require
DIMS = ("V", "F", "Vel")

def theta(cl, th_max, th_min):           # θ_i(CL), Eq.(4)
    return {d: A(require(th_max[d], f"theta_max[{d}]"),
                 require(th_min[d], f"theta_min[{d}]"), cl) for d in DIMS}

def threshold(feat, th):                 # Th = 1[V≥θV ∧ F≥θF ∧ Vel≥θVel]
    return all(feat[d] >= th[d] for d in DIMS)

# ───────── temporal_summation ─────────
import numpy as np
from adaptive import A2, require
from threshold import DIMS

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
from adaptive import A, require

def refractory_period(cl, tr_max, tr_min):          # T_r(CL), Eq.(6)
    return A(require(tr_max, "Tr_max"), require(tr_min, "Tr_min"), cl)

def rt_possible(t_now, t_fire, tr):
    # tr تُحفظ لحظة الإطلاق (CL دورة الإطلاق) ولا تُعاد حسابها
    return t_fire is None or t_now >= t_fire + tr

# ───────── emergency_override ─────────
from threshold import DIMS

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

# ───────── pipeline ─────────
from threshold import DIMS, theta, threshold
from temporal_summation import window_samples, temporal_summation
from refractory import refractory_period, rt_possible
from emergency_override import emergency_override
from decision_maker import decision_maker
from history import record
from nlc_controller import route

CFG = {g: {                              # ∆7: θ حسب كل limb group
    "theta_max": {"V": None, "F": None, "Vel": None},
    "theta_min": {"V": None, "F": None, "Vel": None},
    "tw_max": None, "tw_min": None,      # ∆8 (ثوانٍ)
    "tr_max": None, "tr_min": None,      # ∆9 (ثوانٍ، مستوى القرار لا الخلية)
    "fs": None,                          # ∆10
} for g in ("Axial", "Hand", "Foot", "Devices")}

def new_state():
    return {"t_fire": None, "tr": None, "last_cl": None,
            "buf": {d: [] for d in DIMS},
            "hist": {"all": [], "authorized": []}}

STATES = {g: new_state() for g in CFG}   # حالة مستقلة لكل group

def nlc_step(group, feat, cl, t_now):
    s, c = STATES[group], CFG[group]
    n = window_samples(cl, c["tw_max"], c["tw_min"], c["fs"])
    maxn = window_samples(1.0, c["tw_max"], c["tw_min"], c["fs"])  # أطول نافذة
    for d in DIMS:
        s["buf"][d].append(feat[d])
        s["buf"][d] = s["buf"][d][-maxn:]

    th = theta(cl, c["theta_max"], c["theta_min"])
    th_ok = threshold(feat, th)
    ts_ok = temporal_summation(s["buf"], th_ok, th, n)
    rt_ok = rt_possible(t_now, s["t_fire"], s["tr"])

    # EO: θ من الدورة السابقة، وأول تفعيل بالقيم القصوى الأساسية (∆11: هنا أم داخل EO؟)
    th_eo = (c["theta_max"] if s["last_cl"] is None
             else theta(s["last_cl"], c["theta_max"], c["theta_min"]))
    eo_ok = emergency_override(feat, th_eo)

    execute = decision_maker(th_ok, ts_ok, rt_ok, eo_ok)
    if execute:
        # ∆12: هل تبدأ EO فترة refractory؟ هنا نعم (أي تنفيذ يبدؤها)
        s["t_fire"], s["tr"] = t_now, refractory_period(cl, c["tr_max"], c["tr_min"])
    record(s["hist"], {"t": t_now, **feat}, execute)
    s["last_cl"] = cl
    return execute

def nlc(limb, feat, cl, t_now):
    return nlc_step(route(limb), feat, cl, t_now)


