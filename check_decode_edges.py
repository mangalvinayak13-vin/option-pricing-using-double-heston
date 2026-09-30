import warnings, sys
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")
import numpy as np
from mentor_dh_pinn import params_v2 as P

z = np.full(10, 14.0)
vec = np.asarray(P.to_array(P.decode(z)), float)
print("decode(+14 corner):", vec)
print("any NaN/Inf:", not np.isfinite(vec).all())

z2 = np.full(10, -14.0)
vec2 = np.asarray(P.to_array(P.decode(z2)), float)
print("decode(-14 corner):", vec2)
print("any NaN/Inf:", not np.isfinite(vec2).all())

print("exp(14) =", np.exp(14.0))
