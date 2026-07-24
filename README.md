# Benchmarking NIST Post-Quantum Cryptographic Standards on ARMv9-A Mobile Architectures

Measured performance of **ML-KEM (FIPS 203)** and **ML-DSA (FIPS 204)** on a production Android smartphone — Samsung Galaxy S23 (Qualcomm Snapdragon 8 Gen 2, ARMv9-A), Android 16 — with the platform's resource-management behaviour treated as an object of study rather than a nuisance variable.

This repository is the complete evidence chain for the BSc dissertation of the same title: every value in the thesis is traceable to a timestamped raw log in `logs/`, and every table and figure regenerates from `data/` via the scripts in `analysis/`.

## Headline results

| Finding | Measurement |
|---|---|
| **PQC key exchange is computationally *faster* than classical** | ML-KEM-768 encaps+decaps **34.7 µs** vs ECDH P-256 **42.8 µs** / X25519 **37.4 µs** |
| **Verification at parity** | ML-DSA-65 verify **56.4 µs** vs ECDSA P-256 **55.4 µs** (≈17,700 verifies/s, optimised build) |
| **Signing is the one real cost** | ML-DSA-65 sign **135 µs** vs ECDSA **17.6 µs** (7.7×) — and a wide distribution by construction (Fiat–Shamir aborts) |
| **Hybrid TLS 1.3 costs no measurable latency** | X25519MLKEM768 vs X25519 to cloudflare.com: paired differences −2 to +5 ms against a **null-control noise floor of 7 ms**; handshake grows **1.71×** (+2,266 B, matching FIPS 203 object sizes exactly) |
| **liboqs ships ARM assembly it never activates** | Enabling the aarch64 backends (undocumented per-algorithm flags) yields **1.2–1.9×**; 12 internal-control operations deviate ≤1.4% |
| **No ARM Keccak path exists in liboqs 0.15** | Device exposes FEAT_SHA3 on all 8 cores; library detects it, ships only AVX2/plain-C Keccak → **all results are lower bounds** |
| **The software supply chain dominates** | OpenSSL (Termux, `-Oz`) vs liboqs (`-O3`), same silicon, same day: up to **6.26×** on identical algorithms |
| **Backgrounding costs ~4×** | Android cpuset demotion to A510-only (`Cpus_allowed_list: 0-7 → 0-2`): full cycle 49.6 → 226.3 µs |
| **Microarchitecture beats clock** | Cortex-X3 vs A510, frequency-verified: 3.97× throughput on 1.67× clock = **2.38× work/cycle**; A715 vs A710 at identical clock: +3.9% |
| **The "affinity prohibition" was core_ctl pausing** | `EINVAL` on `taskset -c 7` captured concurrently with `Online: 1, Paused: 1, active_cpus: 0` |

Four claims of the project's own pilot study were falsified by this controlled re-measurement (SHA-3 acceleration attribution, a 4.6× warm-up effect, a kernel affinity prohibition, a 10–50 ms network payload penalty). The falsifications, and what replaced them, are documented in the thesis (Chapter 4, Table 4.7) and in `RESULTS.md`.

## Test platform

| Component | Value |
|---|---|
| Device | Samsung Galaxy S23 (SM-S911B, EU) |
| SoC | Snapdragon 8 Gen 2: 1× Cortex-X3 @3.36 GHz, 2× A715 + 2× A710 @2.80 GHz, 3× A510 @2.02 GHz (verified via MIDR_EL1) |
| OS | Android 16 (SDK 36), build BP4A.251205.006.S911BXXSAFZF5, kernel 5.15.189-android13-8, `walt` governor |
| Environment | Termux (unprivileged native userspace), Clang 21.1.8 |
| Libraries | liboqs main @ `04ab195f` (reports 0.15.0), static `-O3` builds; OpenSSL 3.6.3 (Termux pkg, `-Oz`) |

## Repository layout

```
PROTOCOL.md      Supervised runbook: 8 phases with STOP checkpoints, exact commands
RESULTS.md       Full phase-by-phase results and interpretation
DEVIATIONS.md    Pilot campaign vs final campaign: what changed and why
thesis/          Dissertation source (Markdown) and figures
logs/            Raw, unedited terminal logs, one file per run (the evidence)
data/            Transcribed per-run datasets (CSV)
scripts/         On-device measurement scripts (Termux bash)
analysis/        Python: computes every table and figure from data/
```

## Reproducing

On a comparable Android device with Termux:

```bash
pkg install -y clang cmake ninja git openssl-tool
git clone https://github.com/RedCyberThreat/pqc-armv9-bench && cd pqc-armv9-bench
# Follow PROTOCOL.md phase by phase (Phases 0–8).
```

To regenerate the analysis and figures from the archived data (any machine with Python 3 + matplotlib):

```bash
python3 analysis/analyze.py        # Phase 4 medians, ablation, controls
python3 analysis/p3.py             # classical baselines + cross-library
python3 analysis/p7.py             # TLS paired analysis vs null control
python3 analysis/make_figures.py   # Figures 4.1–4.5
```

Key methodological rules if you replicate: one algorithm per process (suite-mode invocation produces a warm-up confound); `openssl speed -elapsed` (wall-clock, matching liboqs); warm the target cluster before any `taskset` pin (core_ctl pauses idle cores → transient `EINVAL`); and never mix the integrated `-f` full-cycle metric with summed per-operation timings.

## Licensing

- **Code** (`scripts/`, `analysis/`): [MIT](LICENSE)
- **Data and text** (`logs/`, `data/`, `RESULTS.md`, `thesis/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Citation

See `CITATION.cff`, or cite as:

> Vignoli, M. (2026). *Benchmarking NIST post-quantum cryptographic standards on ARMv9-A mobile architectures* [BSc dissertation]. Data and code: https://github.com/RedCyberThreat/pqc-armv9-bench
