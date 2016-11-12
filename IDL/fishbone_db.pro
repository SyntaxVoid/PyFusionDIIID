PRO fishbone_db,shot,xmin,xmax,doplot=doplot,nowrite=nowrite,bthresh=bthresh
; INPUTS
; shot  duh
; xmin, xmax time window

; OUTPUT (appends to the file fishbone_db.dat)
; shot
; time of peak |Bdot| (ms)
; peak amplitude of |Bdot|
; time of peak neutron drop (ms)
; maximum of -dplastic/dt/plastic relative to pre-burst value
; average value before burst
; beam power constant during burst (logical)
; average beam power before burst (MW)
; time of icehigh peak (ms)
; icehigh peak
; icehigh sum during burst (with average subtracted)
; icehigh average before
; icelow sum during burst (with average subtracted)
; icelow average before
; bild sum during burst (with average subtracted)
; bild average before
; bild2 saturated logical
; cer data usable (logical)
; nicrf  number of icrf data points with +-2 ms of peak
; ssnpa logical: 210RT switches (0), 210RT off (1), 210RT on (2)
; sum/average for SSNPA1, 2, and 3

; KEYWORDS
; doplot  plots quantities
; nowrite don't write output to file

; Read signals
gadat,tplastic,plastic,'fplastic',shot,/double
gadat,tbdot,bdot,'mpi66m307d',shot,/double
gadat,tice,icehigh,'icehigh',shot,/double
gadat,tcer,cer,'cerqrotct6',shot,/double
n=get_nbi(shot)
beams=n.pinj & tbeams=1000*n.time
gadat,tbild,bild1,'bild1',shot,/double
gadat,tbild,bild2,'bild2',shot,/double
bild=bild1-bild2
gadat,tice,icelow,'icelow',shot,/double
gadat,ticrf,icrf,'i247mpo',shot,/double
gadat,tnpa,npa1,'ssnpa1',shot,/double & npa1=-npa1
gadat,tnpa,npa2,'ssnpa2',shot,/double & npa2=-npa2
gadat,tnpa,npa3,'ssnpa3',shot,/double & npa3=-npa3
gadat,t21,n21rt,'nbvac21rtf',shot,/double

; Smooth data

time=xmin
tp=xmax-xmin
xx=time + .05*findgen(fix(tp/.05)+1)
w=where(tplastic gt time and tplastic lt time+tp,nw)
y=-smooth(deriv(tplastic,smooth(plastic,101)),31)
yave=total(y[w])/nw
ps=interpol(y,tplastic,xx)
bs=interpol(smooth(abs(bdot),101),tbdot,xx)
is=interpol(smooth(icehigh,31),tice,xx)

; Find fishbones
pthresh=0;.02
if not keyword_set(bthresh) then bthresh=40
ithresh=0;.15

w=where(ps gt pthresh and bs gt bthresh and is gt ithresh,nw)
if nw eq 0 then goto, skipit
ddd=xx[w]-shift(xx[w],1)
ww=where(ddd gt 2,nww)

if nww eq 0 then goto, skipit
; Add small fishbones 12/10
;openw,1,'fishbone_db.dat',/append
openw,1,'small_fishbone_db.dat',/append

ppk=fltarr(2,nww+1)
bpk=ppk
ipk=ppk

xxx=xx[w[0:ww[0]-1]]
yyy=ps[w[0:ww[0]-1]]
dum=max(yyy,imax)
ppk[0,0]=xxx[imax] & ppk[1,0]=dum
yyy=bs[w[0:ww[0]-1]]
dum=max(yyy,imax)
bpk[0,0]=xxx[imax] & bpk[1,0]=dum
yyy=is[w[0:ww[0]-1]]
dum=max(yyy,imax)
ipk[0,0]=xxx[imax] & ipk[1,0]=dum

