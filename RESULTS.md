# Phase 4 Results — liboqs Backend Ablation on ARMv9-A

**Device:** Samsung Galaxy S23 (SM-S911B), Qualcomm Snapdragon 8 Gen 2 (1× Cortex-X3 @ 3.36 GHz,
2× Cortex-A715 + 2× Cortex-A710 @ 2.80 GHz, 3× Cortex-A510 @ 2.02 GHz)
**OS:** Android 16 (SDK 36), build BP4A.251205.006.S911BXXSAFZF5, security patch 2026-06-05
**Kernel:** 5.15.189-android13-8, `walt` governor on all three cpufreq policies
**Environment:** Termux, unprivileged userspace
**Library:** liboqs main @ `04ab195f` (reports 0.15.0), Clang 21.1.8, `-march=armv8-a+crypto -O3`
**Date of campaign:** 2026-07-23, 14:03–15:15 local

---

## 1. Experimental design

Two build configurations, identical except for the lattice-arithmetic backend:

| Arm | Configuration | Lattice arithmetic | Keccak/SHAKE |
|---|---|---|---|
| **generic** | `OQS_DIST_BUILD=ON`, `OQS_OPT_TARGET=generic` | portable C (`_ref`) | portable C |
| **a64** | as above **+** `OQS_ENABLE_KEM_ml_kem_768_aarch64=ON`, `OQS_ENABLE_SIG_ml_dsa_65_aarch64=ON` | aarch64/NEON assembly for ML-KEM-768 and ML-DSA-65 only | portable C |

Because the per-algorithm flags were applied only to ML-KEM-768 and ML-DSA-65, the remaining four
parameter sets executed identical portable-C code in both arms. **These four therefore function as
internal controls**, measured within the same sessions, under the same thermal and DVFS conditions,
and interleaved in the same order as the treated algorithms.

**Protocol:** 5 independent runs per algorithm per arm; `-d 3` (3 s per operation); 60 s cooldown
between algorithms; device idle, screen on, Termux foreground, airplane mode, battery ≥ 80 %,
`termux-wake-lock` held. Reported statistic is the **median of the 5 run means**, with the
across-run min–max range. Medians are used because run-to-run scheduler interference produces
occasional high outliers (see §4.1).

---

## 2. Results

### 2.1 ML-KEM (FIPS 203)

Latency in microseconds; median of 5 runs [min–max].

| Algorithm | Operation | generic (C) | a64 (NEON) | Speedup | Arm |
|---|---|---|---|---|---|
| ML-KEM-512 | keygen | 11.982 [11.97–31.72] | 12.080 [12.05–12.52] | 0.99× | control |
| ML-KEM-512 | encaps | 12.742 [12.65–14.01] | 12.852 [12.76–13.92] | 0.99× | control |
| ML-KEM-512 | decaps | 15.207 [15.11–15.70] | 15.314 [15.19–16.34] | 0.99× | control |
| **ML-KEM-768** | **keygen** | **20.539** [20.48–21.49] | **14.606** [14.52–14.68] | **1.41×** | **treated** |
| **ML-KEM-768** | **encaps** | **19.822** [19.70–20.99] | **15.737** [15.64–15.78] | **1.26×** | **treated** |
| **ML-KEM-768** | **decaps** | **23.236** [23.16–23.64] | **18.908** [18.72–19.71] | **1.23×** | **treated** |
| ML-KEM-1024 | keygen | 31.283 [31.12–31.36] | 31.261 [31.20–31.38] | 1.00× | control |
| ML-KEM-1024 | encaps | 29.282 [29.13–29.59] | 29.685 [29.38–30.65] | 0.99× | control |
| ML-KEM-1024 | decaps | 34.246 [34.08–34.53] | 34.527 [34.24–35.85] | 0.99× | control |

**Full cycle (keygen + encaps + decaps), ML-KEM-768:** 63.60 µs → **49.25 µs** (1.29×, −22.6 %).

### 2.2 ML-DSA (FIPS 204)

