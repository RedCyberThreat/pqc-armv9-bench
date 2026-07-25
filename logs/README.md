# logs/ — raw evidence

Every quantitative claim in the thesis traces to a timestamped log in this directory.
Logs are raw terminal captures via `tee`; none has been edited. Invalid runs, where they
occurred, were renamed with an `_INVALID` suffix and repeated rather than deleted.

## Layout

```
phase1_env/        Environment captures, affinity mapping, core_ctl probes,
                   the isolation-proof capture (Paused:1 concurrent with EINVAL)
phase2_builds/     cmake/ninja transcripts and configuration banners for
                   build-generic, build-native (SIGILL, excluded), build-a64,
                   and the build-provenance capture (CMakeCache + aarch64 source counts)
phase3_openssl/    Classical baselines and OpenSSL-native ML-KEM/ML-DSA (5 runs each)
phase4_matrix/     Main matrix: 2 builds x 6 algorithms x 5 runs (60 files)
phase5_dvfs/       10 Hz frequency trace, cold-vs-sustained runs, foreground/background
phase6_percore/    MIDR reads, pinned runs per core (Cpus_allowed_list recorded in each),
                   frequency-during-pin validation
phase7_tls/        Network context, paired Wi-Fi/cellular sessions, null control
archive_pilot/     March-April 2026 pilot logs — retained for the record, superseded;
                   see DEVIATIONS.md. Not used for any figure in the thesis.
```

## Filename convention

`<phase>_<build>_<test>_run<N>_<YYMMDD_HHMMSS>.log` — build identity is carried by the
filename because the generic and a64 builds print byte-identical configuration banners.

> Note: the log corpus lives on the measurement device (`~/pqc-bench/logs/`) and is
> committed from there. If this directory contains only this README, the upload from the
> device is still pending.
