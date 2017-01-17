pro make_dbJG, shot, times, savename
; John Gresl 1/16/2017
; Input:
;   shot: Shot number
;   times: array of times that I would like to fetch


; I want plasma current, betan, magnetic field, cerarott1 and cerarott6, q0 and q95
; [x] Plasma Current
; [x] Beta N
; [o] Magnetic Field (This will come from PyFusion I think..)
; [?] Cerarott1
; [?] Cerarott6
; [x] q0
; [x] q95


i = size(times, /n_elements)

; PLASMA CURRENT
ip = fltarr(i)
for j=0,i-1 do begin
    ip[j] = 1.e-6*gadatave_efficient("ip",shot,times[j],20)
end

; BETA N
betan = fltarr(i)
for j=0,i-1 do begin
    betan[j] = gadatave_efficient("betan",shot,times[j],25)
end

; q0
q0 = fltarr(i)
for j=0,i-1 do begin
    q0[j] = gadatave_efficient("q0",shot,times[j],25)
end

; q95
q95 = fltarr(i)
for j=0,i-1 do begin
    q95[j] = gadatave_efficient("q95",shot,times[j],25)
end

; cerqrott1 (What is this??)
cerqrott1 = fltarr(i)
for j=0,i-1 do begin
    cerqrott1[j] = gadatave_efficient("cerqrott1",shot,times[j],30)
end

; cerqrott6 (What is this??x2)
cerqrott6 = fltarr(i)
for j=0,i-1 do begin
    cerqrott6[j] = gadatave_efficient("cerqrott6",shot,times[j],30)
end

; Electron temperate
te = fltarr(i)
for j=0,i-1 do begin
    te[j] = gadatave_efficient("tste_0",shot,times[j],30)
end

; Electron Density ( I THINK this is electron density
dene=fltarr(i)
for j=0,i-1 do begin
    dene[j] = gadatave_efficient("tsne_0",shot,times[j],30)
end

;
; Any other parameters we may want in the future will go here. . .
;

; Now we save the arrays to an IDL save file.
save, ip, betan, q0, q95, cerqrott1, cerqrott6, te, dene, filename = savename


end