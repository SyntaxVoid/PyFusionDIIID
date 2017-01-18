function get_times, database
;
;
;

print,"***Make sure you update your template if you add parameters (database_template.sav)!!!***"
; Put Instructions here on how to updata the template
;
;
restore,"database_template.sav"
data = read_ascii(database, template=database_template)
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
times=times[0:cur_index-1]
return times
end