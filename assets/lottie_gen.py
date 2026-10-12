"""Generates the 4 SPRY clinic-day Lottie scenes (640x400, 30fps, 6s).
Frames 0-120 = intro build, 120-180 = idle loop (UI plays [0,120] then loops [120,180])."""
import json, sys, os

W, H, FR, OP = 640, 400, 30, 180

def hexc(h, a=1):
    h = h.lstrip('#')
    return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)] + [a]

# SPRY palette: navy + coral + warm peach. ('blue'/'green' keys kept as aliases so scenes stay readable.)
C = dict(navy='#0B1230', navy2='#1C2550', coral='#EE6A3C', coral2='#F6A27F', blue='#EE6A3C', blue2='#F6A27F',
         tint='#FDE1D3', tint2='#FFF3EC', white='#FFFFFF', wall='#FBF3EA', wall2='#F4E6D6', floor='#E8D5BF',
         floor2='#DCC4A8', green='#0B1230', green2='#FDE1D3', skin1='#F2C4A0', skin2='#9C6644', skin3='#D79B72',
         hair1='#3A2418', hair2='#1A1A1A', hair3='#7A4A2A', grey='#C9CEDD', grey2='#E7EAF2', wood='#B88A62',
         wood2='#9C7050', plant='#4E9A6B', plant2='#2F7A4F', sky='#FFE3CC', sun='#FFD9A8')

EI = {"x": [0.33], "y": [1]}
EO = {"x": [0.67], "y": [0]}
LIN_I = {"x": [1], "y": [1]}
LIN_O = {"x": [0], "y": [0]}

def K(v):
    return {"a": 0, "k": v}

def A(keys, linear=False):
    """keys: list of (t, value). value number or list."""
    dd = []
    for t, v in keys:
        if dd and t <= dd[-1][0]:
            dd[-1] = (dd[-1][0], v) if t == dd[-1][0] else dd[-1]
            continue
        dd.append((t, v))
    keys = dd
    out = []
    for i, (t, v) in enumerate(keys):
        v = v if isinstance(v, list) else [v]
        kf = {"t": t, "s": v}
        if i < len(keys) - 1:
            kf["i"] = LIN_I if linear else EI
            kf["o"] = LIN_O if linear else EO
        out.append(kf)
    return {"a": 1, "k": out}

def prop(v):
    if isinstance(v, dict):
        return v
    return K(v)

