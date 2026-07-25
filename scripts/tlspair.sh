#!/data/data/com.termux/files/usr/bin/bash
# Phase 7 — paired TLS 1.3 handshake sampling. usage: tlspair.sh <host> <n_pairs> <groupA> <groupB> <label>
# Alternating pairs sample the same network state; byte counts are deterministic;
# run with groupA==groupB for the null control that establishes the noise floor.
H=$1; N=$2; GA=$3; GB=$4; LBL=$5
echo "host=$H pairs=$N A=$GA B=$GB network=$LBL started=$(date -u +%FT%TZ)"
echo "pair,group,wallclock_ms,read_bytes,written_bytes,negotiated"
for i in $(seq 1 $N); do
  for G in "$GA" "$GB"; do
    S=$(date +%s%N)
    OUT=$(echo | openssl s_client -connect "$H:443" -groups "$G" -tls1_3 2>&1)
    E=$(date +%s%N)
    MS=$(( (E - S) / 1000000 ))
    RD=$(echo "$OUT" | grep -o "handshake has read [0-9]*" | grep -o "[0-9]*")
    WR=$(echo "$OUT" | grep -o "written [0-9]* bytes" | grep -o "[0-9]*")
    NEG=$(echo "$OUT" | grep -i "Negotiated TLS1.3 group" | sed 's/.*group: *//')
    echo "$i,$G,$MS,${RD:-NA},${WR:-NA},${NEG:-NA}"
    sleep 2
  done
done
