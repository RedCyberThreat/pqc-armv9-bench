"""Figure 4.4 (time-series version): per-cluster frequency and prime-core core_ctl
state across the idle-load-idle window, from the raw 10Hz-nominal trace p5a_trace.csv."""
import csv, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open('p5a_trace.csv')))
t0 = float(rows[0]['ts_s'])
t  = [float(r['ts_s'])-t0 for r in rows]
def mhz(col): return [int(r[col])/1000 if r[col] not in ('NA','') else None for r in rows]
f0, f3, f7 = mhz('policy0_khz'), mhz('policy3_khz'), mhz('policy7_khz')
paused = [r['x3_paused']=='1' for r in rows]

fig, ax = plt.subplots(figsize=(9,3.8), dpi=300)
# shade paused spans
i=0
first=True
while i < len(t):
    if paused[i]:
        j=i
        while j+1<len(t) and paused[j+1]: j+=1
        ax.axvspan(t[i], t[j], color='#fde8e6', zorder=0,
                   label='Cortex-X3 paused (core_ctl)' if first else None)
        first=False; i=j+1
    else: i+=1
# benchmark window (contiguous X3-at-max block: samples 5.0-14.9 s, matches log timestamps 20:31:38-20:31:48)
ax.axvspan(5.0, 14.9, color='#e8f0fe', zorder=0, label='10 s ML-KEM-768 benchmark')
ax.step(t, f0, where='post', lw=1.2, color='#2E7D32', label='policy0 (A510)')
ax.step(t, f3, where='post', lw=1.2, color='#ED7D31', label='policy3 (A710/A715)')
ax.step(t, f7, where='post', lw=1.6, color='#1f77b4', label='policy7 (X3)')
ax.set_xlabel('Time (s)'); ax.set_ylabel('Frequency (MHz)')
ax.set_xlim(0, max(t)); ax.set_ylim(0, 3600)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.set_title('Figure 4.4  Cluster frequencies and prime-core state across the idle–load–idle window', fontsize=11)
ax.legend(frameon=False, fontsize=8, ncol=2, loc='upper right')
fig.savefig('fig4_4_trace.png', bbox_inches='tight'); print('written')
