# ───────── pipeline ─────────
import functions

CFG = {g: {                              # ∆7: θ حسب كل limb group
    "theta_max": {"V": None, "F": None, "Vel": None},
    "theta_min": {"V": None, "F": None, "Vel": None},
    "tw_max": None, "tw_min": None,      # ∆8 (ثوانٍ)
    "tr_max": None, "tr_min": None,      # ∆9 (ثوانٍ، مستوى القرار لا الخلية)
    "fs": None,                          # ∆10
} for g in ("Axial", "Hand", "Foot", "Devices")}

def new_state():
    return {"t_fire": None, "tr": None, "last_cl": None,
            "buf": {d: [] for d in functions.DIMS},
            "hist": {"all": [], "authorized": []}}

STATES = {g: new_state() for g in CFG}   # حالة مستقلة لكل group

def nlc_step(group, feat, cl, t_now):
    s, c = STATES[group], CFG[group]
    n = functions.window_samples(cl, c["tw_max"], c["tw_min"], c["fs"])
    maxn = functions.window_samples(1.0, c["tw_max"], c["tw_min"], c["fs"])  # أطول نافذة
    for d in functions.DIMS:
        s["buf"][d].append(feat[d])
        s["buf"][d] = s["buf"][d][-maxn:]

    th = functions.theta(cl, c["theta_max"], c["theta_min"])
    th_ok = functions.threshold(feat, th)
    ts_ok = functions.temporal_summation(s["buf"], th_ok, th, n)
    rt_ok = functions.rt_possible(t_now, s["t_fire"], s["tr"])

    # EO: θ من الدورة السابقة، وأول تفعيل بالقيم القصوى الأساسية (∆11: هنا أم داخل EO؟)
    th_eo = (c["theta_max"] if s["last_cl"] is None
             else functions.theta(s["last_cl"], c["theta_max"], c["theta_min"]))
    eo_ok = functions.emergency_override(feat, th_eo)

    execute = functions.decision_maker(th_ok, ts_ok, rt_ok, eo_ok)
    if execute:
        # ∆12: هل تبدأ EO فترة refractory؟ هنا نعم (أي تنفيذ يبدؤها)
        s["t_fire"], s["tr"] = t_now, functions.refractory_period(cl, c["tr_max"], c["tr_min"])
    functions.record(s["hist"], {"t": t_now, **feat}, execute)
    s["last_cl"] = cl
    return execute

def nlc(limb, feat, cl, t_now):
    return nlc_step(functions.route(limb), feat, cl, t_now)
