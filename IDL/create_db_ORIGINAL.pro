PRO create_db
; Read fishbone_db.pro and write an idl save file
; shot

; tbdot: time of peak |Bdot| (ms)
; bmax: peak amplitude of |Bdot|
; fbfreq: initial fb frequency (kHz)
; minfreq: final fb frequency (kHz)
; dfreq:  chirping rate
; distort: peak fractional distortion of Mirnov
; rise:  growth rate of Mirnov
; fall:  decay rate of Mirnov

; pdistort:  fractional distortion at tbdot
; rdistort:  rate of change of fractional distortion at tbdot

; tneut: time of peak neutron drop (ms)
; pmax: maximum of -dplastic/dt/plastic relative to pre-burst value
; pave: average plastic value before burst
; lbeam: beam power constant during burst (logical)
; pinj: average beam power before burst (MW)
; tice: time of icehigh peak (ms)
; icehighmax: icehigh peak
; icehighsum: icehigh sum during burst (with average subtracted)
; icehighave: icehigh average before
; icelowsum: icelow sum during burst (with average subtracted)
; icelowave: icelow average before
; bildsum: bild sum during burst (with average subtracted)
; bildave: bild average before
; lbild: bild2 saturated logical
; lcer: cer data usable for fast rotation (logical)
; nicrf:  number of fast icrf data points with +-2 ms of peak
; lssnpa logical: 210RT switches (0), 210RT off (1), 210RT on (2)
; npax: sum/average for SSNPA1, 2, and 3

; ip: plasma current (MA)
; betan:  efit02 betan
; q0:  efit02 q0
; rot0: tang1 toroidal rotation (km/s)
; rot2: tang6 toroidal rotation (km/s)
; te:  core Thomson central Te (keV)
; dene: core Thomson central density (10^13)
 
;  ecot,ecop,ectrt,ectrp,pcot,pcop,pctrt,pctrp:
; average beam voltage and power for co-tangential,
; co-perp, ctr-tangential, ctr-perp


nmax=1000
shot=lonarr(nmax)
tbdot=fltarr(nmax)
bmax=replicate(-99.,nmax)
fbfreq=replicate(-99.,nmax)
minfreq=replicate(-99.,nmax)
dfreq=replicate(-99.,nmax)
distort=replicate(-99.,nmax)
rise=replicate(-99.,nmax)
fall=replicate(-99.,nmax)
pdistort=replicate(-99.,nmax)
rdistort=replicate(-99.,nmax)
tneut=fltarr(nmax)
pmax=fltarr(nmax)
pave=fltarr(nmax)
lbeam=intarr(nmax)
pinj=fltarr(nmax)
tice=fltarr(nmax)
icehighmax=fltarr(nmax)
icehighsum=fltarr(nmax)
icehighave=fltarr(nmax)
icelowsum=fltarr(nmax)
icelowave=fltarr(nmax)
bildsum=fltarr(nmax)
bildave=fltarr(nmax)
lbild=intarr(nmax)
lcer=intarr(nmax)
nicrf=lonarr(nmax)
lssnpa=intarr(nmax)
npa1sum=fltarr(nmax)
npa1ave=fltarr(nmax)
npa2sum=fltarr(nmax)
npa2ave=fltarr(nmax)
npa3sum=fltarr(nmax)
npa3ave=fltarr(nmax)

on_ioerror, bad
openr,unit,'fishbone_db.dat',/get_lun
line=' '

i=0
while(not eof(unit)) do begin
 if(i gt nmax) then goto, bad
 readf,unit,d1
 shot[i]=long(d1)
 readf,unit,d1,d2
 tbdot[i]=d1 & bmax[i]=d2
 readf,unit,d1,d2,d3,d4,d5
 tneut[i]=d1 & pmax[i]=d2 & pave[i]=d3 & lbeam[i]=fix(d4) & pinj[i]=d5
 readf,unit,d1,d2,d3,d4
 tice[i]=d1 & icehighmax[i]=d2 & icehighsum[i]=d3 & icehighave[i]=d4
 readf,unit,d1,d2,d3,d4,d5
 icelowsum[i]=d1 & icelowave[i]=d2 & bildsum[i]=d3 & bildave[i]=d4
 lbild[i]=fix(d5) 
 readf,unit,d1,d2,d3
 lcer[i]=fix(d1) & nicrf[i]=long(d2) & lssnpa[i]=fix(d3)
 readf,unit,d1,d2,d3,d4,d5,d6
 npa1sum[i]=d1 & npa1ave[i]=d2
 npa2sum[i]=d3 & npa2ave[i]=d4
 npa3sum[i]=d5 & npa3ave[i]=d6
 readf,unit,line
 i=i+1
end
help,i

close,unit

