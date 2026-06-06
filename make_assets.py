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

def ring(dst, w, h, cx, cy, R, thick, col):
    x0, x1 = int(cx-R-thick-1), int(cx+R+thick+1)
    y0, y1 = int(cy-R-thick-1), int(cy+R+thick+1)
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            dd = math.hypot(x-cx, y-cy)
            if abs(dd-R) <= thick:
                a = 1 - abs(dd-R)/thick
                blend(dst, w, x, y, (col[0], col[1], col[2], int(col[3]*max(0, min(1, a)))))

def hline(dst, w, h, x0, x1, y, thick, col):
    for yy in range(int(y-thick), int(y+thick)):
        for x in range(int(x0), int(x1)):
            if 0 <= x < w and 0 <= yy < h: blend(dst, w, x, yy, col)

def vline(dst, w, h, y0, y1, x, thick, col):
    for xx in range(int(x-thick), int(x+thick)):
        for y in range(int(y0), int(y1)):
            if 0 <= xx < w and 0 <= y < h: blend(dst, w, xx, y, col)

def boxline(dst, w, h, x, y, bw, bh, thick, col):
    hline(dst, w, h, x, x+bw, y, thick, col); hline(dst, w, h, x, x+bw, y+bh, thick, col)
    vline(dst, w, h, y, y+bh, x, thick, col); vline(dst, w, h, y, y+bh, x+bw, thick, col)

def shadow(dst, w, h, cx, cy, r):
    circle(dst, w, h, cx+4, cy+10, r*0.95, (0, 0, 0, 70), edge=4)

def make_portfolio(path):
    """4:3 beauty-shot tile of the SoccerBocce pitch for the portfolio grid."""
    w, h = 1000, 750
    d = buf(w, h, (110, 74, 43, 255))           # wooden frame (full bleed)
    m = 22
    # green pitch (vertical light gradient)
    for y in range(m, h-m):
        t = (y-m)/(h-2*m)
        col = tuple(int(a*(1-t)+b*t) for a, b in zip((30, 116, 78), (12, 70, 46))) + (255,)
        for x in range(m, w-m): blend(d, w, x, y, col)
    # mowing stripes
    for y in range(m, h-m, 60):
        c = (255, 255, 255, 12) if (y//60) % 2 else (0, 0, 0, 16)
        for yy in range(y, min(h-m, y+30)):
            for x in range(m, w-m): blend(d, w, x, yy, c)
    # markings
    line = (255, 255, 255, 70)
    hline(d, w, h, m, w-m, h/2, 1.4, line)                       # halfway
    ring(d, w, h, w/2, h/2, 96, 1.8, line)                       # centre circle
    circle(d, w, h, w/2, h/2, 4, (255, 255, 255, 120))           # centre spot
    boxline(d, w, h, w/2-210, h-m-150, 420, 150, 1.8, line)      # penalty box (bottom)
    boxline(d, w, h, w/2-115, h-m-66, 230, 66, 1.8, line)        # goal box (bottom)
    boxline(d, w, h, w/2-210, m, 420, 150, 1.8, line)            # penalty box (top)
    # vignette
    cx, cy, maxd = w/2, h/2, math.hypot(w/2, h/2)
    for y in range(m, h-m):
        for x in range(m, w-m):
            a = int(130*max(0, math.hypot(x-cx, y-cy)/maxd - 0.45))
            if a > 0: blend(d, w, x, y, (0, 0, 0, a))
    # balls clustered around the pallina (with soft shadows)
    G, GD = (34, 200, 120, 255), (8, 60, 42, 255)
    R, RD = (214, 78, 76, 255), (74, 18, 20, 255)
    balls = [(430, 400, G, GD), (560, 320, R, RD), (610, 430, G, GD),
             (520, 470, R, RD), (690, 360, G, GD)]
    for bx, by, *_ in balls: shadow(d, w, h, bx, by, 52)
    circle(d, w, h, 545, 405, 22, (255, 255, 255, 255))          # pallina
    circle(d, w, h, 545, 405, 22, (190, 184, 168, 90), edge=3)
    for bx, by, base, dk in balls: soccer_ball(d, w, h, bx, by, 52, base, dk)
    png(path, w, h, d)

if __name__ == "__main__":
    os.makedirs("icons", exist_ok=True)
    os.makedirs("portfolio", exist_ok=True)
    make_icon(192, "icons/icon-192.png")
    make_icon(512, "icons/icon-512.png")
    make_og("og.png")
    make_portfolio("portfolio/soccerbocce.png")
    print("done")
