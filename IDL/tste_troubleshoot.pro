pro tste_troubleshoot x
;
;
;

n=5
shot = 159243
times = 250 + indgen(n)
print,"Checking time for fetching 5 values of tste_0 and tsne_0 between times 250 and 260 ms."
; Electron Temperature
te = fltarr(n)
t0 = systime(/seconds)
for i=1,n-1 do begin
    before = systime(/seconds)
    te[i] = gadatave_efficient("tste_0",shot,times[i],25)
    after = systime(/seconds)
    print, "tste_0 Fetch took " + strtrim(after-before,1) + " seconds."
end
t1 = systime(/seconds)
print, "Fetching 5 elements from tste_0 took " + strtrim(t1-t0,1) + " seconds."


; Electron Density
ne = fltarr(n)
t0 = systime(/seconds)
for i=1,n-1 do begin
    before = systime(/seconds)
    ne[i] = gadatave_efficient("tsne_0",shot,times[i],25)
    after = systime(/seconds)
    print, "tsne_0 Fetch took " + strtrim(after-before,1) + " seconds."
end
t1 = systime(/seconds)
print, "Fetching 5 elements from tsne_0 took " + strtrim(t1-t0,1) + " seconds"
end