#!/usr/bin/env python3
"""SB-AKE measurement-informed endpoint cost model.
Source: Karcz et al., PLOS ONE 21(8), e0355179 (2026), Tables 5,7,8.
The published primitive marginal means/SDs are used as inputs. Independence,
lognormal/gamma distributional families, and symmetric setup costs are model
assumptions, NOT claims that raw ESP32-C6 traces were available.
No physical PUF, energy, complete hardware-memory or network timings modeled.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent / 'SB_AKE_repro_outputs'
OUT.mkdir(exist_ok=True)
SEED=20260924
RUNS=10_000
NS=[1,2,3,5,10]
EX_MEAN=10.; EX_SD=1.
P={
 'P1: ML-KEM-512 + ML-DSA-44':dict(kem_keygen=(110.973,12.250),kem_encap=(114.417,11.596),kem_decap=(138.346,12.404),dsa_keygen=(424.142,19.790),dsa_sign=(893.759,541.178),dsa_verify=(407.182,18.309),combined=(2076.737,689.030)),
 'P2: ML-KEM-768 + ML-DSA-65':dict(kem_keygen=(183.672,14.754),kem_encap=(183.099,14.119),kem_decap=(219.474,15.197),dsa_keygen=(768.171,16.285),dsa_sign=(1259.740,481.598),dsa_verify=(713.344,16.873),combined=(3498.105,649.988)),
}
OPS=('kem_keygen','kem_encap','kem_decap','dsa_keygen','dsa_sign','dsa_verify')
EXCH=('kem_keygen','kem_encap','kem_decap','dsa_sign','dsa_verify')

def sample(rng,mean,sd,size,distribution='lognormal'):
 if distribution=='lognormal':
  v=np.log(1+(sd/mean)**2);return rng.lognormal(np.log(mean)-v/2,np.sqrt(v),size=size)
 if distribution=='gamma':
  return rng.gamma((mean/sd)**2,sd**2/mean,size=size)
 raise ValueError(distribution)

def draw(rng,p,k,size,distribution):return sample(rng,*p[k],size,distribution)

def run(rng,distribution='lognormal',runs=RUNS,exp_mean=EX_MEAN,exp_sd=EX_SD,full_data=False):
 rows=[];raw=[]
 for profile,p in P.items():
  for n in NS:
   keygen=draw(rng,p,'dsa_keygen',runs,distribution)
   first=sum(draw(rng,p,key,runs,distribution) for key in EXCH)
   # Equal *slice-context installation* cost for both candidates: SB uses
   # HKDF context expansion; independent variant uses standalone KDF + state.
   # This is an assumption, evaluated under zero-setup-baseline stress below.
   expansion=sample(rng,exp_mean,exp_sd,(runs,n),distribution).sum(axis=1)
   sb=keygen+first+expansion
   ind=keygen+first+expansion
   for _ in range(1,n):
    ind+=sum(draw(rng,p,key,runs,distribution) for key in EXCH)
   saving=100*(1-sb/ind)
   rows.append(dict(Profile=profile,N_slices=n,SB_AKE_mean_ms=sb.mean(),SB_AKE_median_ms=np.median(sb),SB_AKE_p95_ms=np.quantile(sb,.95),Independent_mean_ms=ind.mean(),Independent_median_ms=np.median(ind),Amortized_mean_ms_per_slice=(sb/n).mean(),Gain_from_mean_totals_pct=100*(1-sb.mean()/ind.mean()),Paired_gain_median_pct=np.median(saving),Paired_gain_p05_pct=np.quantile(saving,.05),Paired_gain_p95_pct=np.quantile(saving,.95)))
   if full_data:
    raw.append(pd.DataFrame(dict(Profile=profile,run=np.arange(1,runs+1),N_slices=n,SB_AKE_ms=sb,Independent_ms=ind,Amortized_ms_per_slice=sb/n,Paired_gain_pct=saving)))
 return pd.DataFrame(rows),pd.concat(raw,ignore_index=True) if raw else None

base,runs_data=run(np.random.default_rng(SEED),full_data=True)
base.to_csv(OUT/'main_10000_summary.csv',index=False)
runs_data.to_csv(OUT/'main_10000_raw.csv',index=False)
cal=[]
for profile,p in P.items():
 total=sum(p[o][0] for o in OPS)
 cal.append(dict(profile=profile,reconstructed_ms=total,published_combined_ms=p['combined'][0],discrepancy_pct=100*(total/p['combined'][0]-1),independent_sd_ms=np.sqrt(sum(p[o][1]**2 for o in OPS)),combined_reported_sd_ms=p['combined'][1]))
pd.DataFrame(cal).to_csv(OUT/'operation_calibration.csv',index=False)
# Analytic expectation and broad sensitivity: not MC measurements.
sweeps=[]
for name,p in P.items():
 key=p['dsa_keygen'][0];exchange=sum(p[o][0] for o in EXCH)
 for n in [2,3,5,10]:
  for ex in [1,5,10,25,50,100,250,500,1000]:
   sb=key+exchange+n*ex
   ind=key+n*exchange+n*ex
   no_baseline_install=key+n*exchange # adversarially favorable zero installation baseline
   sweeps.append(dict(profile=name,N=n,assumed_per_slice_ms=ex,shared_setup_gain_pct=100*(1-sb/ind),zero_baseline_setup_gain_pct=100*(1-sb/no_baseline_install)))
sweep=pd.DataFrame(sweeps);sweep.to_csv(OUT/'wide_sensitivity_analytic.csv',index=False)
# Paired distribution-family check using independently seeded gamma simulations.
gamma,_=run(np.random.default_rng(SEED+1),distribution='gamma',full_data=False)
robust=base.merge(gamma,on=['Profile','N_slices'],suffixes=('_lognormal','_gamma'))
robust['delta_p95_ms']=robust.SB_AKE_p95_ms_gamma-robust.SB_AKE_p95_ms_lognormal
robust['delta_gain_percentage_points']=robust.Gain_from_mean_totals_pct_gamma-robust.Gain_from_mean_totals_pct_lognormal
robust[['Profile','N_slices','SB_AKE_p95_ms_lognormal','SB_AKE_p95_ms_gamma','delta_p95_ms','Gain_from_mean_totals_pct_lognormal','Gain_from_mean_totals_pct_gamma','delta_gain_percentage_points']].to_csv(OUT/'gamma_robustness.csv',index=False)
# Preserve existing five-pane principal figures as separate plot files.
for profile in P:
 s=base[base.Profile==profile];label='P1' if profile.startswith('P1') else 'P2'
 fig,ax=plt.subplots(figsize=(7.2,4.6));ax.plot(s.N_slices,s.SB_AKE_mean_ms/1000,'-o',label='SB-AKE');ax.plot(s.N_slices,s.Independent_mean_ms/1000,'-s',label='Independent AKE');ax.set(xlabel='Authorized slices',ylabel='Mean modeled endpoint computation (s)',title=f'{label}: published-primitive-calibrated estimates');ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(OUT/f'{label}_latency.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.2,4.6));ax.plot(s.N_slices,s.Amortized_mean_ms_per_slice/1000,'-o');ax.set(xlabel='Authorized slices',ylabel='Amortized modeled computation per slice (s)',title=f'{label}: amortized endpoint computation');ax.grid(alpha=.25);fig.tight_layout();fig.savefig(OUT/f'{label}_amortized.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7.2,4.6))
for p in P:
 s=base[base.Profile==p];ax.plot(s.N_slices,s.Gain_from_mean_totals_pct,'-o',label=p[:2])
ax.set(xlabel='Authorized slices',ylabel='Reduction in mean modeled computation (%)',title='Main simulated amortization gains');ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(OUT/'gain_profiles.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7.2,4.6))
for p in P:
 s=sweep[(sweep.profile==p)&(sweep.N==10)]
 ax.plot(s.assumed_per_slice_ms,s.shared_setup_gain_pct,'-o',label=p[:2]+' equal setup')
 ax.plot(s.assumed_per_slice_ms,s.zero_baseline_setup_gain_pct,'--',label=p[:2]+' baseline zero setup')
ax.set(xlabel='Hypothetical slice setup cost (ms; NOT measured)',ylabel='Expected reduction (%)',title='Wide-range structural sensitivity, 10 slices');ax.grid(alpha=.25);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'wide_sensitivity.png',dpi=180);plt.close(fig)
manifest=dict(source='Karcz et al., PLOS ONE 21(8) e0355179 (2026), Tables 5 7 8',source_url='https://doi.org/10.1371/journal.pone.0355179',seed=SEED,trials=RUNS,platform='ESP32-C6 workload+BLE+Wi-Fi source primitives, NOT SB-AKE hardware',model_assumptions=['independent per-operation draws; empirical cross-operation correlation unknown','lognormal positive marginals; gamma checked','per-slice setup 10 +/- 1 ms both constructions; broad and baseline-zero stress checks','no PUF FE, radio/network, end-to-end energy, peak integrated stack modeled'],operation_inputs=P)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
# Regression: original run re-generation with original RNG ordering.
prev=Path(__file__).resolve().parent/'SB_AKE_multislice_10000_FINAL_summary.csv'
if prev.exists():
 old=pd.read_csv(prev)
 assert np.allclose(old.SB_AKE_mean_ms.values,base.SB_AKE_mean_ms.values,atol=1e-9)
 assert np.allclose(old.Independent_mean_ms.values,base.Independent_mean_ms.values,atol=1e-9)
 print('REGRESSION: main simulations reproduce prior fixed-seed results EXACTLY')
print('P1, P2 fixed means:',[(c['profile'],round(c['reconstructed_ms'],3),round(c['discrepancy_pct'],3)) for c in cal])
for p in P:
 for n in [5,10]:
  b=base[(base.Profile==p)&(base.N_slices==n)].iloc[0]
  a=robust[(robust.Profile==p)&(robust.N_slices==n)].iloc[0]
  z=sweep[(sweep.profile==p)&(sweep.N==n)&(sweep.assumed_per_slice_ms==1000)].iloc[0]
  print(p[:2],n,'main gain',round(b.Gain_from_mean_totals_pct,2),'gamma p95_delta_ms',round(a.delta_p95_ms,1),'gamma gain difference pp',round(a.delta_gain_percentage_points,3),'1000ms zero-baseline gain',round(z.zero_baseline_setup_gain_pct,2))
print('OUTPUT_DIR',OUT)
