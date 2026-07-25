#!/data/data/com.termux/files/usr/bin/bash
# Phase 5a — 10 Hz sampler: per-policy frequency + prime-core core_ctl state. Run in background, kill when done.
echo "ts_s,policy0_khz,policy3_khz,policy7_khz,x3_active,x3_paused"
while true; do
  T=$(date +%s.%N)
  F0=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || echo NA)
  F3=$(cat /sys/devices/system/cpu/cpufreq/policy3/scaling_cur_freq 2>/dev/null || echo NA)
  F7=$(cat /sys/devices/system/cpu/cpufreq/policy7/scaling_cur_freq 2>/dev/null || echo NA)
  AC=$(cat /sys/devices/system/cpu/cpu7/core_ctl/active_cpus 2>/dev/null || echo NA)
  PA=$(grep -A4 "^CPU7" /sys/devices/system/cpu/cpu7/core_ctl/global_state 2>/dev/null | grep Paused | tr -dc '0-9')
  echo "$T,$F0,$F3,$F7,$AC,${PA:-NA}"
  sleep 0.1
done