| Algorithm | Operation | generic (C) | a64 (NEON) | Speedup | Arm |
|---|---|---|---|---|---|
| ML-DSA-44 | keypair | 41.811 [41.68–42.20] | 41.767 [41.52–41.92] | 1.00× | control |
| ML-DSA-44 | sign | 160.766 [160.38–161.59] | 162.177 [161.01–162.62] | 0.99× | control |
| ML-DSA-44 | verify | 46.076 [45.93–53.25] | 46.164 [45.94–46.68] | 1.00× | control |
| **ML-DSA-65** | **keypair** | **77.763** [77.58–78.32] | **58.026** [57.83–61.14] | **1.34×** | **treated** |
| **ML-DSA-65** | **sign** | **253.982** [253.48–255.14] | **135.175** [134.07–143.34] | **1.88×** | **treated** |
| **ML-DSA-65** | **verify** | **74.095** [73.84–74.88] | **56.406** [55.80–57.00] | **1.31×** | **treated** |
| ML-DSA-87 | keypair | 117.435 [116.52–118.36] | 117.124 [116.28–118.58] | 1.00× | control |
| ML-DSA-87 | sign | 314.977 [313.59–318.13] | 315.675 [314.45–316.48] | 1.00× | control |
| ML-DSA-87 | verify | 123.065 [122.34–123.56] | 123.218 [122.95–128.40] | 1.00× | control |

### 2.3 Control validation

| Metric | Value |
|---|---|
| Control operations measured | 12 (4 algorithms × 3 operations) |
| Maximum absolute deviation between arms | **1.38 %** |
| Mean absolute deviation between arms | **0.54 %** |
| Treated-arm improvements | **18.6 % – 46.8 %** |

The separation between control deviation (≤ 1.4 %) and treated-arm improvement (≥ 18.6 %) is
roughly an order of magnitude, supporting attribution of the observed differences to the backend
rather than to environmental drift.

---

## 3. Interpretation

### 3.1 The acceleration is confined to lattice arithmetic

Both builds report `SHA-3: C` in the liboqs configuration banner. Inspection of the source tree
shows that `src/common/sha3/xkcp_low/KeccakP-1600/` contains only `avx2/` and `plain-64bits/`
implementations: **liboqs 0.15 ships no ARM backend for the Keccak-f[1600] permutation**, despite
the device advertising `FEAT_SHA3` (the `sha3` hardware capability is present on all eight cores,
and liboqs detects it — `CPU exts active: AES SHA2 SHA3 NEON`). The runtime detection line reports
*hardware capability*, not *code path in use*; this distinction is easily misread.

Consequently the measured speedups are attributable solely to hand-written aarch64/NEON assembly
for the number-theoretic transform, pointwise multiplication, reduction, and rejection sampling.
The SHAKE-based sampling and hashing workload executed identical portable C in both arms.

### 3.2 The speedup gradient is consistent with that attribution

Within ML-KEM-768, the improvement is largest for keygen (1.41×) and smallest for decaps (1.23×).
Key generation is dominated by NTT and matrix expansion; decapsulation carries proportionally more
re-encryption and hashing work, which remains unaccelerated. The gradient therefore follows the
share of runtime that the assembly actually covers.

ML-DSA-65 signing shows the largest single improvement (1.88×), consistent with Fiat–Shamir with
aborts requiring repeated NTT-heavy commitment computations per signature attempt.

### 3.3 Implication for the performance ceiling

All results reported here — and all results in the pilot campaign — were obtained with a software
Keccak permutation. Since Keccak accounts for a substantial fraction of runtime in lattice schemes,
**the measured latencies represent a lower bound on the performance achievable on this hardware**,
not the hardware ceiling. A native ARM Keccak backend using EOR3/RAX1/XAR/BCAX would be expected to
reduce these figures further; quantifying that gain requires an implementation that liboqs does not
currently provide for this architecture.

### 3.4 Deployment observation

The aarch64 backends ship with liboqs but were **not selected by any documented build
configuration** on this platform. `OQS_DIST_BUILD=ON` with `OQS_OPT_TARGET=generic` compiled zero
aarch64 sources (`grep -c aarch64 build.ninja` → 0); activation required undocumented
per-algorithm `OQS_ENABLE_*_aarch64=ON` overrides. `OQS_OPT_TARGET=native` resolved to
`-mcpu=native` and produced binaries that terminated with SIGILL (exit 132) on the target device.

An out-of-the-box liboqs build on Android/aarch64 therefore runs reference C for both the lattice
arithmetic and Keccak, forgoing the 1.2–1.9× improvement demonstrated above.

---

## 4. Threats to validity

### 4.1 Scheduler interference

One run (generic, ML-KEM-512, run 4) reported a keygen mean of 31.724 µs with a within-run
population standard deviation of 61.751 µs, against a typical mean of ~12 µs and stdev ~1.1 µs.
This is consistent with the process being migrated to an efficiency core or preempted mid-run.
Median-based reporting isolates the effect; the outlier is retained in the raw logs and in
`data.csv` rather than removed.