for i=0,nww-2 do begin
  xxx=xx[w[ww[i]:ww[i+1]-1]]
  yyy=ps[w[ww[i]:ww[i+1]-1]]
  dum=max(yyy,imax)
  ppk[0,i+1]=xxx[imax] & ppk[1,i+1]=dum
  yyy=bs[w[ww[i]:ww[i+1]-1]]
  dum=max(yyy,imax)
  bpk[0,i+1]=xxx[imax] & bpk[1,i+1]=dum
  yyy=is[w[ww[i]:ww[i+1]-1]]
  dum=max(yyy,imax)
  ipk[0,i+1]=xxx[imax] & ipk[1,i+1]=dum
end

xxx=xx[w[ww[nww-1]:nw-1]]
yyy=ps[w[ww[nww-1]:nw-1]]
dum=max(yyy,imax)
ppk[0,nww]=xxx[imax] & ppk[1,nww]=dum
yyy=bs[w[ww[nww-1]:nw-1]]
dum=max(yyy,imax)
bpk[0,nww]=xxx[imax] & bpk[1,nww]=dum
yyy=is[w[ww[nww-1]:nw-1]]
dum=max(yyy,imax)
ipk[0,nww]=xxx[imax] & ipk[1,nww]=dum

;--------------------------------------
; Plot of basic signals

;if keyword_set(doplot) then begin
if not keyword_set(hc) then window,0
!p.multi=[0,0,5]
plot,tplastic,plastic,xrange=[time,time+tp],xtickformat='nullticks', $
  /xstyle,/ystyle
plot,tplastic,y,xrange=[time,time+tp],xtickformat='nullticks', $
  /xstyle,/ystyle
oplot,[time,time+tp],[pthresh,pthresh],color=100
oplot,[time,time+tp],[yave,yave],color=100
oplot,xx,ps,color=150
oplot,ppk[0,*],ppk[1,*],psym=2,color=80,symsize=1.5
plot,tbdot,abs(bdot),xrange=[time,time+tp],xtickformat='nullticks', $
  /xstyle,/ystyle
oplot,[time,time+tp],[bthresh,bthresh],color=100
oplot,tbdot,smooth(abs(bdot),101),color=100
oplot,xx,bs,color=150
oplot,bpk[0,*],bpk[1,*],psym=2,color=80,symsize=1.5
plot,tice,icehigh,xrange=[time,time+tp],xtickformat='nullticks', $
  xcharsize=1.5,/xstyle,/ystyle
oplot,[time,time+tp],[ithresh,ithresh],color=100
oplot,tice,smooth(icehigh,31),color=100
oplot,xx,is,color=150
oplot,ipk[0,*],ipk[1,*],psym=2,color=80,symsize=1.5
plot,tcer,cer,psym=2,xrange=[time,time+tp],  /xstyle,/ystyle
;end ; doplot

;Loop through all of the fishbones
for i=0,nww do begin

if not keyword_set(nowrite) then printf,1,' ',shot
if not keyword_set(nowrite) then printf,1,bpk[0,i],bpk[1,i]
w=where(tbdot ge bpk[0,i]-1.5 and tbdot le bpk[0,i]+1.5,nw)

;-------------------------------
; Neutrons

; Beam power constant during drop?
wbeams=where(tbeams ge ppk[0,i]-4 and tbeams le ppk[0,i],nwbeams)
abeams=total(beams[wbeams])/nwbeams
constb=abs(beams[wbeams]-shift(beams[wbeams],1))
dum=max(constb)
if dum gt 5e5 then lbeam=0 else lbeam=1

; Value of slope before burst
wp=where(tplastic ge ppk[0,i]-4 and tplastic le ppk[0,i]-1.5,nwp)
pbefore=total(y[wp])/nwp

dum=min(abs(tplastic-ppk[0,i]),it)
plasticmax=total(plastic[it-5:it+5])/11.
if not keyword_set(nowrite) then $
 printf,1,ppk[0,i],(ppk[1,i]-pbefore)/plasticmax,pbefore/plasticmax,lbeam,1.e-6*abeams

