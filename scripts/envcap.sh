#!/data/data/com.termux/files/usr/bin/bash
# Phase 1 — environment capture: device, kernel, topology, governors, toolchain.
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
