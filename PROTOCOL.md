# PQC Benchmarking Runbook — Samsung Galaxy S23 (Snapdragon 8 Gen 2, ARMv9-A)

**Purpose:** Reproducible re-run of all benchmarks for the capstone project
*Benchmarking NIST Post-Quantum Cryptographic Standards on ARMv9-A Mobile Architectures*.
Every number reported in the thesis must trace to a timestamped log produced by this protocol.

**Ground rules**
1. Every command that produces data is piped through `tee` into `~/pqc-bench/logs/` with a timestamped filename.
2. Never edit a log. If a run is invalid (phone got hot, notification fired), mark it by renaming with suffix `_INVALID` and re-run.
3. Each phase ends with a **STOP checkpoint**: send the log for verification before continuing.
4. Log filename convention: `<phase>_<test>_<build>_run<N>_YYMMDD_HHMMSS.log`

---

## Phase 0 — Workspace and device preparation

```bash
mkdir -p ~/pqc-bench/{logs,scripts,results}
cd ~/pqc-bench
```

Device preparation checklist (repeat before EVERY benchmark phase, record in a `prep_*.txt` note):

- [ ] Battery ≥ 80%, NOT charging during runs (charging changes thermal/DVFS behavior)
- [ ] Airplane mode ON (except Phase 7, which needs network)
- [ ] All other apps closed (recent-apps cleared)
- [ ] Screen ON, Termux in foreground (foreground cpuset — this is a controlled variable, see Phase 5)
- [ ] Do Not Disturb ON
- [ ] Termux battery optimization disabled (Android Settings → Apps → Termux → Battery → Unrestricted)
- [ ] `termux-wake-lock` executed (prevents doze)
- [ ] Device idle ≥ 5 minutes before first run; ≥ 60 s cooldown between runs
- [ ] Ambient conditions noted (room temp approx., phone out of case)

Install prerequisites (one time):

```bash
pkg update
pkg install -y clang cmake ninja git openssl-tool android-tools termux-api
```

> `termux-api` is optional (battery/temperature readouts) and also requires the
> Termux:API companion app. If unavailable, note it and proceed.

---

## Phase 1 — Environment capture (the "who/what/where" of every result)

Create the capture script:

```bash
cat > ~/pqc-bench/scripts/envcap.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
echo "=== DATE ==="; date -u
echo "=== BUILD PROPS ==="
getprop ro.product.model
getprop ro.build.version.release
getprop ro.build.version.sdk
getprop ro.build.version.security_patch
getprop ro.board.platform
getprop ro.build.display.id
echo "=== KERNEL ==="; uname -a
echo "=== LSCPU ==="; lscpu
echo "=== CPUFREQ POLICIES ==="
for p in /sys/devices/system/cpu/cpufreq/policy*; do
  echo "--- $p ---"
  echo -n "related_cpus: ";      cat "$p/related_cpus" 2>/dev/null
  echo -n "governor: ";          cat "$p/scaling_governor" 2>/dev/null
  echo -n "min/max (kHz): ";     cat "$p/cpuinfo_min_freq" 2>/dev/null; cat "$p/cpuinfo_max_freq" 2>/dev/null
done
echo "=== ALLOWED CPUS (this process) ==="
grep -E "Cpus_allowed_list|Cpus_allowed" /proc/self/status
echo "=== THERMAL (may be restricted) ==="
for tz in /sys/class/thermal/thermal_zone*; do
  t=$(cat "$tz/type" 2>/dev/null); v=$(cat "$tz/temp" 2>/dev/null)
  [ -n "$v" ] && echo "$t: $v"
done
echo "=== BATTERY (needs termux-api) ==="
termux-battery-status 2>/dev/null || echo "termux-api not available"
echo "=== TOOLCHAIN ==="
clang --version | head -1
cmake --version | head -1
openssl version -a
EOF
chmod +x ~/pqc-bench/scripts/envcap.sh
~/pqc-bench/scripts/envcap.sh | tee ~/pqc-bench/logs/env_$(date +%y%m%d_%H%M%S).log
```

**Why:** resolves the Android-version inconsistency in the draft (methodology said Android 14;
the build targeted API 36), documents governors, and — via `Cpus_allowed_list` — gives the
first hard datum for the CPU-affinity investigation.

**STOP CHECKPOINT 1 — send `env_*.log` for review.**

---

## Phase 2 — Two liboqs builds (baseline + optimized ablation)