### 4.2 Inherent variance in ML-DSA signing

ML-DSA sign operations exhibit within-run population standard deviations of 72–168 µs against means
of 135–316 µs — far higher than any other operation measured. This is a property of the algorithm,
not of the platform: Fiat–Shamir with aborts causes the number of rejection-sampling iterations to
vary per signature. Any latency budget for ML-DSA signing on mobile must be specified as a
distribution rather than a mean.

### 4.3 Remaining limitations

- Single device, single OS build; results may not generalise to other ARMv9-A implementations.
- Termux is unprivileged native userspace, not the Android application runtime (ART/JNI); real
  application overhead is not captured.
- Core placement was not controlled in this phase; the Android `walt` governor and vendor
  core-control policy determined which cluster executed each run (see the CPU affinity findings).
- Population standard deviations reported by liboqs measure within-run jitter; the across-run
  min–max ranges here measure reproducibility. Neither is a confidence interval.

---

## 5. Provenance

Every value in the tables above derives from a log file in `logs/phase4_matrix/`, named
`p4_<build>_<kem|sig>_<algorithm>_run<N>_<timestamp>.log`. The transcribed per-run values are in
`data.csv`; medians and speedups are computed by `analyze.py`.

**Note on build identification:** both arms print identical `Compile options` and `OQS build flags`
banners, because the per-algorithm overrides are not reflected in the configuration block. Arms are
therefore distinguishable only by build directory, recorded in the log filename. Correctness of the
`a64` arm was verified before benchmarking: `test_kem ML-KEM-768` and `test_sig ML-DSA-65` both
exited 0 against FIPS 203 / FIPS 204 vectors.

### Deviations from the pilot campaign (March–April 2026)

| Parameter | Pilot | This campaign |
|---|---|---|
| `CMAKE_BUILD_TYPE` | `RelWithDebInfo` (`-g3 -fno-omit-frame-pointer`) | `Release` (`-O3 -fomit-frame-pointer`) |
| Linkage | shared | static |
| Invocation | full algorithm suite in one process | one algorithm per process |
| Repetitions | 1 | 5 |
| OpenSSL | 3.6.1 | 3.6.3 |

The build-type change alone accounts for roughly a 22 % difference in generic-arm ML-KEM-768 keygen
latency (28.4 µs pilot → 20.5 µs here). Pilot and final figures are therefore **not
interchangeable** and are archived separately.

---

# Phase 3 Results — Classical Baselines and Cross-Library Validation

**Tool:** OpenSSL 3.6.3 (Termux package, compiled `-Oz`), `openssl speed -elapsed`
**Protocol:** 5 independent runs, 60 s cooldown, same device state as Phase 4
**Date:** 2026-07-23, 15:29–16:20 local
**Note on timing basis:** `-elapsed` selects wall-clock time, matching liboqs's timing basis.
Without it OpenSSL divides by CPU time and the two libraries are not comparable.

## 6. Classical baselines

Median of 5 runs [min–max], microseconds per operation.

| Algorithm | Operation | Latency (µs) | Range |
|---|---|---|---|
| ECDSA P-256 | sign | **17.605** | [17.53–18.99] |
| ECDSA P-256 | verify | **55.423** | [55.38–56.45] |
| ECDH P-256 | derive | **42.775** | [42.70–43.30] |
| X25519 | derive | **37.415** | [37.32–37.64] |
| Ed25519 | sign | 34.962 | [34.63–35.11] |
| Ed25519 | verify | 88.688 | [87.21–90.16] |

Ed25519 verification is slower than ECDSA P-256 verification on this platform, which is the
reverse of the usual ordering. OpenSSL ships dedicated ARM assembly for P-256 (`ecp_nistz256`)
but not for Ed25519, so this reflects implementation coverage rather than algorithmic cost.

## 7. Classical versus post-quantum

Comparison uses the fastest available implementation of each: OpenSSL for classical primitives,
liboqs `a64` for post-quantum.

| Operation pair | Classical | Post-quantum | Ratio |
|---|---|---|---|
| **Signing** | ECDSA P-256: 17.61 µs | ML-DSA-65: 135.18 µs | **7.68× slower** |
| **Verification** | ECDSA P-256: 55.42 µs | ML-DSA-65: 56.41 µs | **1.02× — parity** |
| **Key exchange** | ECDH P-256: 42.78 µs | ML-KEM-768 encaps+decaps: 34.65 µs | **0.81× — PQC faster** |
| **Key exchange** | X25519: 37.42 µs | ML-KEM-768 encaps+decaps: 34.65 µs | **0.93× — PQC faster** |

