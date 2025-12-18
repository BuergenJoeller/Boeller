!/usr/bin/env python3
import sys, json, random

random.seed(1)
first_tick = True

for line in sys.stdin:
    data = json.loads(line)
    if first_tick:
        config = data.get("config", {})
        width = config.get("width")
        height = config.get("height")
        print(f"Random walker (Python) launching on a {width}x{height} map",
              file=sys.stderr, flush=True)
    gems = data.get("visible_gems", {})
    former = 0
    for i in gems.length:
        currentGem = gems[i]
        if currentGem["ttl"] > former:
            highest = i
    currentGem = gems[highest]
    tgtX = currentGem["position"[0]] 
    tgtY = currentGem["position"[1]] 
    posX = data.get("bot"[0])
    posY = data.get("bot"[1])
    if posX != tgtX:
        if posX > tgtX:
            move = "W"
        else:
            move = "E"
    elif posY != tgtY:
        if posY > tgtY:
            move = "S"
        else:
            move = "N"
    print(move, flush=True)
    first_tick = False

