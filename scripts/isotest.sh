#!/data/data/com.termux/files/usr/bin/bash
# Phase 1f — capture core_ctl state concurrently with a failing affinity call.
# Idle 90 s, read CPU7 state IMMEDIATELY before the pin attempt, attempt, read again.
echo "=== idling 90s — do not touch the phone ==="
sleep 90
echo "--- state captured BEFORE pin attempt ---"
date +%H:%M:%S.%3N
echo -n "isolated: [";  cat /sys/devices/system/cpu/isolated 2>/dev/null | tr -d '\n'; echo "]"
echo -n "active_cpus: "; cat /sys/devices/system/cpu/cpu7/core_ctl/active_cpus 2>/dev/null
echo -n "policy7 freq: "; cat /sys/devices/system/cpu/cpufreq/policy7/scaling_cur_freq 2>/dev/null
grep -A6 "^CPU7" /sys/devices/system/cpu/cpu7/core_ctl/global_state 2>/dev/null | grep -E "Online|Paused|Busy%|Nr running|Active CPUs"
echo "--- pin attempt ---"
taskset -c 7 true 2>&1 && echo "RESULT: OK" || echo "RESULT: FAIL"
echo "--- state captured AFTER ---"
grep -A6 "^CPU7" /sys/devices/system/cpu/cpu7/core_ctl/global_state 2>/dev/null | grep -E "Online|Paused|Active CPUs"
