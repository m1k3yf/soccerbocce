#!/usr/bin/env python3
"""Dependency-free PNG generator for SoccerBocce icons + OG image.
Draws flat/anti-aliased circles into an RGBA buffer and writes PNGs with stdlib.
Run:  python3 make_assets.py
"""
import zlib, struct, math, os

def png(path, w, h, px):
    """px: bytearray of RGBA, len = w*h*4"""
    raw = bytearray()
    for y in range(h):
        raw.append(0)                       # filter type 0
        raw += px[y*w*4:(y+1)*w*4]
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(out)
    print("wrote", path, f"{w}x{h}")

def buf(w, h, rgba=(0,0,0,0)):
    b = bytearray(w*h*4)
    for i in range(w*h):
        b[i*4:i*4+4] = bytes(rgba)
    return b

def blend(dst, w, x, y, col):
    if x < 0 or y < 0 or x >= w or y >= len(dst)//(4*w): return
    i = (y*w + x)*4
    sr,sg,sb,sa = col
    a = sa/255
    dst[i]   = int(sr*a + dst[i]*(1-a))
    dst[i+1] = int(sg*a + dst[i+1]*(1-a))
    dst[i+2] = int(sb*a + dst[i+2]*(1-a))
    dst[i+3] = max(dst[i+3], sa)

def circle(dst, w, h, cx, cy, r, col, edge=1.2):
    x0,x1 = int(cx-r-2), int(cx+r+2)
    y0,y1 = int(cy-r-2), int(cy+r+2)
    for y in range(max(0,y0), min(h,y1)):
        for x in range(max(0,x0), min(w,x1)):
            d = math.hypot(x-cx, y-cy)
            if d <= r-edge:
                blend(dst, w, x, y, col)
            elif d < r+edge:
                a = (r+edge - d)/(2*edge)
                blend(dst, w, x, y, (col[0],col[1],col[2], int(col[3]*max(0,min(1,a)))))

def round_bg(dst, w, h, rad, col):
    for y in range(h):
        for x in range(w):
            # rounded-rect mask
            dx = max(rad-x, x-(w-1-rad), 0)
            dy = max(rad-y, y-(h-1-rad), 0)
            if math.hypot(dx,dy) <= rad:
                blend(dst, w, x, y, col)

def vgrad(dst, w, h, top, bot):
    for y in range(h):
        t = y/(h-1)
        col = tuple(int(top[k]*(1-t)+bot[k]*t) for k in range(3)) + (255,)
        for x in range(w):
            blend(dst, w, x, y, col)

def soccer_ball(dst, w, h, cx, cy, r, base, dark):
    circle(dst, w, h, cx, cy, r, base)
    # pentagon-ish spots
    circle(dst, w, h, cx, cy, r*0.20, dark, edge=1.0)
    for k in range(5):
        a = k/5*math.tau - math.pi/2
        circle(dst, w, h, cx+math.cos(a)*r*0.55, cy+math.sin(a)*r*0.55, r*0.15, dark, edge=1.0)
    # highlight
    circle(dst, w, h, cx-r*0.35, cy-r*0.35, r*0.28, (255,255,255,60), edge=1.5)

def make_icon(size, path):
    w=h=size
    d = buf(w,h)
    round_bg(d,w,h,int(size*0.22),(11,61,46,255))      # green tile
    # subtle radial light
    circle(d,w,h,w*0.5,h*0.32,size*0.5,(255,255,255,18),edge=size*0.4)
    soccer_ball(d,w,h,w*0.37,h*0.58,size*0.20,(25,176,110,255),(8,60,42,255))   # green ball
    soccer_ball(d,w,h,w*0.66,h*0.50,size*0.20,(196,58,61,255),(77,18,20,255))   # maroon ball
    circle(d,w,h,w*0.55,h*0.34,size*0.055,(255,255,255,255))                    # pallina
    png(path,w,h,d)

def make_og(path):
    w,h = 1200,630
    d = buf(w,h)
    vgrad(d,w,h,(10,64,46),(4,16,11))
    # field stripes
    for y in range(0,h,70):
        c = (255,255,255,10) if (y//70)%2 else (0,0,0,16)
        for yy in range(y,min(h,y+35)):
            for x in range(w):
                blend(d,w,x,yy,c)
    soccer_ball(d,w,h,800,330,150,(25,176,110,255),(8,60,42,255))
    soccer_ball(d,w,h,1010,420,150,(196,58,61,255),(77,18,20,255))
    circle(d,w,h,915,250,42,(255,255,255,255))   # pallina
    png(path,w,h,d)

if __name__ == "__main__":
    os.makedirs("icons", exist_ok=True)
    make_icon(192, "icons/icon-192.png")
    make_icon(512, "icons/icon-512.png")
    make_og("og.png")
    print("done")
