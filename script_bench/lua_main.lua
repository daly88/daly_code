require "math"

g_int_array = {1,23,4,5,6,15,6,2}

function shuffle_pick(origin, n)
	local l = table.getn(origin)
	local pick = {}
	for _,v in ipairs(origin) do
		table.insert(pick, v)
	end

	local i = 0
	local j = 0
	local tmp = 0
	for i=1, n do
		i = math.random(l)
		if i > l/2 then
			j = math.random(i-1)
		else
			j = i + 1 + math.random(l-i-1)
		end
		tmp = pick[i]
		pick[i] = pick[j]
		pick[j] = tmp
	end

	for _,v in ipairs(pick) do
		for i=1, l do
			if origin[i] == v then
				--print(i)
			end
		end
	end
end

for i=1,1000 do
	shuffle_pick(g_int_array, 1000)
end
