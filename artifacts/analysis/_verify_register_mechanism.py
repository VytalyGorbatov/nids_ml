"""Verify the REGISTER FN-recovery mechanism for the writeup. Read-only analysis."""
import json, statistics as st
from nids_ml.data.sip_struct import (
    header_text_from_record as H, parse_sip_header as P, sip_message_type as T,
)

RUNS = {
    "baseline": "nids_ml/artifacts/runs/phase3_trainability/head_last_block_production",
    "E4a_bf30": "nids_ml/artifacts/runs/phase3_trainability/e4a_hlb_register770_bf30",
    "E5a_bf20": "nids_ml/artifacts/runs/phase3_trainability/e5a_hlb_register770_bf20",
    "E2b_hlb":  "nids_ml/artifacts/runs/phase3_trainability/e2b_hlb_register770",
}

def load(p):
    d = json.load(open(p)); return d["dataset"] if isinstance(d, dict) else d

# dataset test records, ordered benign then attack (same as *_samples.json)
ben = load("sip-dataset/benign/test.json"); att = load("sip-dataset/attack/test.json")
recs = ben + att
types = [T(P(H(r))) for r in recs]
print(f"test: {len(ben)} benign + {len(att)} attack = {len(recs)}")

def q95(samples):  # val benign raw_score 95th pct -> FPR<=5% threshold
    b = sorted(s["raw_score"] for s in samples if s["is_attack"] == 0)
    return b[int(0.95 * len(b)) - 1]

def med(xs): return round(st.median(xs), 3) if xs else None

# FN population (is_attack=1, alerted=0)
fn_types = [types[i] for i, r in enumerate(recs) if r.get("is_attack") == 1 and r.get("alerted", 0) == 0]
print("FN pops:", {t: fn_types.count(t) for t in ("INVITE","OPTIONS","REGISTER","RESPONSE")}, "tot", len(fn_types))
reg_alert = sum(1 for r in recs if r.get("is_attack")==1 and T(P(H(r)))=="REGISTER" and r.get("alerted",0)==1)
print("REGISTER attack with alerted=1:", reg_alert)
# K=770 natural fraction: train-U REGISTER attack vs benign
tr = load("sip-dataset/benign/train.json") + load("sip-dataset/attack/train.json")
tr_t = [T(P(H(r))) for r in tr]
reg_p = sum(1 for i,r in enumerate(tr) if r.get("is_attack")==1 and r.get("alerted",0)==0 and tr_t[i]=="REGISTER")
reg_u_ben = sum(1 for i,r in enumerate(tr) if r.get("is_attack")==0 and tr_t[i]=="REGISTER")
print(f"train REGISTER: attackU={reg_p} benignU={reg_u_ben} natfrac={reg_p/(reg_p+reg_u_ben):.1%} K770ratio=1:{reg_u_ben/770:.1f} K128ratio=1:{reg_u_ben/128:.1f}")

for name, d in RUNS.items():
    ts = load(f"{d}/test_samples.json"); vs = load(f"{d}/val_samples.json")
    assert len(ts) == len(recs)
    T_run = q95(vs)
    g = lambda kind: [ts[i]["raw_score"] for i,r in enumerate(recs)
                      if r.get("is_attack")==1 and r.get("alerted",0)==0 and types[i]==kind]
    ben_s = [ts[i]["raw_score"] for i,r in enumerate(recs) if r.get("is_attack")==0]
    regfp = sum(1 for i,r in enumerate(recs) if r.get("is_attack")==0 and types[i]=="REGISTER" and ts[i]["raw_score"]>=T_run)
    inv_above = sum(1 for x in g("INVITE") if x>=T_run); reg_above = sum(1 for x in g("REGISTER") if x>=T_run)
    print(f"\n{name}: T_run={T_run:.3f}  INV50={med(g('INVITE'))} REG50={med(g('REGISTER'))} "
          f"OPT50={med(g('OPTIONS'))} BEN50={med(ben_s)}  INV>=T={inv_above} REG>=T={reg_above} REGfp={regfp}")
