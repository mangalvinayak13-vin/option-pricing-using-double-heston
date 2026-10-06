"""Look at the real NSE bhavcopy files: what the designs can show honestly."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "market_data_audit" / "stage_a" / "raw" / "nse"
days = sorted(p.name for p in RAW.iterdir() if p.is_dir())
print("days", len(days), days[0], days[-1])
last = days[-1]
fo = pd.read_csv(RAW / last / f"BhavCopy_NSE_FO_0_0_0_{last.replace('-', '')}_F_0000.csv")
print(fo.FinInstrmTp.value_counts().to_dict())
n = fo[(fo.TckrSymb == "NIFTY") & (fo.FinInstrmTp == "IDO")]
print("NIFTY expiries", sorted(n.XpryDt.unique())[:10])
print("underlying", n.UndrlygPric.unique()[:3])
print(n[["XpryDt", "StrkPric", "OptnTp", "ClsPric", "SttlmPric", "OpnIntrst", "TtlTradgVol"]].head(4))
cm = pd.read_csv(RAW / last / f"BhavCopy_NSE_CM_0_0_0_{last.replace('-', '')}_F_0000.csv")
r = cm[(cm.TckrSymb == "RELIANCE") & (cm.SctySrs == "EQ")]
print(r[["OpnPric", "HghPric", "LwPric", "ClsPric", "PrvsClsgPric", "TtlTradgVol"]])
