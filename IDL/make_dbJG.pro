pro make_dbJG, shot, times, savename
; John Gresl 1/16/2017
; Input:
;   shot: Shot number
;   times: file with the times that we are interested in
; Output:
;   Does not return values, instead it creates a save file with the
;   the following arrays of values.
;       ip:        Plasma Current
;       betan:     ???
;       q0:        ???
;       q95:       ???
;       cerqrott1: ???
;       cerqrott6: ???
;       te:        Electron Temperature
;       dene:      Electron Density


print,"***Make sure you update your template if you add parameters (database_template.sav)!!!***"

restore,"database_template.sav"
data = read_ascii(times, template=database_template)
n_max = n_elements(data.time)
cur_time = -9999
cur_index = 0
times = fltarr(n_max)
for j=0,n_max-1 do begin
    if cur_time ne data.time[j] then begin
        times[cur_index] = data.time[j]
        cur_time = data.time[j]
        cur_index = cur_index + 1
    end
end

i = size(times, /n_elements)
i2 = cur_index - 1
print,i-i2

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

; Electron Density ( I THINK this is electron density )
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