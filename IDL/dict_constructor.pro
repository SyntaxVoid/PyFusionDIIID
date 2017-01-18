function dict_constructor, pointnames

n = n_elements(pointnames)
result = "{"
for i=0,n-1 do begin
    cur_point = pointnames[i]
    ;to_add = "(scope_varfetch("""+cur_point+""", /enter, level=1))"
    to_add = cur_point
    if i eq n-1 then result += to_add + ":" + to_add + "}"
    if i ne n-1 then result += to_add + ":" + to_add + ","
end
return, result
end
