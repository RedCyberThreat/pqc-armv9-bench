#!/data/data/com.termux/files/usr/bin/bash
# Phase 5c — foreground vs background. Start, then either leave Termux on screen (control)
# or press Home immediately (treatment). 30 s sleep lets Android settle the lifecycle state.
sleep 30
echo "=== state at measurement time ==="
grep Cpus_allowed_list /proc/self/status
echo -n "x3_active_cpus: "; cat /sys/devices/system/cpu/cpu7/core_ctl/active_cpus 2>/dev/null
echo -n "policy7_khz: ";    cat /sys/devices/system/cpu/cpufreq/policy7/scaling_cur_freq 2>/dev/null
grep -A4 "^CPU7" /sys/devices/system/cpu/cpu7/core_ctl/global_state 2>/dev/null | grep -E "Paused|Busy%"
echo "=== benchmark ==="
~/liboqs/build-a64/tests/speed_kem -d 3 ML-KEM-768
