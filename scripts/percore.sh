#!/data/data/com.termux/files/usr/bin/bash
# Phase 6 — pinned per-core benchmark. usage: percore.sh <cpu> <runs>
# Busy-loop warm-up defeats core_ctl pausing; retry loop handles transient EINVAL;
# Cpus_allowed_list is printed inside the pinned process to prove the pin held.
C=$1; N=$2
B=~/liboqs/build-a64/tests/speed_kem
for i in $(seq 1 $N); do
  timeout 5 sh -c 'while :; do :; done' >/dev/null 2>&1   # wake target cluster
  ok=0
  for a in 1 2 3 4 5; do
    taskset -c $C true 2>/dev/null && { ok=1; break; }
    echo "[cpu$C paused, retry $a]"
    timeout 3 sh -c 'while :; do :; done' >/dev/null 2>&1
  done
  [ $ok -eq 0 ] && { echo "[FAILED cpu$C run$i]"; continue; }
  echo "=== cpu$C run$i ==="
  taskset -c $C sh -c "grep Cpus_allowed_list /proc/self/status; exec $B -d 3 ML-KEM-768"
  sleep 30
done
