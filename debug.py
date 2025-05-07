import copy

a = [1]
b = [2]

c = [a, b]

d = copy.deepcopy(c)

a.append(22)
b.append(32)

print(c)
print(d)