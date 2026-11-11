"""Synthesises soft, royalty-free UI sound effects (pop, tick, whoosh, paper) into project/assets/sfx."""
import numpy as np, wave, os
SR=48000; out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'project','assets','sfx')
rng=np.random.default_rng(7)
def save(name,x,peak=0.5):
    x=x/np.max(np.abs(x))*peak; x=np.int16(x*32767)
    with wave.open(os.path.join(out,name),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(x.tobytes())
def t(d): return np.arange(int(SR*d))/SR
# pop: quick downward sine sweep with fast decay
tt=t(0.12); f=900*np.exp(-tt*18)+260; ph=2*np.pi*np.cumsum(f)/SR
save('pop.wav',np.sin(ph)*np.exp(-tt*38)*(1-np.exp(-tt*900)))
# tick: short bright click
tt=t(0.05); save('tick.wav',(np.sin(2*np.pi*2400*tt)+0.5*np.sin(2*np.pi*3600*tt))*np.exp(-tt*140),0.4)
# whoosh: band-limited noise with swell
tt=t(0.45); n=rng.standard_normal(len(tt)); k=np.ones(40)/40; n=np.convolve(n,k,'same')-np.convolve(n,np.ones(400)/400,'same')
save('whoosh.wav',n*np.sin(np.pi*tt/0.45)**2,0.35)
# paper: crisp noise flutter
tt=t(0.35); n=rng.standard_normal(len(tt)); n=n-np.convolve(n,np.ones(12)/12,'same')
env=np.sin(np.pi*tt/0.35)**1.5*(0.6+0.4*np.sin(2*np.pi*22*tt)); save('paper.wav',n*env,0.3)
print('ok')