**Semantics caveat.** OpenSSL's `ecdh` operation measures a single shared-secret derivation. The
closest ML-KEM analogue after key generation is encapsulation plus decapsulation, used above. A
full ephemeral exchange additionally requires key generation on one side; including it
(ML-KEM-768 full cycle = 49.25 µs) still leaves the post-quantum exchange within 1.2× of ECDH
P-256. The comparison is therefore not exact, and both framings are reported.

**Interpretation.** The computational cost of migration is not uniform, and the draft's single
"quantum tax" figure conceals three different outcomes:

1. **Key establishment is cheaper post-quantum.** ML-KEM-768 completes encapsulation and
   decapsulation in less time than a single P-256 or X25519 scalar multiplication. Lattice
   arithmetic is dominated by vectorisable polynomial operations, whereas elliptic-curve
   operations are serial by nature. The bandwidth cost of ML-KEM (2,272 B vs 128 B) is therefore
   the sole penalty for key exchange on this platform; the CPU penalty is negative.
2. **Verification is at parity.** ML-DSA-65 verification differs from ECDSA P-256 verification by
   1.8 %, which is within the run-to-run range of both measurements. For workloads dominated by
   signature verification — certificate chain validation, token checking, software update
   verification — the computational cost of migration is not measurable at the application level.
3. **Signing carries a real cost.** ML-DSA-65 signing is 7.68× slower than ECDSA P-256 signing.
   This is the honest cost of migration and must be stated: at 135 µs it remains far below any
   interactive-latency threshold, but the ratio is substantial and workload-dependent.

**Hybrid deployment cost.** The thesis recommends hybrid key exchange (X25519 + ML-KEM-768, the
`X25519MLKEM768` group). From the measurements above, the combined computational cost is
37.42 + 49.25 = **86.67 µs** — approximately 2.3× the cost of X25519 alone, and still under
0.1 ms. Hybrid deployment is therefore not constrained by computation on this class of device.

## 8. Cross-library validation

Both libraries implement the same FIPS 203 / FIPS 204 algorithms; both were measured on the same
device on the same day with the same timing basis.

| Algorithm | Operation | liboqs C | liboqs a64 | OpenSSL | OpenSSL / best liboqs |
|---|---|---|---|---|---|
| ML-KEM-512 | keygen | 11.98 | 12.08 | 23.19 | 1.94× |
| ML-KEM-512 | encaps | 12.74 | 12.85 | 19.33 | 1.52× |
| ML-KEM-512 | decaps | 15.21 | 15.31 | 30.62 | 2.01× |
| ML-KEM-768 | keygen | 20.54 | 14.61 | 38.28 | 2.62× |
| ML-KEM-768 | encaps | 19.82 | 15.74 | 28.46 | 1.81× |
| ML-KEM-768 | decaps | 23.24 | 18.91 | 43.59 | 2.31× |
| ML-KEM-1024 | keygen | 31.28 | 31.26 | 57.34 | 1.83× |
| ML-KEM-1024 | encaps | 29.28 | 29.68 | 38.73 | 1.32× |
| ML-KEM-1024 | decaps | 34.25 | 34.53 | 58.03 | 1.69× |
| ML-DSA-44 | keygen | 41.81 | 41.77 | 84.77 | 2.03× |
| ML-DSA-44 | sign | 160.77 | 162.18 | 495.12 | 3.08× |
| ML-DSA-44 | verify | 46.08 | 46.16 | 95.13 | 2.06× |
| ML-DSA-65 | keygen | 77.76 | 58.03 | 150.54 | 2.59× |
| ML-DSA-65 | sign | 253.98 | 135.18 | 846.53 | **6.26×** |
| ML-DSA-65 | verify | 74.09 | 56.41 | 149.23 | 2.65× |
| ML-DSA-87 | keygen | 117.44 | 117.12 | 230.38 | 1.97× |
| ML-DSA-87 | sign | 314.98 | 315.68 | 990.10 | 3.14× |
| ML-DSA-87 | verify | 123.06 | 123.22 | 246.81 | 2.01× |

OpenSSL is slower than liboqs on every one of the 18 operations measured, by factors of 1.32× to
6.26×. The Termux OpenSSL package is compiled with **`-Oz`** (optimise for minimum size), visible
in the `compiler:` line of every OpenSSL log, whereas both liboqs builds used `-O3`. The
comparison is therefore between two build configurations as much as between two codebases, and
should not be read as a statement about the libraries' relative quality.

