"""Generates Figures 4.1-4.5 for the dissertation from measured data.
Every number is transcribed from the raw logs (Phases 3-7)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import statistics as st

plt.rcParams.update({'font.size': 10, 'axes.titlesize': 11, 'axes.labelsize': 10,
                     'figure.dpi': 300, 'savefig.bbox': 'tight',
                     'axes.spines.top': False, 'axes.spines.right': False})
C_GEN, C_A64, C_CTRL, C_ACC = '#7f7f7f', '#1f77b4', '#c7c7c7', '#d62728'

# ---------------- Figure 4.1: Ablation with internal controls ----------------
ops = ['ML-KEM-512\nkeygen','ML-KEM-512\nencaps','ML-KEM-512\ndecaps',
       'ML-KEM-768\nkeygen','ML-KEM-768\nencaps','ML-KEM-768\ndecaps',
       'ML-KEM-1024\nkeygen','ML-KEM-1024\nencaps','ML-KEM-1024\ndecaps',
       'ML-DSA-44\nkeypair','ML-DSA-44\nsign','ML-DSA-44\nverify',
       'ML-DSA-65\nkeypair','ML-DSA-65\nsign','ML-DSA-65\nverify',
       'ML-DSA-87\nkeypair','ML-DSA-87\nsign','ML-DSA-87\nverify']
gen = [11.982,12.742,15.207, 20.539,19.822,23.236, 31.283,29.282,34.246,
       41.811,160.766,46.076, 77.763,253.982,74.095, 117.435,314.977,123.065]
a64 = [12.080,12.852,15.314, 14.606,15.737,18.908, 31.261,29.685,34.527,
       41.767,162.177,46.164, 58.026,135.175,56.406, 117.124,315.675,123.218]
treated = [False]*3+[True]*3+[False]*3+[False]*3+[True]*3+[False]*3
speedup = [g/a for g,a in zip(gen,a64)]

fig, ax = plt.subplots(figsize=(9,3.6))
x = np.arange(len(ops))
cols = [C_ACC if t else C_CTRL for t in treated]
ax.bar(x, speedup, color=cols, width=0.7)
ax.axhline(1.0, color='k', lw=0.8)
ax.axhspan(1-0.0138, 1+0.0138, color='0.85', zorder=0)
ax.set_xticks(x); ax.set_xticklabels(ops, rotation=90, fontsize=7)
ax.set_ylabel('Speedup (generic / a64)')
ax.set_ylim(0.9, 2.0)
ax.set_title('Figure 4.1  Backend ablation: aarch64 assembly speedup, with internal controls')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=C_ACC,label='Treated (aarch64 backend enabled)'),
                   Patch(color=C_CTRL,label='Control (identical C in both arms)'),
                   Patch(color='0.85',label='Control noise band (±1.38%)')],
          frameon=False, fontsize=8, loc='upper left')
fig.savefig('figs/fig4_1_ablation.png'); plt.close(fig)

# ---------------- Figure 4.2: Latency vs security category ----------------
fig, (a1,a2) = plt.subplots(1,2, figsize=(8,3.2))
cat_kem=[1,3,5]
a1.plot(cat_kem,[11.982,20.539,31.283],'o-',label='keygen')
a1.plot(cat_kem,[12.742,19.822,29.282],'s-',label='encaps')
a1.plot(cat_kem,[15.207,23.236,34.246],'^-',label='decaps')
a1.set_title('ML-KEM (portable C)'); a1.set_xlabel('NIST security category')
a1.set_ylabel('Median latency (µs)'); a1.set_xticks(cat_kem); a1.legend(frameon=False, fontsize=8)
cat_dsa=[2,3,5]
a2.plot(cat_dsa,[41.811,77.763,117.435],'o-',label='keypair')
a2.plot(cat_dsa,[160.766,253.982,314.977],'s-',label='sign')
a2.plot(cat_dsa,[46.076,74.095,123.065],'^-',label='verify')
a2.set_title('ML-DSA (portable C)'); a2.set_xlabel('NIST security category')
a2.set_xticks(cat_dsa); a2.legend(frameon=False, fontsize=8)
fig.suptitle('Figure 4.2  Latency scaling across security categories', y=1.02)
fig.tight_layout(); fig.savefig('figs/fig4_2_categories.png'); plt.close(fig)

# ---------------- Figure 4.3: Per-core hierarchy ----------------
cores=['Cortex-A510\n2016 MHz','Cortex-A710\n2803 MHz','Cortex-A715\n2803 MHz','Cortex-X3\n3360 MHz']
full=[202.73,72.55,69.86,51.07]; wpc=[1.00,2.01,2.09,2.38]
fig, ax = plt.subplots(figsize=(6.5,3.6))
b=ax.bar(cores, full, color=['#9edae5','#aec7e8','#6baed6','#1f77b4'], width=0.6)
for r,v in zip(b,full): ax.text(r.get_x()+r.get_width()/2, v+3, f'{v:.1f} µs', ha='center', fontsize=8)
ax.set_ylabel('ML-KEM-768 full cycle (µs)'); ax.set_ylim(0,230)
ax2=ax.twinx(); ax2.spines['right'].set_visible(True)
ax2.plot(cores, wpc, 'o--', color=C_ACC, label='Work per cycle (A510 = 1.00)')
for i,v in enumerate(wpc): ax2.annotate(f'{v:.2f}×', (i, v), textcoords='offset points', xytext=(0,8),
                                        ha='center', color=C_ACC, fontsize=8)
ax2.set_ylabel('Work per cycle (normalised)', color=C_ACC); ax2.set_ylim(0.8,2.7)
ax2.tick_params(axis='y', colors=C_ACC)
ax.set_title('Figure 4.3  Per-core performance, pinned, frequency-verified (median of 5)')
fig.savefig('figs/fig4_3_cores.png'); plt.close(fig)

# ---------------- Figure 4.4: Platform state occupancy during idle-load-idle window ----------------
# From the 408-sample 10 Hz trace (counts transcribed from p5a summary).
fig, (a1,a2) = plt.subplots(1,2, figsize=(8,3.2), gridspec_kw={'width_ratios':[2.2,1]})
labels=['policy0\n(A510)','policy3\n(A710/A715)','policy7\n(X3)']
# occupancy fractions of 408 samples; 'other' = remaining minor bins beyond top-5 in logs
p0={'2016 (max)':144,'1018':247,'other':17}
p3={'2803 (max)':174,'1286':61,'2189':20,'2054':20,'614':36,'other':97}
p7={'3360 (max)':68,'1248':69,'1133':8,'998':19,'864 (floor)':238,'other':6}
def stack(axis, x, d, cmap):
    bottom=0
    colors=plt.cm.get_cmap(cmap)(np.linspace(0.85,0.3,len(d)))
    for (k,v),c in zip(d.items(),colors):
        axis.bar(x, v/408*100, bottom=bottom, color=c, width=0.55,
                 label=None)
        if v/408>0.08: axis.text(x, bottom+v/408*50, k, ha='center', va='center', fontsize=7)
        bottom+=v/408*100
stack(a1,0,p0,'Greens'); stack(a1,1,p3,'Oranges'); stack(a1,2,p7,'Blues')
a1.set_xticks([0,1,2]); a1.set_xticklabels(labels, fontsize=8)
a1.set_ylabel('Share of samples (%)'); a1.set_ylim(0,100)
a1.set_title('Frequency-state occupancy (MHz)')
a2.bar(['Active','Paused'],[142/408*100,266/408*100],color=['#1f77b4','#d62728'],width=0.55)
a2.set_ylim(0,100); a2.set_title('Cortex-X3 core_ctl state')
for i,v in enumerate([142/408*100,266/408*100]): a2.text(i,v+2,f'{v:.0f}%',ha='center',fontsize=8)
fig.suptitle('Figure 4.4  Platform state across the idle–load–idle window (408 samples @ 10 Hz)', y=1.03)
fig.tight_layout(); fig.savefig('figs/fig4_4_occupancy.png'); plt.close(fig)

# ---------------- Figure 4.5: TLS paired differences vs null control ----------------
wifi_pqc=[86,84,95,113,95,121,108,92,126,88,95,96,92,85,93,90,101,88,83,89,95,111,95,94,93]
wifi_cls=[96,89,109,96,101,96,107,90,109,124,89,86,91,83,77,102,157,89,94,100,92,94,110,89,99]
null_a=[105,83,93,108,119,85,82,94,100,100,91,129,84,101,120]
null_b=[83,101,90,101,84,116,93,95,96,86,93,79,81,110,96]
c1_pqc=[135,134,173,165,163,165,141,147,143,151,182,159,174,190,165,204,181,170,173,137,187,179,153,176]
c1_cls=[228,134,138,173,148,148,160,154,182,151,150,140,158,164,186,147,165,185,181,283,309,146,143,208,196]
c2_pqc=[187,186,175,163,144,182,162,158,151,138,158,170,190,197,165,131,143,204,159,182,212,203,172,236]
c2_cls=[162,150,161,172,155,178,177,142,163,150,163,144,181,179,156,169,181,197,180,188,195,181,157,142,209]
def pdiff(a,b): 
    n=min(len(a),len(b)); return [a[i]-b[i] for i in range(n)]
data=[pdiff(null_a,null_b), pdiff(wifi_pqc,wifi_cls), pdiff(c1_pqc,c1_cls), pdiff(c2_pqc,c2_cls)]
labels=['Null control\n(X25519 vs X25519)','Wi-Fi\n(hybrid − classical)','Cellular 1\n(hybrid − classical)','Cellular 2\n(hybrid − classical)']
fig, ax = plt.subplots(figsize=(7,3.6))
bp=ax.boxplot(data, labels=labels, showmeans=False, medianprops=dict(color=C_ACC,lw=2))
ax.axhline(0,color='k',lw=0.8)
ax.axhspan(-7,7,color='0.88',zorder=0)
ax.set_ylabel('Per-pair wall-clock difference (ms)')
ax.set_title('Figure 4.5  TLS 1.3 paired handshake differences against the null-control noise floor')
ax.text(0.99,0.03,'shaded band: ±7 ms null-control median difference',transform=ax.transAxes,
        ha='right',fontsize=8,color='0.35')
ax.tick_params(axis='x', labelsize=8)
fig.savefig('figs/fig4_5_tls.png'); plt.close(fig)

print("done")
