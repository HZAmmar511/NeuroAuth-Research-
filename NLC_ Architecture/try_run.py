# try_run.py : quick manual run (no pass/fail judgment)
import pipeline

import pipeline

feat = {"V": 4, "F": 3, "Vel": 2.5}
print(pipeline.nlc_step("Hand", feat, 0.5, 0))    # True  (Th)
print(pipeline.nlc_step("Hand", feat, 0.5, 10))   # False (RT يحجب حتى t=30)
print(pipeline.nlc_step("Hand", feat, 0.5, 100))  # True  (انتهى الحجب)
# 31/10/2026 