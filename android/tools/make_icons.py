#!/usr/bin/env python3
"""Draws the launcher icon (wheel + pointer) at every density, plus a 512px store icon."""
import math, os, sys
from PIL import Image, ImageDraw
SEGS = ["#ff3d7f","#ffb03b","#2ec4b6","#7b5cff","#ff6b3d","#3da5ff","#9be15d","#f15bb5"]
BG1, RIM = (27,16,53), (255,247,251)
def icon(px, round_=False):
    s = px*4; im = Image.new("RGBA",(s,s),(0,0,0,0)); d = ImageDraw.Draw(im)
    if round_: d.ellipse([0,0,s-1,s-1], fill=BG1)
    else: d.rounded_rectangle([0,0,s-1,s-1], radius=int(s*0.22), fill=BG1)
    cx = cy = s/2; R = s*0.36
    d.ellipse([cx-R-s*0.03, cy-R-s*0.03+s*0.03, cx+R+s*0.03, cy+R+s*0.03+s*0.03], fill=RIM)
    cy2 = cy+s*0.03
    for i,c in enumerate(SEGS):
        a0 = -90+i*45 + 10; d.pieslice([cx-R,cy2-R,cx+R,cy2+R], a0, a0+45, fill=c)
    hr = R*0.16; d.ellipse([cx-hr,cy2-hr,cx+hr,cy2+hr], fill=RIM)
    hr2 = R*0.10; d.ellipse([cx-hr2,cy2-hr2,cx+hr2,cy2+hr2], fill=SEGS[0])
    w = s*0.075; top = cy2-R-s*0.075
    d.polygon([(cx-w,top),(cx+w,top),(cx,top+s*0.13)], fill=RIM)
    return im.resize((px,px), Image.LANCZOS)
out = sys.argv[1]
for dens, px in {"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}.items():
    p = os.path.join(out, "res", f"mipmap-{dens}"); os.makedirs(p, exist_ok=True)
    icon(px).save(os.path.join(p,"ic_launcher.png")); icon(px,True).save(os.path.join(p,"ic_launcher_round.png"))
os.makedirs(os.path.join(out,"store"), exist_ok=True)
st = Image.new("RGB",(512,512),BG1); st.paste(icon(512), (0,0), icon(512)); st.save(os.path.join(out,"store","play-store-icon-512.png"))
print("icons done")