if keyword_set(doplot) then begin
  !p.multi=[0,0,3]
  if not keyword_set(hc) then window,3
  plot,tplastic,plastic,xrange=[ppk[0,i]-5,ppk[0,i]+5],xtickformat='nullticks', $
   /xstyle,/ystyle
  plot,tplastic,y,xrange=[ppk[0,i]-5,ppk[0,i]+5],xtickformat='nullticks', $
   /xstyle,/ystyle
  oplot,[ppk[0,i]-5,ppk[0,i]+5],[0,0],color=100
  oplot,[ppk[0,i]-4,ppk[0,i]-4],[-100,100],color=100
  oplot,[ppk[0,i]-1.5,ppk[0,i]]-1.5,[-100,100],color=100
  plot,tbeams,beams,xrange=[ppk[0,i]-5,ppk[0,i]+5],/xstyle
  oplot,[ppk[0,i]-5,ppk[0,i]+5],[abeams,abeams],color=100
  oplot,[ppk[0,i]-4,ppk[0,i]-4],[-100,100],color=100
  oplot,[ppk[0,i],ppk[0,i]],[0,20e6],color=100
end  ; doplot

;------------------------------------------
;  ICE and BILD

if keyword_set(doplot) then begin
if not keyword_set(hc) then window,5
!p.multi=[0,0,4]
 plot,tplastic,y,xrange=[ppk[0,i]-5,ppk[0,i]+5],xtickformat='nullticks', $
  /xstyle,/ystyle
 plot,tbild,bild,psym=2,xrange=[ppk[0,i]-4,ppk[0,i]+4],  /xstyle,/ystyle
 oplot,[ppk[0,i]-1,ppk[0,i]-1],[-1.e6,1.e6],color=150
 oplot,[ppk[0,i]+2,ppk[0,i]+2],[-1.e6,1.e6],color=150
 oplot,[ppk[0,i]-3,ppk[0,i]-3],[-1.e6,1.e6],color=100
 oplot,[ppk[0,i]-1.5,ppk[0,i]-1.5],[-1.e6,1.e6],color=100
 plot,tice,icehigh,psym=2,xrange=[ppk[0,i]-4,ppk[0,i]+4],  /xstyle,/ystyle
 oplot,[ppk[0,i]-1,ppk[0,i]-1],[-1.e6,1.e6],color=150
 oplot,[ppk[0,i]+2,ppk[0,i]+2],[-1.e6,1.e6],color=150
 oplot,[ppk[0,i]-3,ppk[0,i]-3],[-1.e6,1.e6],color=100
 oplot,[ppk[0,i]-1.5,ppk[0,i]-1.5],[-1.e6,1.e6],color=100
 plot,tice,icelow,psym=2,xrange=[ppk[0,i]-4,ppk[0,i]+4],  /xstyle,/ystyle
 oplot,[ppk[0,i]-3,ppk[0,i]-3],[-1.e6,1.e6],color=100
 oplot,[ppk[0,i]-1.5,ppk[0,i]-1.5],[-1.e6,1.e6],color=100
 oplot,[ppk[0,i]-1,ppk[0,i]-1],[-1.e6,1.e6],color=150
 oplot,[ppk[0,i]+2,ppk[0,i]+2],[-1.e6,1.e6],color=150
end

wbild=where(tbild gt ppk[0,i]-3 and tbild lt ppk[0,i]-1.5,nwbild)
avebild=total(bild[wbild])/nwbild
wbild=where(tbild gt ppk[0,i]-1 and tbild lt ppk[0,i]+2,nwbild)
bildsum=total(bild[wbild]-avebild)
wcheck=where(abs(bild2[wbild]) gt 4.95 or abs(bild1[wbild]) gt 4.95,bildsat)
if bildsat ge 1 then bildsat=1

wice=where(tice gt ppk[0,i]-3 and tice lt ppk[0,i]-1.5,nwice)
aveicelow=total(icelow[wice])/nwice
aveicehigh=total(icehigh[wice])/nwice
wice=where(tice gt ppk[0,i]-1 and tice lt ppk[0,i]+2,nwbild)
icehighsum=total(icehigh[wice]-aveicehigh)
icelowsum=total(icelow[wice]-aveicelow)

if not keyword_set(nowrite) then $
 printf,1,ipk[0,i],ipk[1,i],icehighsum,aveicehigh