def gtr(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    return {"ty": "tr", "nm": "tr", "p": prop(list(p) if isinstance(p, tuple) else p),
            "a": prop(list(a) if isinstance(a, tuple) else a), "s": prop(list(s) if isinstance(s, tuple) else s),
            "r": prop(r), "o": prop(o), "sk": K(0), "sa": K(0)}

def fill(col, o=100):
    return {"ty": "fl", "nm": "fill", "c": K(hexc(C.get(col, col))), "o": prop(o), "r": 1, "bm": 0}

def stroke(col, w, o=100):
    return {"ty": "st", "nm": "stroke", "c": K(hexc(C.get(col, col))), "o": prop(o), "w": prop(w), "lc": 2, "lj": 2, "bm": 0}

def grp(items, nm="g", **t):
    return {"ty": "gr", "nm": nm, "it": items + [gtr(**t)], "np": len(items)}

def rect(x, y, w, h, col, r=0, st=None, sw=2, **t):
    items = [{"ty": "rc", "nm": "rc", "d": 1, "s": K([w, h]), "p": K([x + w / 2, y + h / 2]), "r": K(r)}]
    if col: items.append(fill(col))
    if st: items.append(stroke(st, sw))
    if ('r' in t or 's' in t) and 'p' not in t:
        t['p'] = t['a'] = (x + w / 2, y + h / 2)
    return grp(items, "rect", **t)

def ell(cx, cy, w, h, col, st=None, sw=2, **t):
    items = [{"ty": "el", "nm": "el", "d": 1, "s": K([w, h]), "p": K([cx, cy])}]
    if col: items.append(fill(col))
    if st: items.append(stroke(st, sw))
    if ('r' in t or 's' in t) and 'p' not in t:
        t['p'] = t['a'] = (cx, cy)
    return grp(items, "ell", **t)

def pathd(pts, closed=False):
    n = len(pts)
    return {"ty": "sh", "nm": "sh", "ks": K({"i": [[0, 0]] * n, "o": [[0, 0]] * n, "v": [list(p) for p in pts], "c": closed})}

def poly(pts, col, closed=True, **t):
    return grp([pathd(pts, closed), fill(col)], "poly", **t)

def line(pts, col, w, trim=None, o=100, **t):
    items = [pathd(pts)]
    if trim is not None:
        items.append({"ty": "tm", "nm": "trim", "s": K(0), "e": trim, "o": K(0), "m": 1})
    items.append(stroke(col, w, o))
    return grp(items, "line", **t)

_ind = [0]

def layer(name, shapes, pivot=(0, 0), pos=None, s=None, r=None, o=None, ip=0, op=OP):
    """Shapes are drawn in comp coordinates; pivot is the anchor. pos keys are OFFSETS from pivot."""
    _ind[0] += 1
    px, py = pivot
    if pos is None:
        p = K([px, py])
    else:
        p = A([(t, [px + d[0], py + d[1]]) for t, d in pos])
    ks = {"o": prop(o if o is not None else 100), "r": prop(r if r is not None else 0), "p": p,
          "a": K([px, py]), "s": prop(s if s is not None else [100, 100])}
    return {"ddd": 0, "ind": _ind[0], "ty": 4, "nm": name, "sr": 1, "ks": ks, "ao": 0,
            "shapes": shapes[::-1], "ip": ip, "op": op, "st": 0, "bm": 0}

def pop(t0, dur=14, over=112):
    """scale 0 -> over -> 100"""
    return A([(0, [0, 0]), (t0, [0, 0]), (t0 + dur * 0.65, [over, over]), (t0 + dur, [100, 100])])

def fade(t0, dur=10, to=100):
    return A([(0, 0), (t0, 0), (t0 + dur, to)])

def growx(t0, dur=16):
    return A([(0, [0, 100]), (t0, [0, 100]), (t0 + dur, [100, 100])])

def growy(t0, dur=16):
    return A([(0, [100, 0]), (t0, [100, 0]), (t0 + dur, [100, 100])])

def pulse_ring(cx, cy, d, col, t0=120, period=60):
    """expanding/fading ring during idle loop"""
    keys_s, keys_o = [(0, [100, 100]), (t0 - 1, [100, 100])], [(0, 0), (t0 - 1, 0)]
    t = t0
    while t < OP:
        keys_s += [(t, [100, 100]), (min(t + period - 1, OP), [190, 190])]
        keys_o += [(t, 70), (min(t + period - 1, OP), 0)]
        t += period
    return layer("pulse", [ell(cx, cy, d, d, None, st=col, sw=3)], pivot=(cx, cy), s=A(keys_s, True), o=A(keys_o, True))

def bob(amp=3, period=60, t0=0, axis=1):
    keys = []
    t = t0
    flip = 0
    while t <= OP:
        d = [0, 0]
        d[axis] = -amp if flip else 0
        keys.append((t, d))
        t += period / 2
        flip ^= 1
    return keys

def comp(name, layers):
    return {"v": "5.7.4", "fr": FR, "ip": 0, "op": OP, "w": W, "h": H, "nm": name, "ddd": 0, "assets": [],
            "layers": layers}

# ---------- reusable scene parts ----------

def room_bg(wall='wall', floor='floor', floor_y=300):
    return layer("room", [
        rect(0, 0, W, floor_y, wall),
        rect(0, floor_y, W, H - floor_y, floor),
        rect(0, floor_y, W, 6, 'floor2'),
    ])

def window(x, y, w, h):
    return layer("window", [
        rect(x, y, w, h, 'white', r=8),
        rect(x + 8, y + 8, w - 16, h - 16, 'sky', r=4),
        ell(x + w * 0.72, y + h * 0.35, 34, 34, 'sun'),
        rect(x + 8, y + h * 0.5 - 2, w - 16, 4, 'white'),
        rect(x + w / 2 - 2, y + 8, 4, h - 16, 'white'),
    ])

def plant(x, base):
    return layer("plant", [
        ell(x - 12, base - 54, 26, 44, 'plant', r=-25),  # leaves behind pot
        ell(x + 12, base - 58, 26, 46, 'plant2', r=25),
        ell(x, base - 70, 24, 50, 'plant'),
        rect(x - 18, base - 34, 36, 34, 'coral', r=6),
    ], pivot=(x, base), r=A([(0, 0), (60, 2), (120, -2), (180, 0)]))

def head(cx, cy, skin, hair, d=34, style=0):
    items = []
    if style == 1:  # bun
        items.append(ell(cx + 2, cy - d * 0.55, d * 0.45, d * 0.45, hair))
    items.append(ell(cx, cy - d * 0.12, d * 1.02, d * 0.78, hair))
    items.append(ell(cx, cy, d, d, skin))
    return items

# ---------- Scene 1: Front desk ----------

def scene_front_desk():
    _ind[0] = 0
    L = []
    # intake tablet card (top layer group, built bottom-up later)
    cx0, cy0 = 470, 120
    card = [rect(400, 22, 190, 140, 'white', r=14, st='tint', sw=2)]
    L_card = layer("intake-card", card, pivot=(495, 162), s=pop(34, 14, 106))
    lines = []
    for i, (w, t0) in enumerate([(110, 50), (86, 60), (120, 70), (70, 80)]):
        y = 56 + i * 24
        lines.append(layer(f"field-{i}", [rect(442, y, w, 8, 'grey2', r=4)], pivot=(432, y + 4)))
        lines.append(layer(f"field-fill-{i}", [rect(442, y, w, 8, 'blue2', r=4)], pivot=(442, y + 4), s=growx(t0, 12)))
        lines.append(layer(f"check-{i}", [rect(418, y - 3, 14, 14, 'blue', r=4),
                                           line([(421.5, y + 4), (424.5, y + 7), (429, y + 1)], 'white', 2)],
                           pivot=(425, y + 4), s=pop(t0 + 10, 10, 120)))
    header = layer("card-head", [rect(418, 34, 70, 8, 'navy', r=4), ell(570, 38, 12, 12, 'blue')], pivot=(495, 162),
                   s=pop(34, 14, 106))
    # eligibility badge
    badge = layer("elig-badge", [
        rect(448, 176, 142, 34, 'green2', r=17, st='green', sw=2),
        ell(468, 193, 20, 20, 'green'),
        line([(462.5, 193), (466.5, 197), (473.5, 189)], 'white', 2.6),
        rect(486, 189, 88, 8, 'green', r=4),
    ], pivot=(519, 193), s=pop(96, 16, 116))
    ring = pulse_ring(468, 193, 26, 'green')
    # insurance card sliding from patient to desk
    ins = layer("insurance-card", [rect(280, 214, 46, 30, 'blue', r=5), rect(286, 222, 20, 5, 'white', r=2),
                                   rect(286, 231, 30, 4, 'blue2', r=2)],
                pivot=(303, 229), pos=[(0, (40, 10)), (44, (40, 10)), (66, (0, 0))],
                o=A([(0, 0), (44, 0), (50, 100)]))
    # desk
    desk = layer("desk", [
        rect(60, 236, 280, 18, 'wood2', r=6),
        rect(70, 252, 260, 70, 'wood', r=4),
        rect(90, 268, 220, 6, 'wood2', r=3),
        rect(205, 192, 64, 44, 'navy', r=6), rect(211, 198, 52, 32, 'blue', r=3),
        rect(232, 236, 10, 4, 'navy'),
    ])
    screen_glow = layer("screen-lines", [rect(217, 205, 30, 4, 'white', r=2), rect(217, 214, 40, 4, 'blue2', r=2),
                                         rect(217, 222, 22, 4, 'blue2', r=2)], pivot=(217, 214), s=growx(54, 20))
    # front desk staff (behind desk)
    staff = layer("staff", [
        rect(122, 196, 64, 70, 'navy2', r=24),
        *head(154, 176, 'skin2', 'hair2', 36, 1),
    ], pivot=(154, 236), pos=bob(2, 90))
    staff_arm = layer("staff-arm", [line([(176, 214), (200, 228)], 'navy2', 12)], pivot=(176, 214),
                      r=A([(0, 0), (60, -12), (70, 0), (120, 0), (150, -8), (180, 0)]))
    # patient walking in
    pat_walk = [(0, (260, 0)), (40, (0, 0))] + [(t, d) for t, d in bob(3, 40, 60)]
    patient = layer("patient", [
        rect(452 - 400 + 400, 0, 0, 0, None) if False else rect(360, 294, 18, 60, 'navy2', r=8),
        rect(384, 294, 18, 60, 'navy2', r=8),
        rect(352, 206, 58, 98, 'coral', r=24),
        *head(381, 186, 'skin1', 'hair3', 38),
    ], pivot=(381, 300), pos=pat_walk)
    pat_arm = layer("patient-arm", [line([(358, 226), (330, 238)], 'blue', 12)], pivot=(358, 226),
                    pos=[(0, (260, 0)), (40, (0, 0))], r=A([(0, 20), (40, 20), (56, 0), (80, 0), (96, 20)]))
    # order: top first
    L = [ring, badge, header] + lines[::-1] + [L_card, ins, pat_arm, patient, desk, screen_glow, staff_arm, staff,
                                              plant(604, 300), window(30, 30, 130, 96), room_bg()]
    # screen lines should be above desk
    L.remove(screen_glow)
    L.insert(L.index(desk), screen_glow)
    return comp("SPRY Front desk", L)

# ---------- Scene 2: Treatment gym ----------

def scene_gym():
    _ind[0] = 0
    # plinth
    plinth = layer("plinth", [
        rect(70, 228, 230, 18, 'navy2', r=6),
        rect(90, 246, 12, 60, 'grey'), rect(268, 246, 12, 60, 'grey'),
        rect(76, 216, 70, 14, 'tint', r=7),
    ])
    # patient seated, knee extension
    patient = layer("patient", [
        rect(140, 214, 90, 22, 'navy2', r=11),  # thigh
        rect(118, 140, 52, 92, 'coral', r=22),
        *head(146, 120, 'skin3', 'hair1', 36),
    ])
    shin = layer("shin", [rect(214, 222, 20, 76, 'navy2', r=10), rect(206, 290, 36, 14, 'navy', r=6)],
                 pivot=(224, 226),
                 r=A([(0, 0), (30, -70), (45, -70), (75, 0), (90, 0), (120, -70), (135, -70), (165, 0), (180, 0)]))
    pat_arm = layer("patient-arm", [line([(150, 170), (178, 214)], 'coral', 12)])
    # parallel bars background
    bars = layer("bars", [rect(300, 168, 4, 132, 'grey'), rect(330, 168, 4, 132, 'grey'),
                          rect(296, 168, 70, 6, 'grey', r=3)], o=60)
    # therapist
    ther = layer("therapist", [
        rect(258, 300 - 64, 16, 66, 'navy', r=8), rect(280, 236, 16, 66, 'navy', r=8),
        rect(250, 140, 54, 104, 'white', r=22, st='tint', sw=3),
        rect(270, 150, 14, 40, 'blue', r=4),
        *head(277, 118, 'skin1', 'hair2', 36, 1),
    ], pivot=(277, 300), pos=bob(2, 60))
    tablet = layer("tablet", [rect(220, 176, 30, 40, 'navy', r=5), rect(224, 181, 22, 30, 'blue2', r=2)],
                   pivot=(235, 196), r=A([(0, -8), (90, -4), (180, -8)]))
    ther_arm = layer("therapist-arm", [line([(258, 162), (238, 192)], 'white', 12), ], o=100)
    # AI orb + waveform
    orb = [ell(380, 120, 54, 54, 'blue'), ell(380, 120, 70, 70, 'blue', ), ]
    orb_l = layer("orb", [ell(380, 120, 52, 52, 'blue')], pivot=(380, 120), s=pop(10, 14, 115))
    orb_glow = layer("orb-glow", [ell(380, 120, 76, 76, 'blue')], pivot=(380, 120), o=A([(0, 0), (10, 0), (24, 25), (60, 12), (90, 25), (120, 12), (150, 25), (180, 12)]))
    wave = []
    for i, dx in enumerate([-14, -7, 0, 7, 14]):
        hs = [(0, [100, 30])]
        t = 0
        while t < 180:
            hs.append((t + 6 + i * 2, [100, [100, 60, 140, 80, 120][(i + t // 10) % 5]]))
            t += 12
        hs = [(min(tt, 180), v) for tt, v in hs]
        # dedupe times
        seen, hk = set(), []
        for tt, v in hs:
            if tt in seen: continue
            seen.add(tt); hk.append((tt, v))
        wave.append(layer(f"wave-{i}", [rect(380 + dx - 2.5, 108, 5, 24, 'white', r=2.5)], pivot=(380 + dx, 120),
                          s=A(hk, True), o=fade(14, 6)))
    link = layer("orb-link", [line([(404, 128), (430, 150), (452, 150)], 'blue2', 3,
                                   trim=A([(0, 0), (20, 0), (40, 100)]))])
    # SOAP panel
    panel = layer("soap-panel", [rect(452, 58, 160, 214, 'white', r=14, st='tint', sw=2),
                                 rect(468, 72, 70, 8, 'navy', r=4)], pivot=(532, 272), s=pop(24, 14, 105))
    soap = []
    for i, (w1, w2) in enumerate([(100, 70), (110, 60), (90, 80), (106, 50)]):
        y = 98 + i * 40
        t0 = 40 + i * 18
        soap.append(layer(f"key-{i}", [rect(468, y, 18, 18, 'blue', r=5)], pivot=(477, y + 9), s=pop(t0, 8, 125)))
        soap.append(layer(f"l1-{i}", [rect(494, y + 1, w1, 6, 'grey', r=3)], pivot=(494, y + 4), s=growx(t0 + 2, 10)))
        soap.append(layer(f"l2-{i}", [rect(494, y + 11, w2, 6, 'grey2', r=3)], pivot=(494, y + 14), s=growx(t0 + 7, 10)))
    done = layer("signed", [rect(468, 250 - 2, 128, 0.1, None) if False else rect(480, 240, 104, 22, 'green', r=11),
                            line([(492, 251), (496, 255), (503, 247)], 'white', 2.6),
                            rect(510, 248, 62, 6, 'white', r=3)], pivot=(532, 251), s=pop(118, 12, 112))
    ring = pulse_ring(497, 251, 20, 'green', t0=130)
    L = [ring, done] + soap[::-1] + [panel, link] + wave[::-1] + [orb_l, orb_glow,
         ther_arm, tablet, ther, pat_arm, shin, patient, plinth, bars,
         layer("wall-art", [rect(40, 40, 120, 70, 'tint', r=8), poly([(52, 98), (84, 66), (108, 90), (124, 76), (148, 98)], 'blue2')]),
         room_bg()]
    return comp("SPRY Treatment gym", L)

# ---------- Scene 3: Billing ----------

def scene_billing():
    _ind[0] = 0
    desk = layer("desk", [rect(40, 236, 280, 16, 'wood2', r=6), rect(60, 252, 12, 56, 'wood2'), rect(288, 252, 12, 56, 'wood2'),
                          rect(150, 160, 110, 72, 'navy', r=8), rect(157, 167, 96, 58, 'tint', r=4),
                          rect(198, 232, 14, 6, 'navy')])
    screen = layer("screen", [rect(165, 176, 40, 6, 'navy', r=3), rect(165, 188, 76, 5, 'blue2', r=2.5),
                              rect(165, 198, 60, 5, 'blue2', r=2.5), rect(165, 208, 70, 5, 'blue2', r=2.5)],
                   pivot=(165, 192), s=growx(4, 18))
    staff = layer("staff", [rect(76, 168, 58, 84, 'coral', r=22), *head(105, 148, 'skin1', 'hair1', 36, 1)],
                  pivot=(105, 250), pos=bob(2, 90))
    arm = layer("staff-arm", [line([(126, 196), (156, 228)], 'coral', 12)], pivot=(126, 196),
                r=A([(0, 0), (8, 8), (14, 0), (20, 8), (26, 0), (180, 0)]))
    # payer building
    payer = layer("payer", [
        poly([(470, 150), (540, 118), (610, 150)], 'navy'),
        rect(474, 150, 132, 10, 'navy2'),
        rect(484, 164, 12, 70, 'tint'), rect(512, 164, 12, 70, 'tint'), rect(540, 164, 12, 70, 'tint'),
        rect(568, 164, 12, 70, 'tint'), rect(588, 164, 8, 70, 'tint'),
        rect(470, 234, 140, 14, 'navy2', r=3),
    ])
    payer_check = layer("payer-check", [ell(540, 86, 34, 34, 'green'),
                                        line([(531, 86), (537, 92), (549, 79)], 'white', 3.4)],
                        pivot=(540, 86), s=pop(74, 12, 120))
    ring = pulse_ring(540, 86, 34, 'green', t0=120)
    # claim documents flying along arc
    def claim(name, t0):
        doc = [rect(-22, -28, 44, 56, 'white', r=5, st='blue', sw=2.5),
               rect(-13, -18, 22, 5, 'navy', r=2.5), rect(-13, -7, 26, 4, 'blue2', r=2),
               rect(-13, 1, 26, 4, 'blue2', r=2), rect(-13, 9, 16, 4, 'coral', r=2),
               ell(13, 18, 12, 12, 'green')]
        path = [(0, (205, 196)), (t0, (205, 196)), (t0 + 14, (300, 110)), (t0 + 28, (420, 90)), (t0 + 42, (528, 186))]
        return layer(name, doc, pivot=(0, 0),
                     pos=[(t, d) for t, d in path] if t0 > 0 else path[1:],
                     s=A([(0, [60, 60]), (t0, [60, 60]), (t0 + 14, [120, 120]), (t0 + 42, [50, 50])]),
                     o=A([(0, 0), (t0, 0), (t0 + 4, 100), (t0 + 38, 100), (t0 + 42, 0)]),
                     r=A([(0, 0), (t0, 0), (t0 + 20, -12), (t0 + 42, 8)]))
    c1, c2, c3 = claim("claim-1", 20), claim("claim-2", 44), claim("claim-3", 130)
    # prior auth progress bar
    bar_bg = layer("auth-bg", [rect(40, 40, 260, 56, 'white', r=12, st='tint', sw=2),
                               rect(56, 54, 80, 7, 'navy', r=3.5), rect(56, 72, 200, 10, 'grey2', r=5)],
                   pivot=(170, 68), s=pop(6, 12, 104))
    bar_fill = layer("auth-fill", [rect(56, 72, 200, 10, 'blue', r=5)], pivot=(56, 77),
                     s=A([(0, [0, 100]), (24, [0, 100]), (60, [55, 100]), (80, [70, 100]), (104, [100, 100])]))
    auth_ok = layer("auth-ok", [ell(276, 77, 22, 22, 'green'), line([(270.5, 77), (274.5, 81), (281.5, 73)], 'white', 2.6)],
                    pivot=(276, 77), s=pop(104, 10, 120))
    L = [ring, payer_check, c3, c2, c1, auth_ok, bar_fill, bar_bg, payer, screen, desk, arm, staff,
         plant(350, 300), room_bg()]
    # screen must be above desk
    return comp("SPRY Billing", L)

# ---------- Scene 4: Owner office ----------

def scene_owner():
    _ind[0] = 0
    board = layer("board", [rect(170, 40, 300, 180, 'navy', r=14), rect(182, 52, 276, 156, 'navy2', r=8),
                            rect(196, 64, 70, 8, 'white', r=4), ell(442, 68, 10, 10, 'green')],
                  pivot=(320, 130), s=pop(0, 14, 103))
    bars = []
    heights = [40, 62, 54, 80, 96]
    for i, hgt in enumerate(heights):
        x = 200 + i * 24
        bars.append(layer(f"bar-{i}", [rect(x, 190 - hgt, 14, hgt, 'coral' if i == 4 else 'coral2', r=4)],
                          pivot=(x + 7, 190),
                          s=A([(0, [100, 0]), (14 + i * 6, [100, 0]), (32 + i * 6, [100, 100]),
                               (150, [100, 100]), (165, [100, 90 + (i % 2) * 14]), (180, [100, 100])])))
    chart = layer("trend", [line([(332, 176), (356, 160), (378, 166), (402, 136), (426, 128), (446, 100)], 'sun', 4,
                                 trim=A([(0, 0), (30, 0), (80, 100)]))])
    dot = layer("trend-dot", [ell(446, 100, 12, 12, 'sun')], pivot=(446, 100), s=pop(78, 10, 130))
    donut_bg = layer("donut-bg", [ell(560, 110, 76, 76, None, st='grey2', sw=12)], pivot=(560, 110), s=pop(20, 12, 105))
    donut = layer("donut", [grp([{"ty": "el", "nm": "el", "d": 1, "s": K([76, 76]), "p": K([560, 110])},
                                 {"ty": "tm", "nm": "trim", "s": K(0), "e": A([(0, 0), (36, 0), (90, 92)]), "o": K(0), "m": 1},
                                 stroke('coral', 12)], "donut")], pivot=(560, 110), r=-90)
    donut_c = layer("donut-center", [ell(560, 110, 18, 18, 'coral')], pivot=(560, 110), s=pop(90, 10, 110))
    card = layer("donut-card", [rect(506, 56, 108, 110, 'white', r=14, st='tint', sw=2)], pivot=(560, 110), s=pop(16, 12, 104))
    notif = layer("notif", [rect(500, 186, 120, 30, 'white', r=15, st='green', sw=2),
                            ell(518, 201, 14, 14, 'green'), rect(532, 197, 72, 8, 'grey', r=4)],
                  pivot=(560, 201), s=pop(100, 12, 110),
                  pos=[(0, (0, 0)), (120, (0, 0)), (150, (0, -3)), (180, (0, 0))])
    desk = layer("desk", [rect(120, 262, 340, 16, 'wood2', r=6), rect(140, 278, 12, 40, 'wood2'), rect(428, 278, 12, 40, 'wood2'),
                          rect(318, 222, 80, 42, 'navy', r=6), rect(323, 227, 70, 32, 'blue', r=3)])
    owner = layer("owner", [rect(226, 206, 66, 84, 'navy2', r=24), rect(250, 210, 18, 40, 'white', r=4),
                            *head(259, 186, 'skin3', 'hair2', 38)], pivot=(259, 290), pos=bob(2, 90))
    mug = layer("mug", [rect(194, 240, 22, 24, 'coral', r=5), ell(218, 252, 12, 12, None, st='coral', sw=3)])
    steam = layer("steam", [line([(202, 234), (198, 224), (204, 214), (200, 204)], 'grey', 3),
                            line([(210, 234), (214, 224), (208, 214), (212, 204)], 'grey', 3)],
                  pivot=(206, 234), o=A([(0, 60), (45, 20), (90, 60), (135, 20), (180, 60)]),
                  pos=[(0, (0, 0)), (90, (0, -4)), (180, (0, 0))])
    arm = layer("owner-arm", [line([(282, 228), (318, 252)], 'navy2', 12)], pivot=(282, 228),
                r=A([(0, 0), (40, -6), (80, 0), (120, -6), (160, 0), (180, 0)]))
    L = [notif, donut_c, donut, donut_bg, card, dot, chart] + bars[::-1] + [board, steam, mug, arm, desk, owner,
         plant(80, 300), window(40, 40, 110, 90), room_bg(wall='wall')]
    return comp("SPRY Owner office", L)

if __name__ == "__main__":
    out = sys.argv[1]
    scenes = {"frontDesk": ("lottie-front-desk.json", scene_front_desk()),
              "treatmentGym": ("lottie-treatment-gym.json", scene_gym()),
              "billing": ("lottie-billing.json", scene_billing()),
              "ownerOffice": ("lottie-owner-office.json", scene_owner())}
    bundle = {}
    for key, (fn, data) in scenes.items():
        with open(os.path.join(out, fn), "w") as f:
            json.dump(data, f, separators=(",", ":"))
        bundle[key] = data
    with open(os.path.join(out, "lottie-data.js"), "w") as f:
        f.write("/* SPRY clinic-day Lottie scenes, bundled so the page works from file:// */\nwindow.LOTTIE_DATA = ")
        json.dump(bundle, f, separators=(",", ":"))
        f.write(";\n")
    print("ok")