; trim arrays
shot=shot[0:i-1]
tbdot=tbdot[0:i-1]
bmax=bmax[0:i-1]
tneut=tneut[0:i-1]
pmax=pmax[0:i-1]
pave=pave[0:i-1]
lbeam=lbeam[0:i-1]
pinj=pinj[0:i-1]
tice=tice[0:i-1]
icehighmax=icehighmax[0:i-1]
icehighsum=icehighsum[0:i-1]
icehighave=icehighave[0:i-1]
icelowsum=icelowsum[0:i-1]
icelowave=icelowave[0:i-1]
bildsum=bildsum[0:i-1]
bildave=bildave[0:i-1]
lbild=lbild[0:i-1]
lcer=lcer[0:i-1]
nicrf=nicrf[0:i-1]
lssnpa=lssnpa[0:i-1]
npa1sum=npa1sum[0:i-1]
npa1ave=npa1ave[0:i-1]
npa2sum=npa2sum[0:i-1]
npa2ave=npa2ave[0:i-1]
npa3sum=npa3sum[0:i-1]
npa3ave=npa3ave[0:i-1]
fbfreq=fbfreq[0:i-1]
minfreq=minfreq[0:i-1]
dfreq=dfreq[0:i-1]
distort=distort[0:i-1]
rise=rise[0:i-1]
fall=fall[0:i-1]
pdistort=pdistort[0:i-1]
rdistort=rdistort[0:i-1]

;----------------------
; Merge with Mirnov data
read_fb_mirnov,a
for i=0,i-1 do begin
  w=where(shot[i] eq a.shot and tbdot[i] eq a.tbdot,nw)
  if nw eq 1 then begin
    fbfreq[i]=reform(a.fbfreq[w])
    minfreq[i]=reform(a.minfreq[w])
    dfreq[i]=reform(a.dfreq[w])
    distort[i]=reform(a.distort[w])
    rise[i]=reform(a.rise[w])
    fall[i]=reform(a.fall[w])
  end else print,'FB not found:',shot[i],tbdot[i],nw
end

;----------------------
; Merge with distort data
read_fb_distort,a
for i=0,i-1 do begin
  w=where(shot[i] eq a.shot and tbdot[i] eq a.tbdot,nw)
  if nw eq 1 then begin
    pdistort[i]=reform(a.pdistort[w])
    rdistort[i]=reform(a.rdistort[w])
  end else print,'distort FB not found:',shot[i],tbdot[i],nw
end

;-----------------------
; Fetch plasma signals

ip=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  ip[j]=1.e-6*gadatave_efficient('ip',sh,tbdot[j],20,x=x,y=y)
end

betan=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  betan[j]=gadatave_efficient('betan',sh,tbdot[j],25,x=x,y=y)
end

q0=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  q0[j]=gadatave_efficient('q0',sh,tbdot[j],25,x=x,y=y)
end

help,q0

rot0=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  rot0[j]=gadatave_efficient('cerqrott1',sh,tbdot[j],30,x=x,y=y)
end

rot2=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  rot2[j]=gadatave_efficient('cerqrott6',sh,tbdot[j],30,x=x,y=y)
end

te=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  te[j]=gadatave_efficient('tste_0',sh,tbdot[j],30,x=x,y=y)
end

dene=fltarr(i)
sh=0
for j=0,i-1 do begin
  if shot[j] ne sh then begin
    sh=shot[j]
    x=1 & y=1
  end
  dene[j]=gadatave_efficient('tsne_0',sh,tbdot[j],30,x=x,y=y)
end

; ------------------------
; Beam data
ecot=fltarr(i) & ecop=fltarr(i) & ectrt=fltarr(i) & ectrp=fltarr(i)
pcot=fltarr(i) & pcop=fltarr(i) & pctrt=fltarr(i) & pctrp=fltarr(i)
nbi=get_nbi(shot[0])
for j=0,i-1 do begin
  eav_co_ctr,shot[j],tbdot[j],d1,d2,d3,d4,d5,d6,d7,d8,nbi=nbi
  ecot[j]=d1 & ecop[j]=d2 & ectrt[j]=d3 & ectrp[j]=d4
  pcot[j]=d5 & pcop[j]=d6 & pctrt[j]=d7 & pctrp[j]=d8
end

;-------------------------
save,filename='fb_db.dat',shot,tbdot,bmax,fbfreq,minfreq,dfreq,distort, $
 rise,fall,pdistort,rdistort,tneut,pmax $
 ,pave,lbeam,pinj,tice,icehighmax,icehighsum,icehighave, $
 icelowsum,icelowave,bildsum,bildave,lbild,lcer,nicrf,lssnpa, $
 npa1sum,npa1ave,npa2sum,npa2ave,npa3sum,npa3ave, $
 ip,betan,q0,rot0,rot2,te,dene, $
 ecot,ecop,ectrt,ectrp,pcot,pcop,pctrt,pctrp

bad:
end