The magnitude is nonetheless the point. The spread attributable to implementation and build
configuration (up to 6.26×) exceeds the spread attributable to the ARM assembly backend (1.88×)
and vastly exceeds the difference between post-quantum and classical verification (1.02×). For
RQ3, this ranks the factors influencing post-quantum performance on ARMv9-A:

1. Library and compiler configuration — up to 6.3×
2. Availability of architecture-specific assembly — up to 1.9×
3. Choice of security category (512 → 1024) — approximately 2.6×
4. Post-quantum versus classical, for verification — 1.02×

The dominant factor is not the instruction set, the scheduler, or the algorithm. It is the
software supply chain: which library an application links against, and how the distribution
maintainer compiled it.

## 9. Provenance (Phase 3)

Per-run throughput values are in `p3_data.csv`; conversions and comparisons are computed by
`p3.py`. Raw logs are in `logs/phase3_openssl/`, named
`p3_openssl_{classical,pqc_kem,pqc_sig}_run<N>_<timestamp>.log`. OpenSSL reports throughput
(ops/s); latencies above are the reciprocal, taken as the median across the 5 runs.
`OPENSSL_armcap=0xefd` is recorded in every log and documents the ARM crypto features OpenSSL
enabled at runtime.

---

# Phase 7 Results — TLS 1.3 Handshake Measurement

**Endpoint:** cloudflare.com:443, TLS 1.3, `TLS_AES_256_GCM_SHA384`, ECDSA P-256 server certificate
**Client:** OpenSSL 3.6.3 `s_client`, groups forced to `X25519MLKEM768` (hybrid) or `X25519` (classical)
**Design:** paired alternating sampling — each pair issues one hybrid and one classical handshake
back to back, so both conditions experience the same network state. Plus a **null control** in which
both arms of the pair request `X25519`, establishing the noise floor of the measurement itself.
**Networks:** Wi-Fi (25 pairs + 15 null-control pairs) and cellular (two independent sessions,
25 pairs each). RTT baseline to the endpoint: min 17.8 / avg 30.6 / max 51.4 ms, mdev 12.7 ms.
**Date:** 2026-07-23, 13:16–13:50 UTC

## 10. Handshake size (deterministic)

Byte counts reported by `s_client` are independent of network conditions and identical on every
one of the 100 handshakes measured.

| Key exchange group | Client→server (B) | Server→client (B) | Total (B) |
|---|---|---|---|
| X25519 | 325 | 2,869 | 3,194 |
| X25519MLKEM768 | 1,503 | 3,957 | 5,460 |
| **Difference** | **+1,178 (4.62×)** | **+1,088 (1.38×)** | **+2,266 (1.71×)** |

The server→client difference is **exactly 1,088 bytes**, which is precisely the ML-KEM-768
ciphertext size specified in FIPS 203. The client→server difference of 1,178 bytes corresponds to
the ML-KEM-768 encapsulation key (1,184 B) replacing nothing and the X25519 share (32 B) being
retained, plus TLS extension framing. This exact correspondence validates that the measurement is
capturing the intended quantity.

**This supersedes the primitive-size table in the earlier draft.** A complete TLS 1.3 handshake
grows by a factor of 1.71×, not the 18–41× suggested by comparing raw key and signature sizes in
isolation — because the handshake is dominated by the certificate chain, which is unchanged. The
raw-primitive framing substantially overstates the deployed cost.

## 11. Handshake latency

Wall-clock per handshake includes process startup, DNS, TCP connect, the TLS handshake, and
teardown. Absolute values are therefore **not** TLS handshake times and must not be reported as
such. Only the paired difference is interpretable.

| Session | Hybrid median (ms) | Classical median (ms) | Difference |
|---|---|---|---|
| Wi-Fi (n=25 pairs) | 94.0 | 96.0 | **−2.0 ms** |
| Cellular session 1 (n=24/25) | 165.0 | 160.0 | **+5.0 ms** |
| Cellular session 2 (n=24/25) | 171.0 | 169.0 | **+2.0 ms** |
| **Null control** (X25519 vs X25519, n=15 pairs) | 100.0 | 93.0 | **+7.0 ms** |

**The null control is decisive.** Two identical conditions, differing in nothing but sampling order,
produced a spurious median difference of 7.0 ms. Every measured hybrid-versus-classical difference
(−2.0, +5.0, +2.0 ms) is smaller in magnitude than that noise floor. At this sample size, the
latency cost of the hybrid post-quantum key exchange is **not distinguishable from measurement
noise** on either Wi-Fi or cellular.

