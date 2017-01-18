function seconds2str, time
; Input:
;   time: A time length in seconds
;
; Output:
;   That time, converted to a string like {} days {} hours {} minutes {} seconds

  ; Seconds
  temp = double(time)
  result = string(temp mod 60, format='(f4.1, " seconds")')

  ; Minutes
  temp = floor(tempTime / 60)
  if temp eq 0 then return, result
  val = (temp mod 60) eq 1 ? ' minute and ' : ' minutes and '
  result = string(temp mod 60, format='(i2)') + val + result

  ; Hours
  temp /= 60
  if temp eq 0 then return, result
  val = (temp mod 24) eq 1 ? " hour, " : " hours, "
  result = string(temp mod 24, format = '(i2)') + val + result

  ; Days
  temp /= 24
  if temp eq 0 then return, result
  val = (temp mod 365) eq 1 ? " day, " : " days, "
  result = string(temp mod 365, format = '(i3)')+ val + result

  ; Years
  temp /= 365
  if temp eq 0 then return, result
  val = (temp eq 1) ? " year, " : " years, "
  result = strtrim(temp, 2) + val + result

  return, result
end

function dict_constructor, pointnames
;
;
n = n_elements(pointnames)
result = "{"
for i=0,n-1 do begin
    cur_point = pointnames[i]
    to_add = cur_point
    if i ne n-1 then result += to_add + ":" + to_add + ","
    if i eq n-1 then result += to_add + ":" + to_add + "}"
end
return, result
end





pro make_dbv2, shot, pointnames, times, savename
; John Gresl 1/17/2017
; Input:
;   shot: Shot Number
;   pointnames: A strarr of pointnames you would like to fetch (using gadatave_efficient)
;   times: A fltarr of times you would like to fetch for each pointname
;   savename: The name of the file you would like to save the structure to
; Output:
;   ---


; Discard any duplicate times.
n_max = n_elements(times)
cur_time = -9999
cur_index = 0
unique_times = fltarr(n_max)
for j=0,n_max-1 do begin
    if cur_time ne times[j] then begin
        unique_times[cur_index] = times[j]
        cur_time = times[j]
        cur_index += 1
    end
end
unique_times = unique_times[0:cur_index-1]
n = n_elements(unique_times)

; Print out an estimation of when the database will be complete since some
; pointnames take a \very\ long time to calculate. Each variable is the average
; time, in seconds, that it took to fetch 100 elements, divided by 100.
t_ip = 4.78 / 100.
t_betan = 0.629 / 100.
t_q0 = 0.644 / 100.
t_q95 = 0.566 / 100.
t_cerqrott1 = 0.495 / 100.
t_cerqrott6 = 0.505 / 100.
t_tste_0 = 350. / 100.
t_tsne_0 = 700. / 100.

n_points = n_elements(pointnames)
cur_factor = 0
for j=0,n_points-1 do begin
    cur_point = pointnames[j]
    case 1 of
        cur_point eq "ip": cur_factor += t_ip
        cur_point eq "betan": cur_factor += t_betan
        cur_point eq "q0": cur_factor += t_q0
        cur_point eq "q95": cur_factor += t_q95
        cur_point eq "cerqrott1": cur_factor += t_cerqrott1
        cur_point eq "cerqrott6": cur_factor += t_cerqrott6
        cur_point eq "tste_0": cur_factor += t_tste_0
        cur_point eq "tsne_0": cur_factor += t_tsne_0
    else: print, "Pointname has not been timed yet and will not be included: ", cur_point
    end
end
fetch_time = cur_factor*n
print, "Data fetching should be complete in ", time2string(fetch_time)


;; Test
;points = ["ip","john","bill"]
;ip = [1,6,2]
;john = 16
;bill = "doctor"
;ans = dict_constructor(points)
;dum = execute("my_dict="+ans)
;help,my_dict
;; End Test


; Now the actual fetching. Gets a little sketchy looking here...
for i=0,n_points-1 do begin
    cur_point = pointnames[i]
    (scope_varfetch(cur_point, /enter, level=1)) = fltarr(n)
    temp_arr = fltarr(n)
    for j=0,n-1 do begin
        (scope_varfetch(cur_point, /enter, level=1))[j] = gadatave_efficient(cur_point,shot,unique_times[j],25)
    end
end
construction_string = dict_constructor(pointnames)
dum = execute("data_dict="+construction_string)
help,data_dict
end