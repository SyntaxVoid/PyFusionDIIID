PRO read_fb_mirnov,a
; Read fishbone_db.pro and return a structure with the data
; shot
; time of peak |Bdot| (ms)
; fishbone start frequency (kHz)
; fishbone end frequency (kHz)
; rate of change dT/dt of fishbone period after mode peak
; fractional distortion of Bdot period near peak
; exponential rate of rise of Bdot
; exponential rate of fall of Bdot

nmax=1000
shot=lonarr(nmax)
tbdot=fltarr(nmax)
fbfreq=fltarr(nmax)
minfreq=fltarr(nmax)
dfreq=fltarr(nmax)
distort=fltarr(nmax)
rise=fltarr(nmax)
fall=fltarr(nmax)

on_ioerror, bad
openr,unit,'fb_mirnov.dat',/get_lun
line=' '

i=0
while(not eof(unit)) do begin
 if(i gt nmax) then goto, bad
 readf,unit,line	; blank line
 readf,unit,d1,d2
 shot[i]=long(d1)
 tbdot[i]=d2
 readf,unit,d1,d2,d3,d4
 fbfreq[i]=d1 & minfreq[i]=d2 & dfreq[i]=d3 & distort[i]=d4
 readf,unit,d1,d2
 rise[i]=d1 & fall[i]=d2
 i=i+1
end
help,i

close,unit

; trim arrays
shot=shot[0:i-1]
tbdot=tbdot[0:i-1]
fbfreq=fbfreq[0:i-1]
minfreq=minfreq[0:i-1]
dfreq=dfreq[0:i-1]
distort=distort[0:i-1]
rise=rise[0:i-1]
fall=fall[0:i-1]

a={shot:shot,tbdot:tbdot,fbfreq:fbfreq,minfreq:minfreq,dfreq:dfreq, $
   distort:distort,rise:rise,fall:fall}

bad:
end
