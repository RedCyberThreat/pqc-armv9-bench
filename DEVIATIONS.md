# DEVIATIONS.md — Pilot Campaign vs Final Campaign

The project ran two measurement campaigns. The **pilot** (March–April 2026) established the
toolchain; an examiner-style review then found that several of its headline figures could not be
traced to raw logs, that its central hardware-acceleration claim was contradicted by its own build
configuration, and that two experiments were confounded. Rather than patching the pilot data, the
**final campaign** (23 July 2026) re-executed everything under a supervised protocol with per-phase
verification checkpoints. All figures in the thesis and in `RESULTS.md` derive from the final
campaign; pilot logs are retained under `logs/archive_pilot/` for the record and are cited only as
motivation.

## Configuration deviations (and their measured consequences)

| Parameter | Pilot | Final | Consequence |
|---|---|---|---|
| liboqs build type | `RelWithDebInfo` (`-O2 -g3 -fno-omit-frame-pointer`) | `Release` (`-O3 -fomit-frame-pointer`) | ≈22% latency shift (ML-KEM-768 keygen 28.4 → 20.5 µs); pilot and final numbers are NOT interchangeable |
| Linkage | Shared libraries | Static (`BUILD_SHARED_LIBS=OFF`) | No cross-build library contamination; enables single-file binary handling |
| Benchmark invocation | Full algorithm suite in one process | One algorithm per process | Removes the warm-up confound: ML-KEM ran ~40 algorithms deep in the pilot suite, on a pre-boosted CPU |
| Repetitions | 1 run per configuration | 5 runs per configuration, 60 s cooldowns | Across-run dispersion measurable; medians reported |
| Statistical unit | Single-run mean | Median of 5 run means [min–max] | Robust to scheduler-induced outliers (retained, not scrubbed) |
| OpenSSL | 3.6.1 | 3.6.3 | Version drift documented |
| Android version on record | "Android 14" (undocumented) | Android 16 / SDK 36, verified by `getprop` in Phase 1 | Pilot documentation error corrected by environment capture |
| liboqs provenance | "0.15.0" | main @ `04ab195f` (self-reports 0.15.0) | Same commit both campaigns; recorded precisely |
| Affinity experiment | Single failed attempt, wrong CLI syntax | Full per-core map, failure-state capture, retry protocol | Mechanism identified (core_ctl pause), claim corrected |
| Network claim | Asserted (10–50 ms, uncited) | Measured (paired sampling + null control) | Claim falsified; replaced by bounded null result |

## Pilot claims falsified by the final campaign

1. **"Sub-millisecond speed comes down to SHA-3 hardware extensions."** liboqs 0.15 ships no ARM
   Keccak implementation; `SHA-3: C` in every build banner. All results, both campaigns, ran
   software Keccak.
2. **"4.6× burst-to-sustained warm-up effect."** Under controlled single-algorithm invocation from
   5-minute idle: +1.1%, opposite direction. Artefact of suite-mode invocation.
3. **"The kernel did not allow any changes to CPU affinity."** Affinity is fully available;
   intermittent `EINVAL` is core_ctl pausing (captured in-state), and a separate cpuset demotion
   applies when backgrounded.
4. **"PQC payloads may add 10–50 ms on mobile networks."** No effect above a 7 ms measured noise
   floor on Wi-Fi or cellular; handshake size grows 1.71×, not orders of magnitude.