Two outliers were excluded and are retained in the raw logs: a 519,352 ms stall on the first
cellular pair (occurring during mobile network establishment, with no byte counts recorded) and a
single 546 ms handshake in the second cellular session. The first cellular session was repeated for
this reason; both sessions are reported.

## 12. Interpretation — revising the "network bottleneck" claim

The earlier draft asserted that transmitting PQC payloads over a congested mobile network "may add
on the order of 10–50 milliseconds of delay," and concluded that the bottleneck shifts from CPU to
network. The measurements support one half of that claim and refute the other.

**Supported: the network dominates end-to-end latency.** A complete handshake takes 94 ms on Wi-Fi
and 165–171 ms on cellular, against 35 µs of ML-KEM-768 computation measured in Phase 3 — a factor
of roughly 2,700× and 4,800× respectively. Even the bare RTT (30.6 ms) exceeds the cryptographic
computation by ~875×. Optimising post-quantum CPU cost cannot meaningfully improve mobile handshake
latency, because computation is not where the time goes.

**Refuted: the enlarged payload does not cost measurable latency.** Adding 2,266 bytes to the
handshake produced no detectable increase on either network. The most plausible mechanism is that
the enlarged ClientHello still fits within a single MTU-sized TCP segment, so no additional
round trip is introduced; this is consistent with ML-KEM-768 having been selected for hybrid TLS
partly on those grounds. **This explanation was not directly verified** — packet capture requires
privileges unavailable on the device — and is offered as the hypothesis most consistent with the
data rather than as a demonstrated mechanism.

The revised claim, which the data does support:

> Under the tested conditions, the end-to-end cost of a TLS 1.3 handshake on this device is
> dominated by network round-trip time, which exceeds the post-quantum cryptographic computation by
> approximately three orders of magnitude. The additional 2,266 bytes introduced by the
> `X25519MLKEM768` hybrid group increased total handshake size by 1.71× but produced no latency
> difference distinguishable from measurement noise (paired differences of −2 to +5 ms against a
> null-control noise floor of 7 ms). The constraint on post-quantum deployment in this scenario is
> therefore neither CPU nor handshake payload size.

## 13. Limitations of Phase 7

- Wall-clock includes non-TLS overhead; only paired differences are interpretable, and the design
  cannot isolate the TLS handshake itself without instrumentation unavailable here.
- A single endpoint (Cloudflare) on a well-provisioned CDN. Results may differ against origin
  servers, under packet loss, or on congested cells. No congestion or loss was induced.
- Cellular connection type (LTE vs 5G NR), band, and signal strength were not recorded;
  `termux-api` and `ip route` were both unavailable to the unprivileged process.
- n=25 pairs per condition bounds the detectable effect at roughly the 7 ms noise floor. A larger
  effect would have been detected; an effect below ~7 ms would not.
- No packet capture, so the single-segment ClientHello hypothesis is unverified.

## 14. Provenance (Phase 7)

Raw logs in `logs/phase7_tls/`: `p7_netcontext_*.log`, `p7_paired_wifi_*.log`,
`p7_nullcontrol_wifi_*.log`, `p7_paired_cellular_*.log` (two sessions). Each log is CSV-formatted
with per-handshake wall-clock, byte counts, and the negotiated group. Analysis in `p7.py`.
Negotiation of `X25519MLKEM768` was confirmed on every hybrid handshake via the
`Negotiated TLS1.3 group` field; handshakes that did not report the expected group would have been
excluded (none occurred).

---

# Phases 5 & 6 — Scheduler, DVFS, and Per-Core Characterisation

**Build:** liboqs `build-a64` throughout. **Algorithm:** ML-KEM-768.
**Date:** 2026-07-23, 20:31–22:20 local.

**Metric warning.** Two distinct metrics appear below and must not be mixed. liboqs `-f`
(`fullcycletest`) measures one integrated keygen→encaps→decaps loop; the Phase 4 and Phase 6
tables sum three separately-timed operations. The integrated loop benefits from cache locality the
separate loops do not, so the two are not interchangeable. Phase 5b uses `-f`; Phases 4 and 6 use
summed operations.

## 15. Core identification (MIDR_EL1)

| CPU | MIDR_EL1 | Part | Core | cpufreq policy | Max clock |
|---|---|---|---|---|---|
| 0–2 | `0x411fd461` | `0xd46` | Cortex-A510 | policy0 | 2016 MHz |
| 3–4 | `0x411fd4d0` | `0xd4d` | Cortex-A715 | policy3 | 2803 MHz |
| 5–6 | `0x412fd470` | `0xd47` | Cortex-A710 | policy3 | 2803 MHz |
| 7 | `0x411fd4e0` | `0xd4e` | Cortex-X3 | policy7 | 3360 MHz |

