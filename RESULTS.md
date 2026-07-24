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
