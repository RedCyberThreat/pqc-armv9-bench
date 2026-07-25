#!/data/data/com.termux/files/usr/bin/bash
# Phase 4 — main benchmark matrix. usage: matrix2.sh <build-dir>  e.g. matrix2.sh build-a64
# One algorithm per process invocation (avoids the suite-mode warm-up confound); 60 s cooldowns.
B=$1
L=~/pqc-bench/logs
for i in 1 2 3 4 5; do
  for a in ML-KEM-512 ML-KEM-768 ML-KEM-1024; do
    ~/liboqs/$B/tests/speed_kem -d 3 "$a" 2>&1 \
      | tee $L/p4_${B}_kem_${a}_run${i}_$(date +%y%m%d_%H%M%S).log
    sleep 60
  done
  for a in ML-DSA-44 ML-DSA-65 ML-DSA-87; do
    ~/liboqs/$B/tests/speed_sig -d 3 "$a" 2>&1 \
      | tee $L/p4_${B}_sig_${a}_run${i}_$(date +%y%m%d_%H%M%S).log
    sleep 60
  done
done