The mid cluster contains **two different microarchitectures sharing one frequency domain** —
2× Cortex-A715 and 2× Cortex-A710. This is not visible from `cpufreq` topology alone and enables
a controlled microarchitectural comparison at identical clock (§17).

## 16. Frequency validation of the pinned measurements

`scaling_cur_freq` was sampled every 100 ms throughout each pinned benchmark:

| Pinned CPU | Policy | min | median | max |
|---|---|---|---|---|
| 0 (A510) | policy0 | 2,016,000 | 2,016,000 | 2,016,000 |
| 3 (A715) | policy3 | 2,803,200 | 2,803,200 | 2,803,200 |
| 5 (A710) | policy3 | 2,803,200 | 2,803,200 | 2,803,200 |
| 7 (X3) | policy7 | 3,360,000 | 3,360,000 | 3,360,000 |

Every core held its maximum frequency for the entire duration, with zero variation across all
samples. The cycle-normalised figures in §17 are therefore measured rather than assumed, and the
comparison is not confounded by DVFS.

## 17. Per-core performance (ML-KEM-768, median of 5 runs, µs)

| Core | keygen | encaps | decaps | Full cycle | Speedup | Clock ratio | Work per cycle |
|---|---|---|---|---|---|---|---|
| Cortex-A510 @2016 | 59.56 | 66.43 | 76.74 | **202.73** | 1.00× | 1.00× | 1.00 |
| Cortex-A710 @2803 | 21.69 | 23.35 | 27.51 | **72.55** | 2.79× | 1.39× | 2.01 |
| Cortex-A715 @2803 | 20.89 | 22.52 | 26.45 | **69.86** | 2.90× | 1.39× | 2.09 |
| Cortex-X3 @3360 | 15.33 | 16.31 | 19.44 | **51.07** | 3.97× | 1.67× | **2.38** |

Affinity was verified per run: each log records `Cpus_allowed_list` immediately before the
benchmark, confirming the pin held.

**Microarchitecture dominates clock.** The Cortex-X3 delivers 3.97× the throughput of the
Cortex-A510 on only 1.67× the clock frequency; normalising for frequency leaves a 2.38× advantage
in work completed per cycle. The vectorised NTT and rejection-sampling code benefits
disproportionately from the wider issue width and larger vector execution resources of the
performance cores. Post-quantum key exchange is therefore not merely "faster on big cores" in
proportion to their clocks — it is architecturally favoured by them.

**A710 versus A715 at identical frequency.** Because both occupy policy3, the comparison isolates
microarchitecture with clock, thermal state, and memory subsystem held constant:

| Operation | A710 | A715 | A715 advantage |
|---|---|---|---|
| keygen | 21.687 | 20.886 | 3.84 % |
| encaps | 23.353 | 22.517 | 3.71 % |
| decaps | 27.511 | 26.452 | 4.00 % |
| full cycle | 72.551 | 69.855 | **3.86 %** |

The consistency across all three operations (3.71–4.00 %) indicates a systematic generational
improvement rather than measurement noise.

**Variance by core class.** Within-run population standard deviation on keygen was 18–29 µs on the
A510 (30–50 % of the mean) against 1.5–2.1 µs on the A715 and X3 (roughly 10 %). Cryptographic
latency on the efficiency cores is not only ~4× higher but substantially less predictable, since
those cores host background system work. Any latency budget derived from big-core measurements
will be violated when the workload lands on a little core.

## 18. Core-control behaviour during a sustained workload

A 10-second unpinned run was traced with a sampler sleeping 100 ms between samples (nominal
10 Hz); the raw trace (`data/p5a_trace.csv`) shows a median effective interval of 164 ms, the
excess being sysfs read latency on the sampling core. 408 samples cover 81.6 s of idle, load,
and ramp-down; the benchmark window (t = 5.0–14.9 s in the trace) is identified by the
contiguous block of prime-core maximum-frequency samples and matches the benchmark log's
wall-clock timestamps:

| Metric | Observation |
|---|---|
| Cortex-X3 `Paused: 1` | 266 / 408 samples (65 %) |
| Cortex-X3 `active_cpus: 0` | 270 / 408 samples (66 %) |
| policy7 at 864 MHz (idle floor) | 238 samples |
| policy7 at 3360 MHz (maximum) | 68 samples |
| policy3 at 2803 MHz (maximum) | 174 samples |
| policy0 at 1017 MHz | 247 samples |

