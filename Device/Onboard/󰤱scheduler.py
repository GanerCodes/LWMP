name, que, dur
n,q,d,t = time_info

current_scene

S = (name,d,t)

if q:
  que.append(n,d,que[-1][2]+que[-1][1])
else:
  if d == inf:
    que.clear()
    que.append(S)
  else:
    que.insert(0,S)
    
while que:
  n,d,t = que[0]
  if T>=t:
    if T-t >= d:
      que.pop(0)
      continue
    if d == inf:
      current_scene = n
      # 󰤱 write as "device scene"?
      que.clear()
      break
    controller(n,T)