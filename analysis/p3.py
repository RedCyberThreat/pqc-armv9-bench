import statistics as st

# ops/s from 5 runs -> microseconds
def us(ops): return [1e6/o for o in ops]
def med(ops): return st.median(us(ops))
def rng(ops):
    u=us(ops); return f"[{min(u):.2f}-{max(u):.2f}]"

classical = {
 ('ECDSA P-256','sign')   : [56243.7,56851.8,57035.0,52668.3,56803.5],
 ('ECDSA P-256','verify') : [18016.5,18055.5,18047.2,17714.1,18043.0],
 ('ECDH P-256','derive')  : [23418.4,23411.3,23378.2,23092.6,23211.8],
 ('X25519','derive')      : [26734.4,26585.7,26794.8,26568.7,26726.9],
 ('Ed25519','sign')       : [28872.7,28602.1,28730.5,28481.1,28562.8],
 ('Ed25519','verify')     : [11092.0,11386.7,11466.1,11275.5,11110.5],
}
ossl_kem = {
 ('ML-KEM-512','keygen'): [42382.0,43422.3,42930.3,43130.7,43270.3],
 ('ML-KEM-512','encaps'): [51738.7,51786.7,51762.7,51434.0,51485.7],
 ('ML-KEM-512','decaps'): [32224.3,32321.7,32752.0,32656.0,32663.7],
 ('ML-KEM-768','keygen'): [26045.0,25803.7,26155.3,26132.0,26123.3],
 ('ML-KEM-768','encaps'): [35165.7,35271.0,35129.7,35140.3,35075.7],
 ('ML-KEM-768','decaps'): [22929.0,23065.7,23004.3,22922.0,22942.0],
 ('ML-KEM-1024','keygen'):[17499.3,17533.3,17439.3,17384.7,17389.0],
 ('ML-KEM-1024','encaps'):[25979.3,25877.0,25820.3,25764.7,25730.0],
 ('ML-KEM-1024','decaps'):[17335.3,17330.0,17231.3,17156.3,17142.7],
}
ossl_sig = {
 ('ML-DSA-44','keygen'):[11797.0,11880.0,11828.0,11750.3,11639.3],
 ('ML-DSA-44','sign')  :[2019.7,2052.3,2034.3,2010.7,1963.7],
 ('ML-DSA-44','verify'):[10549.0,10544.0,10512.3,10453.7,10403.7],
 ('ML-DSA-65','keygen'):[6664.3,6654.0,6642.7,6616.7,6598.7],
 ('ML-DSA-65','sign')  :[1196.0,1181.3,1157.7,1181.3,1177.7],
 ('ML-DSA-65','verify'):[6746.7,6723.3,6701.0,6683.0,6684.0],
 ('ML-DSA-87','keygen'):[4364.0,4360.0,4303.0,4289.7,4340.7],
 ('ML-DSA-87','sign')  :[1018.7,1004.3,1010.0,1024.3,995.7],
 ('ML-DSA-87','verify'):[4071.7,4066.3,4047.7,4041.3,4051.7],
}

print("=== CLASSICAL BASELINE (OpenSSL 3.6.3, -elapsed, 5 runs) ===")
for k,v in classical.items():
    print(f"  {k[0]:<14}{k[1]:<8}{med(v):>9.3f} us  {rng(v)}")

print("\n=== OPENSSL NATIVE PQC ===")
for d in (ossl_kem, ossl_sig):
    for k,v in d.items():
        print(f"  {k[0]:<14}{k[1]:<8}{med(v):>9.3f} us  {rng(v)}")

# liboqs medians from Phase 4
liboqs = {
 ('ML-KEM-512','generic'):(11.982,12.742,15.207), ('ML-KEM-512','a64'):(12.080,12.852,15.314),
 ('ML-KEM-768','generic'):(20.539,19.822,23.236), ('ML-KEM-768','a64'):(14.606,15.737,18.908),
 ('ML-KEM-1024','generic'):(31.283,29.282,34.246),('ML-KEM-1024','a64'):(31.261,29.685,34.527),
 ('ML-DSA-44','generic'):(41.811,160.766,46.076),('ML-DSA-44','a64'):(41.767,162.177,46.164),
 ('ML-DSA-65','generic'):(77.763,253.982,74.095),('ML-DSA-65','a64'):(58.026,135.175,56.406),
 ('ML-DSA-87','generic'):(117.435,314.977,123.065),('ML-DSA-87','a64'):(117.124,315.675,123.218),
}
print("\n=== CROSS-LIBRARY: liboqs vs OpenSSL (same device, same day) ===")
print(f"{'alg':<13}{'op':<8}{'liboqs-C':>10}{'liboqs-a64':>12}{'OpenSSL':>10}{'OSSL/best':>11}")
for a in ['ML-KEM-512','ML-KEM-768','ML-KEM-1024']:
    for i,o in enumerate(['keygen','encaps','decaps']):
        g=liboqs[(a,'generic')][i]; n=liboqs[(a,'a64')][i]; s=med(ossl_kem[(a,o)])
        print(f"{a:<13}{o:<8}{g:>10.2f}{n:>12.2f}{s:>10.2f}{s/min(g,n):>10.2f}x")
for a in ['ML-DSA-44','ML-DSA-65','ML-DSA-87']:
    for i,o in enumerate(['keygen','sign','verify']):
        g=liboqs[(a,'generic')][i]; n=liboqs[(a,'a64')][i]; s=med(ossl_sig[(a,o)])
        print(f"{a:<13}{o:<8}{g:>10.2f}{n:>12.2f}{s:>10.2f}{s/min(g,n):>10.2f}x")

print("\n=== CLASSICAL vs PQC (best liboqs = a64) ===")
ec_s=med(classical[('ECDSA P-256','sign')]); ec_v=med(classical[('ECDSA P-256','verify')])
ecdh=med(classical[('ECDH P-256','derive')]); x=med(classical[('X25519','derive')])
kem_ex = liboqs[('ML-KEM-768','a64')][1]+liboqs[('ML-KEM-768','a64')][2]
kem_full = sum(liboqs[('ML-KEM-768','a64')])
dsa_s=liboqs[('ML-DSA-65','a64')][1]; dsa_v=liboqs[('ML-DSA-65','a64')][2]
print(f"  SIGNING : ECDSA {ec_s:.2f} us  vs  ML-DSA-65 {dsa_s:.2f} us   -> PQC {dsa_s/ec_s:.2f}x SLOWER")
print(f"  VERIFY  : ECDSA {ec_v:.2f} us  vs  ML-DSA-65 {dsa_v:.2f} us   -> PQC {dsa_v/ec_v:.2f}x  (parity)")
print(f"  KEX     : ECDH-P256 {ecdh:.2f} us  vs  ML-KEM-768 encaps+decaps {kem_ex:.2f} us -> PQC {kem_ex/ecdh:.2f}x (FASTER)")
print(f"  KEX     : X25519 {x:.2f} us  vs  ML-KEM-768 encaps+decaps {kem_ex:.2f} us -> PQC {kem_ex/x:.2f}x (FASTER)")
print(f"  HYBRID  : X25519 + ML-KEM-768 full cycle = {x+kem_full:.2f} us")