The original build produced `SHA-3: C` (software Keccak) with `-march=armv8-a+crypto` and
`OQS_OPT_TARGET=generic`. We rebuild twice to create a controlled comparison:

- **Build A (`build-generic`)** — replicates the original dispatch build (baseline).
- **Build B (`build-native`)** — compiled for the actual CPU, intended to activate the
  ARMv8.2 `FEAT_SHA3` Keccak path and any other native optimizations.

Deviations from your original build, both deliberate — document them in the thesis:
`CMAKE_BUILD_TYPE=Release` instead of `RelWithDebInfo` (removes `-g3`/frame-pointer overhead),
and `BUILD_SHARED_LIBS=OFF` (static binaries prevent one build accidentally loading the other
build's shared library, and make Phase 6's `adb push` trivial).

```bash
cd ~ && [ -d liboqs ] || git clone --depth 1 --branch 0.15.0 https://github.com/open-quantum-safe/liboqs.git
cd ~/liboqs

# --- Build A: baseline (dispatch/generic) ---
rm -rf build-generic && mkdir build-generic && cd build-generic
cmake -GNinja \
  -DOQS_DIST_BUILD=ON \
  -DOQS_OPT_TARGET=generic \
  -DBUILD_SHARED_LIBS=OFF \
  -DOQS_USE_OPENSSL=OFF \
  -DCMAKE_BUILD_TYPE=Release \
  -DOQS_ENABLE_KEM_NTRUPRIME=OFF \
  .. 2>&1 | tee ~/pqc-bench/logs/build_generic_cmake_$(date +%y%m%d_%H%M%S).log
ninja 2>&1 | tail -5 | tee ~/pqc-bench/logs/build_generic_ninja_$(date +%y%m%d_%H%M%S).log

# --- Build B: native (target = this CPU) ---
cd ~/liboqs
rm -rf build-native && mkdir build-native && cd build-native
cmake -GNinja \
  -DOQS_DIST_BUILD=OFF \
  -DOQS_OPT_TARGET=native \
  -DBUILD_SHARED_LIBS=OFF \
  -DOQS_USE_OPENSSL=OFF \
  -DCMAKE_BUILD_TYPE=Release \
  -DOQS_ENABLE_KEM_NTRUPRIME=OFF \
  .. 2>&1 | tee ~/pqc-bench/logs/build_native_cmake_$(date +%y%m%d_%H%M%S).log
ninja 2>&1 | tail -5 | tee ~/pqc-bench/logs/build_native_ninja_$(date +%y%m%d_%H%M%S).log
```

Verify what each build actually uses (the Configuration info block prints at the top of any run):

```bash
~/liboqs/build-generic/tests/speed_kem -d 1 ML-KEM-768 2>&1 | head -18 | tee ~/pqc-bench/logs/config_generic_$(date +%y%m%d_%H%M%S).log
~/liboqs/build-native/tests/speed_kem  -d 1 ML-KEM-768 2>&1 | head -18 | tee ~/pqc-bench/logs/config_native_$(date +%y%m%d_%H%M%S).log
```

**Decision tree at this checkpoint:**
- If Build B reports `SHA-3: C and ARM ...` (or any non-plain-C Keccak) → ablation is live; proceed.
- If Build B still reports `SHA-3: C` → retry Build B adding
  `-DCMAKE_C_FLAGS="-march=armv8.2-a+crypto+sha3"` to the cmake line.
