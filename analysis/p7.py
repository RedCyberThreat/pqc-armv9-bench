import statistics as st

wifi_pqc  = [86,84,95,113,95,121,108,92,126,88,95,96,92,85,93,90,101,88,83,89,95,111,95,94,93]
wifi_cls  = [96,89,109,96,101,96,107,90,109,124,89,86,91,83,77,102,157,89,94,100,92,94,110,89,99]
null_a    = [105,83,93,108,119,85,82,94,100,100,91,129,84,101,120]
null_b    = [83,101,90,101,84,116,93,95,96,86,93,79,81,110,96]
# cellular run1: pair-1 PQC = 519352 ms (network establishment stall, bytes=NA) -> excluded
cell1_pqc = [135,134,173,165,163,165,141,147,143,151,182,159,174,190,165,204,181,170,173,137,187,179,153,176]
cell1_cls = [228,134,138,173,148,148,160,154,182,151,150,140,158,164,186,147,165,185,181,283,309,146,143,208,196]
cell2_pqc = [187,186,175,163,144,182,162,158,151,138,158,170,190,197,546,165,131,143,204,159,182,212,203,172,236]
cell2_cls = [162,150,161,172,155,178,177,142,163,150,163,144,181,179,156,169,181,197,180,188,195,181,157,142,209]
cell2_pqc_clean = [v for v in cell2_pqc if v < 400]

def s(name, d):
    print(f"  {name:<28} n={len(d):>3}  median={st.median(d):>7.1f}  IQR=[{st.quantiles(d,n=4)[0]:.0f}-{st.quantiles(d,n=4)[2]:.0f}]  min-max=[{min(d)}-{max(d)}]")

print("=== WALL-CLOCK (ms), includes process start + DNS + TCP + TLS + teardown ===")
s("wifi  X25519MLKEM768", wifi_pqc); s("wifi  X25519", wifi_cls)
print(f"    -> paired median delta: {st.median(wifi_pqc)-st.median(wifi_cls):+.1f} ms")
print()
s("NULL CONTROL X25519 (A)", null_a); s("NULL CONTROL X25519 (B)", null_b)
print(f"    -> SPURIOUS delta between IDENTICAL conditions: {st.median(null_a)-st.median(null_b):+.1f} ms")
print()
s("cell1 X25519MLKEM768", cell1_pqc); s("cell1 X25519", cell1_cls)
print(f"    -> paired median delta: {st.median(cell1_pqc)-st.median(cell1_cls):+.1f} ms")
s("cell2 X25519MLKEM768", cell2_pqc_clean); s("cell2 X25519", cell2_cls)
print(f"    -> paired median delta: {st.median(cell2_pqc_clean)-st.median(cell2_cls):+.1f} ms")

print()
print("=== HANDSHAKE BYTES (deterministic, network-independent) ===")
print(f"  {'':<18}{'written':>10}{'read':>10}{'total':>10}")
print(f"  {'X25519':<18}{325:>10}{2869:>10}{3194:>10}")
print(f"  {'X25519MLKEM768':<18}{1503:>10}{3957:>10}{5460:>10}")
print(f"  {'delta':<18}{1503-325:>+10}{3957-2869:>+10}{5460-3194:>+10}")
print(f"  {'ratio':<18}{1503/325:>10.2f}{3957/2869:>10.2f}{5460/3194:>10.2f}")
print()
print("  ML-KEM-768 spec sizes: encapsulation key 1184 B, ciphertext 1088 B")
print(f"  measured read delta  = {3957-2869} B  <-> ML-KEM-768 ciphertext = 1088 B  (exact match)")
print(f"  measured write delta = {1503-325} B  <-> ML-KEM-768 ek 1184 B minus X25519 share 32 B = 1152 B")
print()
print("=== EFFECT SIZE vs NOISE FLOOR ===")
noise = abs(st.median(null_a)-st.median(null_b))
for lbl,a,b in [("wifi",wifi_pqc,wifi_cls),("cell1",cell1_pqc,cell1_cls),("cell2",cell2_pqc_clean,cell2_cls)]:
    d = st.median(a)-st.median(b)
    print(f"  {lbl:<8} PQC-classical delta = {d:+6.1f} ms   |delta| {'<' if abs(d)<noise else '>='} null-control noise ({noise:.1f} ms)")
print()
print(f"  PQC computation measured in Phase 3 (encaps+decaps) = 0.035 ms")
print(f"  Wi-Fi RTT baseline (ping avg) = 30.6 ms  -> {30.6/0.035:.0f}x the PQC computation")
