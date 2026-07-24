import csv, statistics as st
from collections import defaultdict

d = defaultdict(list)
with open('data.csv') as f:
    for r in csv.DictReader(f):
        d[(r['build'], r['alg'], r['op'])].append(float(r['us']))

algs = ['ML-KEM-512','ML-KEM-768','ML-KEM-1024','ML-DSA-44','ML-DSA-65','ML-DSA-87']
ops  = {'ML-KEM':['keygen','encaps','decaps'], 'ML-DSA':['keypair','sign','verify']}
ACCEL = {'ML-KEM-768','ML-DSA-65'}

print(f"{'algorithm':<13}{'op':<9}{'generic med':>12}{'[min-max]':>18}{'a64 med':>10}{'[min-max]':>18}{'speedup':>9}{'delta%':>9}  arm")
print('-'*106)
rows=[]
for a in algs:
    fam = 'ML-KEM' if 'KEM' in a else 'ML-DSA'
    for o in ops[fam]:
        g = d[('generic',a,o)]; n = d[('a64',a,o)]
        gm, nm = st.median(g), st.median(n)
        sp = gm/nm; dl = (nm-gm)/gm*100
        arm = 'ACCEL' if a in ACCEL else 'control'
        rows.append((a,o,gm,min(g),max(g),nm,min(n),max(n),sp,dl,arm))
        print(f"{a:<13}{o:<9}{gm:>12.3f}{f'[{min(g):.2f}-{max(g):.2f}]':>18}{nm:>10.3f}{f'[{min(n):.2f}-{max(n):.2f}]':>18}{sp:>9.3f}{dl:>+9.1f}  {arm}")

print()
print("FULL-CYCLE / TOTAL (sum of medians)")
for a in algs:
    fam = 'ML-KEM' if 'KEM' in a else 'ML-DSA'
    gt = sum(st.median(d[('generic',a,o)]) for o in ops[fam])
    nt = sum(st.median(d[('a64',a,o)]) for o in ops[fam])
    arm = 'ACCEL' if a in ACCEL else 'control'
    print(f"  {a:<13} generic {gt:8.2f}  a64 {nt:8.2f}  speedup {gt/nt:.3f}  ({arm})")

print()
ctrl=[abs(r[9]) for r in rows if r[10]=='control']
print(f"CONTROL ARMS: n={len(ctrl)}, max |delta| = {max(ctrl):.2f}%, mean |delta| = {sum(ctrl)/len(ctrl):.2f}%")
acc=[r for r in rows if r[10]=='ACCEL']
print(f"ACCELERATED : speedups {[round(r[8],3) for r in acc]}")