- If it STILL reports `SHA-3: C` → liboqs 0.15 may not ship an ARM-SHA3 Keccak backend at all.
  That is itself a reportable finding ("the dominant Keccak workload runs in portable C even on
  FEAT_SHA3 hardware under the default toolchain"), and the A-vs-B comparison remains valid as
  a generic-vs-native ablation. We decide together how to frame it.

**STOP CHECKPOINT 2 — send both `config_*.log` files before any benchmarking.**

---## Phase 3 — Classical baseline (OpenSSL)

Five repetitions, 60 s cooldown between each:

```bash
for i in 1 2 3 4 5; do
  openssl speed ecdhp256 ecdsap256 ecdhx25519 ed25519 2>&1 \
    | tee ~/pqc-bench/logs/p3_openssl_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 60
done
```

`x25519`/`ed25519` are included because the hybrid recommendation in the thesis
(ML-KEM-768 + X25519) needs the X25519 number to compute the hybrid cost from your own data.

Optional (worth 2 minutes): OpenSSL 3.5+ implements ML-KEM/ML-DSA natively. Check:

```bash
openssl list -kem-algorithms      | tee ~/pqc-bench/logs/p3_openssl_kems_$(date +%y%m%d_%H%M%S).log
openssl list -signature-algorithms | tee ~/pqc-bench/logs/p3_openssl_sigs_$(date +%y%m%d_%H%M%S).log
```

If ML-KEM appears and `openssl speed` supports it on this build, we gain a free
**cross-library validation** (OpenSSL's ML-KEM vs liboqs's) — strong for the thesis. We check
the exact invocation together at the checkpoint.

**STOP CHECKPOINT 3 — send one `p3_openssl_run*.log`.**

---

## Phase 4 — Main benchmark matrix (the new Tables)

Matrix: 2 builds × {ML-KEM-512/768/1024} × 5 runs, and 2 builds × {ML-DSA-44/65/87} × 5 runs.
3-second duration per operation (liboqs default), 60 s cooldown between algorithms.

```bash
cat > ~/pqc-bench/scripts/matrix.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# usage: matrix.sh <build-dir-name>   e.g. matrix.sh build-generic
B=$1
for i in 1 2 3 4 5; do
  for alg in ML-KEM-512 ML-KEM-768 ML-KEM-1024; do
    ~/liboqs/$B/tests/speed_kem -d 3 "$alg" 2>&1 \
      | tee ~/pqc-bench/logs/p4_${B}_kem_${alg}_run${i}_$(date +%y%m%d_%H%M%S).log
    sleep 60
  done
  for alg in ML-DSA-44 ML-DSA-65 ML-DSA-87; do
    ~/liboqs/$B/tests/speed_sig -d 3 "$alg" 2>&1 \
      | tee ~/pqc-bench/logs/p4_${B}_sig_${alg}_run${i}_$(date +%y%m%d_%H%M%S).log
    sleep 60
  done
done
EOF
chmod +x ~/pqc-bench/scripts/matrix.sh

~/pqc-bench/scripts/matrix.sh build-generic   # session 1 (~1h with cooldowns)
~/pqc-bench/scripts/matrix.sh build-native    # session 2 (fresh prep checklist first)
```

Also re-run the two "boundary" algorithms for the feasibility argument (2 runs each is enough;
these are slow):

```bash
for i in 1 2; do
  ~/liboqs/build-generic/tests/speed_sig -d 3 SLH_DSA_PURE_SHAKE_128S 2>&1 \
    | tee ~/pqc-bench/logs/p4_slhdsa_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 60
  ~/liboqs/build-generic/tests/speed_kem -d 3 Classic-McEliece-8192128 2>&1 \
    | tee ~/pqc-bench/logs/p4_mceliece_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 120
done
```

**Reporting rule for the thesis:** each table cell = median of the 5 run-means, with min–max
(or IQR) across runs. State that liboqs's per-run stdev measures within-run jitter, while the
across-run spread measures reproducibility.

**STOP CHECKPOINT 4 — send the full `p4_*` log set; I will build the corrected results tables
with you and we diff them against the old draft's tables.**

---

## Phase 5 — Scheduler & DVFS characterization (redesigned "warm-up" experiment)

The original burst-vs-sustained comparison was confounded (ML-KEM ran after ~40 other
algorithms in the same suite, i.e., already warm). Replacement design: observe the mechanism
directly by logging per-cluster frequencies during a sustained run.

```bash
cat > ~/pqc-bench/scripts/freqlog.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Sample scaling_cur_freq for every policy every 100 ms until killed.
POLICIES=$(ls -d /sys/devices/system/cpu/cpufreq/policy* 2>/dev/null)
echo "timestamp $(for p in $POLICIES; do echo -n "$(basename $p) "; done)"
while true; do
  line="$(date +%s.%N)"
  for p in $POLICIES; do
    f=$(cat "$p/scaling_cur_freq" 2>/dev/null || echo NA)
    line="$line $f"
  done
  echo "$line"
  sleep 0.1
done
EOF
chmod +x ~/pqc-bench/scripts/freqlog.sh
```

Experiment 5a — frequency trace during a sustained full-cycle run (after ≥5 min idle):

```bash
~/pqc-bench/scripts/freqlog.sh > ~/pqc-bench/logs/p5_freq_during10s_$(date +%y%m%d_%H%M%S).log &
FL=$!
sleep 3   # capture idle baseline
~/liboqs/build-generic/tests/speed_kem -d 10 -f ML-KEM-768 2>&1 \
  | tee ~/pqc-bench/logs/p5_fullcycle10s_$(date +%y%m%d_%H%M%S).log
sleep 3   # capture ramp-down
kill $FL
```

Experiment 5b — short vs long duration, single algorithm, controlled idle (5 runs each):

```bash
for i in 1 2 3 4 5; do
  ~/liboqs/build-generic/tests/speed_kem -d 1  -f ML-KEM-768 2>&1 | tee ~/pqc-bench/logs/p5_fc1s_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 300   # 5 min idle so the next 1 s run starts from a comparable state
done
for i in 1 2 3 4 5; do
  ~/liboqs/build-generic/tests/speed_kem -d 10 -f ML-KEM-768 2>&1 | tee ~/pqc-bench/logs/p5_fc10s_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 300
done
```

Experiment 5c — foreground vs background cpuset (tests the hypothesis explaining the old
taskset failure). Start the script, then IMMEDIATELY press Home / turn the screen off; the
script waits 30 s so the app is demoted to the background cpuset before measuring:

```bash
cat > ~/pqc-bench/scripts/bgtest.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
sleep 30
echo "=== allowed cpus while backgrounded ==="
grep Cpus_allowed_list /proc/self/status
~/liboqs/build-generic/tests/speed_kem -d 3 ML-KEM-768
EOF
chmod +x ~/pqc-bench/scripts/bgtest.sh
termux-wake-lock
~/pqc-bench/scripts/bgtest.sh 2>&1 | tee ~/pqc-bench/logs/p5_background_$(date +%y%m%d_%H%M%S).log
# then repeat with Termux kept in the FOREGROUND for the control:
~/pqc-bench/scripts/bgtest.sh 2>&1 | tee ~/pqc-bench/logs/p5_foreground_$(date +%y%m%d_%H%M%S).log
```

If `Cpus_allowed_list` shrinks (e.g., to the A510 cores) when backgrounded, you have direct
evidence for the cpuset mechanism — and an honest, measured version of the draft's
"Intelligence-Driven Core Scheduling" recommendation.

**STOP CHECKPOINT 5 — send `p5_*` logs (especially the frequency trace; we will plot it).**

---

## Phase 6 — CPU affinity via `adb shell` (rescuing the failed taskset experiment)

The `shell` user is not confined to the app cpuset, so `taskset` may work where Termux's failed.
All on-device (Android 11+ Wireless debugging), no PC required:

1. Settings → Developer options → **Wireless debugging** → ON → **Pair device with pairing code**.
   Note the pairing `IP:PORT` and code, and the separate connection `IP:PORT`.
2. In Termux (split-screen helps, so the pairing dialog stays visible):

```bash
adb pair <IP:PAIR_PORT>        # enter the 6-digit code when prompted
adb connect <IP:CONN_PORT>
adb devices                    # should list the device as 'connected'

# Static binaries → single-file push:
adb push ~/liboqs/build-generic/tests/speed_kem /data/local/tmp/speed_kem_generic
adb push ~/liboqs/build-native/tests/speed_kem  /data/local/tmp/speed_kem_native
adb shell chmod +x /data/local/tmp/speed_kem_generic /data/local/tmp/speed_kem_native

# What may the shell user use?
adb shell "grep Cpus_allowed_list /proc/self/status" | tee ~/pqc-bench/logs/p6_shell_cpus_$(date +%y%m%d_%H%M%S).log

# Pin to the Cortex-X3 (cpu7) and to an A510 (cpu0) — 3 runs each:
for i in 1 2 3; do
  adb shell "taskset -c 7 /data/local/tmp/speed_kem_generic -d 3 ML-KEM-768" 2>&1 \
    | tee ~/pqc-bench/logs/p6_pin_X3_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 60
  adb shell "taskset -c 0 /data/local/tmp/speed_kem_generic -d 3 ML-KEM-768" 2>&1 \
    | tee ~/pqc-bench/logs/p6_pin_A510_run${i}_$(date +%y%m%d_%H%M%S).log
  sleep 60
done
```

Outcomes and how each serves the thesis:
- **Both pins work** → you finally get per-core-class numbers (X3 vs A510), directly answering
  RQ3, plus the finding "affinity is a privilege boundary, not a hardware limit."
- **cpu7 still fails under `adb shell`** → the restriction is deeper (kernel/cpuset config);
  document the exact error and the `Cpus_allowed_list` output — still a solid, now
  properly-evidenced finding.
- Also repeat the ORIGINAL failing command from Termux once, with correct syntax this time,
  and capture `Cpus_allowed_list` alongside it, so the thesis can show the Termux-vs-shell contrast:

```bash
grep Cpus_allowed_list /proc/self/status | tee ~/pqc-bench/logs/p6_termux_cpus_$(date +%y%m%d_%H%M%S).log
taskset -c 7 ~/liboqs/build-generic/tests/speed_kem -d 3 ML-KEM-768 2>&1 \
  | tee ~/pqc-bench/logs/p6_termux_pin7_$(date +%y%m%d_%H%M%S).log
```

**STOP CHECKPOINT 6 — send `p6_*` logs.**

---

## Phase 7 — Network reality check (turns the "bottleneck shifts to the network" claim into a measurement)

Airplane mode OFF for this phase; note network type (Wi-Fi vs 5G — ideally do both, labeled).
OpenSSL 3.5+ supports the hybrid group `X25519MLKEM768` in TLS 1.3, and major CDNs
(e.g., Cloudflare) negotiate it. We time repeated handshakes, hybrid-PQC vs classical, same host:

```bash
cat > ~/pqc-bench/scripts/tlstime.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# usage: tlstime.sh <host> <group> <n>
H=$1; G=$2; N=$3
for i in $(seq 1 $N); do
  S=$(date +%s.%N)
  echo | openssl s_client -connect "$H:443" -groups "$G" -brief 2>&1 | grep -E "Protocol|group|Cipher"
  E=$(date +%s.%N)
  echo "handshake_wallclock_s: $(echo "$E - $S" | bc)"
done
EOF
chmod +x ~/pqc-bench/scripts/tlstime.sh

# sanity check first: does this OpenSSL know the group, and does the host negotiate it?
echo | openssl s_client -connect cloudflare.com:443 -groups X25519MLKEM768 -brief 2>&1 | head -10

# then 20 handshakes per condition:
~/pqc-bench/scripts/tlstime.sh cloudflare.com X25519MLKEM768 20 | tee ~/pqc-bench/logs/p7_tls_pqc_$(date +%y%m%d_%H%M%S).log
~/pqc-bench/scripts/tlstime.sh cloudflare.com X25519        20 | tee ~/pqc-bench/logs/p7_tls_classical_$(date +%y%m%d_%H%M%S).log
```

Caveats to write into the methodology: wall-clock includes TCP + network RTT + server load
(hence 20 repetitions and median reporting); the *difference* between the two conditions on the
same host isolates the PQC handshake overhead. If `-groups X25519MLKEM768` is rejected by this
OpenSSL build, report it and we fall back to citing published deployment measurements instead —
but Termux ships OpenSSL 3.6.1, so it should work.

**STOP CHECKPOINT 7 — send `p7_*` logs. This single experiment upgrades the thesis's central
conclusion from speculation to evidence.**

---

## Phase 8 — Repository assembly

Suggested structure:

```
pqc-armv9-bench/
├── README.md                  # summary, device, headline results table, how to reproduce
├── PROTOCOL.md                # this runbook
├── env/                       # env_*.log, config_*.log
├── logs/
│   ├── phase3_openssl/
│   ├── phase4_matrix/
│   ├── phase5_dvfs/
│   ├── phase6_affinity/
│   └── phase7_tls/
├── scripts/                   # envcap.sh, matrix.sh, freqlog.sh, bgtest.sh, tlstime.sh
└── results/
    ├── tables.md              # every table cell annotated with its source log filename
    └── figures/
```

Rules that make the repo examiner-proof:
1. `results/tables.md` — each value carries a footnote naming the exact log file and line.
2. Never commit edited logs; raw only.
3. README states device model, Android build (`ro.build.display.id`), security patch,
   liboqs commit, and toolchain versions — all copied from `env_*.log`.
4. Add a short `DEVIATIONS.md` noting differences from the original capstone runs
   (Release vs RelWithDebInfo, static vs shared, single-alg invocation vs full suite) and why.

---

## Estimated effort

| Phase | Active time | Wall time |
|---|---|---|
| 0–1 Prep + env capture | 20 min | 20 min |
| 2 Two builds + verify | 15 min | ~40 min (compile) |
| 3 OpenSSL baseline | 5 min | ~30 min |
| 4 Main matrix (2 builds) | 15 min | ~2.5 h |
| 5 DVFS experiments | 20 min | ~1.5 h |
| 6 adb affinity | 30 min | 45 min |
| 7 TLS handshakes | 15 min | 30 min |
| 8 Repo assembly | 1–2 h | — |