if not keyword_set(nowrite) then $
 printf,1,icelowsum,aveicelow,bildsum,avebild,bildsat

;----------------------------------
; CER and ICRF loops

if keyword_set(doplot) then begin
 if not keyword_set(hc) then window,6
 !p.multi=[0,0,3]
 plot,tplastic,y,xrange=[ppk[0,i]-4,ppk[0,i]+4],xtickformat='nullticks', $
  /xstyle,/ystyle
 plot,tcer,cer,psym=2,xrange=[ppk[0,i]-4,ppk[0,i]+4], $
   xtickformat='nullticks',/xstyle,/ystyle
 oplot,[ppk[0,i],ppk[0,i]],[-1.e6,1.e6],color=100
 plot,ticrf,icrf,xrange=[ppk[0,i]-4,ppk[0,i]+4],  /xstyle,/ystyle
 oplot,[ppk[0,i],ppk[0,i]],[-1.e6,1.e6],color=100
end

; midpoint of tcer bin is 0.25 ms later
wcb=where(tcer+.25 ge ppk[0,i]-3.5 and tcer+.25 le ppk[0,i],ncb)
wca=where(tcer+.25 ge ppk[0,i] and tcer+.25 le ppk[0,i]+3.5,nca)
if ncb ge 6 and nca ge 6 then lcer=1 else lcer=0

wib=where(ticrf ge ppk[0,i]-2 and ticrf le ppk[0,i]+2,nicrf)


;--------------------------------------
; SSNPA

w21on=where(t21 ge ppk[0,i]-2.7 and t21 le ppk[0,i]+1.8 and n21rt gt 2,non)
w21off=where(t21 ge ppk[0,i]-2.7 and t21 le ppk[0,i]+1.8 and n21rt lt 2,noff)
case 1 of
  non eq 0 and noff gt 0: lnpa=1
  non gt 0 and noff eq 0: lnpa=2
else: lnpa=0
endcase

wnpa=where(tnpa gt ppk[0,i]-2.7 and tnpa lt ppk[0,i]-1.5,nwnpa)
avenpa1=total(npa1[wnpa])/nwnpa
avenpa2=total(npa2[wnpa])/nwnpa
avenpa3=total(npa3[wnpa])/nwnpa
wnpa=where(tnpa gt ppk[0,i]-1 and tnpa lt ppk[0,i]+1.8,nwnpa)
npasum1=total(npa1[wnpa]-avenpa1)
npasum2=total(npa2[wnpa]-avenpa2)
npasum3=total(npa3[wnpa]-avenpa3)

if not keyword_set(nowrite) then $
 printf,1,lcer,nicrf,lnpa
if not keyword_set(nowrite) then $
 printf,1,npasum1,avenpa1,npasum2,avenpa2,npasum3,avenpa3
if not keyword_set(nowrite) then printf,1,' '

if keyword_set(doplot) then begin
if not keyword_set(hc) then window,7
!p.multi=[0,0,3]
plot,tplastic,y,xrange=[ppk[0,i]-5,ppk[0,i]+5],xtickformat='nullticks', $
  /xstyle,/ystyle
plot,tnpa,smooth(npa3,11),xrange=[ppk[0,i]-4,ppk[0,i]+4],  /xstyle,/ystyle
oplot,[ppk[0,i]-1,ppk[0,i]-1],[-1.e6,1.e6],color=150
oplot,[ppk[0,i]+1.8,ppk[0,i]+1.8],[-1.e6,1.e6],color=150
oplot,[ppk[0,i]-2.7,ppk[0,i]-2.7],[-1.e6,1.e6],color=100
oplot,[ppk[0,i]-1.5,ppk[0,i]-1.5],[-1.e6,1.e6],color=100
oplot,[ppk[0,i]-2.7,ppk[0,i]-1.5],[avenpa3,avenpa3],color=100,thick=3
plot,t21,n21rt,xrange=[ppk[0,i]-4,ppk[0,i]+4],yrange=[-2,8],/xstyle,/ystyle
end

end ; loop over fishbones
close,1

skipit:

end