The prime core was paused for roughly two-thirds of the trace — the idle periods before and after
the benchmark — and was resumed and driven to maximum frequency during the sustained workload.
Unpinned full-cycle performance (49.32 µs median, Phase 5b) is close to the X3-pinned measurement,
indicating that Android's scheduler does migrate a sustained foreground cryptographic workload onto
the prime core.

Retries were also required to pin cpu5 (3 retries on one run, 2 on another), confirming that
core-control pausing applies to mid-cluster cores as well as the prime core, not only to CPU 7.

## 19. Cold versus sustained execution — the "warm-up" hypothesis

The earlier draft reported a 4.6× improvement between a 3-second burst and a 10-second sustained
run, attributed to DVFS ramp-up. That comparison was confounded: in the original suite, ML-KEM-768
executed after approximately forty other algorithms had already loaded the CPU. The redesigned
experiment invokes a single algorithm per process, each preceded by five minutes of device idle.

| Duration | Runs (µs) | Median |
|---|---|---|
| 1 s | 54.32, 48.91, 48.80, 48.08, 48.18 | **48.80** |
| 10 s | 51.15, 49.32, 49.23, 49.23, 49.40 | **49.32** |

The difference is **+1.1 %, in the opposite direction** to the hypothesis. **No warm-up effect is
observable.** The reported 4.6× improvement was an artefact of the confounded experimental design
and does not survive controlled measurement.

The first run in each sequence is mildly elevated (54.32 and 51.15 µs), consistent with a small
first-invocation cost — page faults, binary load, core resume — of roughly 4–10 %, an order of
magnitude smaller than the effect originally claimed.

## 20. Application state and CPU allocation

Identical benchmark, identical build; the only variable is whether Termux is the foreground
application.

| | `Cpus_allowed_list` | keygen | encaps | decaps | full cycle |
|---|---|---|---|---|---|
| Foreground | `0-7` (all cores) | 14.70 | 15.91 | 19.01 | 49.63 µs |
| **Background** | **`0-2` (A510 only)** | 56.55 | 62.04 | 107.68 | 226.27 µs |
| Ratio | — | 3.85× | 3.90× | 5.66× | **4.56×** |

Android confines backgrounded applications to the efficiency-core cpuset. The background
decapsulation figure carries a population standard deviation of 5,936 µs (55× its mean), indicating
a scheduling stall during that measurement; the keygen and encapsulation pair, which are stable,
give a ratio of **3.87×** and should be preferred as the headline figure.

**This is the deployment-relevant result.** Both measurements were taken with the prime core
already paused (`Paused: 1` in both), so the difference is attributable to cpuset membership alone.
A messaging or synchronisation application performing post-quantum key exchange while backgrounded
— which is precisely when such work typically occurs — will experience approximately four times the
latency measured in foreground benchmarks. Benchmark figures obtained from a foreground process,
including every other figure in this report, therefore represent a best case that many real
deployments will not see.

Two distinct mechanisms have now been separately evidenced:

1. **Core-control pausing** (§18, and the affinity investigation): the prime core is withdrawn from
   the scheduler's active mask under idle, causing intermittent `EINVAL` on `sched_setaffinity`.
   Load-dependent and transient.
2. **Cpuset demotion** (this section): backgrounded applications are restricted to CPUs 0–2.
   Application-state-dependent and persistent while backgrounded.

The earlier draft attributed its failed affinity experiment to a blanket kernel prohibition. Neither
mechanism is a prohibition, and affinity control is fully available to unprivileged userspace in the
foreground.

## 21. Provenance (Phases 5 & 6)

`logs/phase5_dvfs/`: `p5a_freqtrace_*.log` (408-sample CSV trace), `p5a_fullcycle10s_*.log`,
`p5b_fc1s_run{1..5}_*.log`, `p5b_fc10s_run{1..5}_*.log`, `p5c_foreground_*.log`,
`p5c_background_*.log`.
`logs/phase6_percore/`: `p6_midr_*.log`, `p6_pin_cpu{0,3,5,7}_*.log` (5 runs each, each recording
`Cpus_allowed_list`), `p6_freq_during_pin_*.log`.

The frequency sampler is itself a process polling sysfs (nominal 100 ms period; ~164 ms effective) and may keep an efficiency core
active; this observer effect cannot be eliminated without root privileges and is noted as a
limitation.
