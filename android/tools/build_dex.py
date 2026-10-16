#!/usr/bin/env python3
"""
Builds classes.dex for Spin the Wheel without the Android Gradle toolchain.

It assembles two small classes directly in Dalvik bytecode:

  com.ash.spinthewheel.MainActivity  (extends android.app.Activity)
      onCreate: FrameLayout (fitsSystemWindows) > WebView with JS + DOM storage,
      loads file:///android_asset/index.html?app=1 (fully offline).

  com.ash.spinthewheel.Bridge  (extends android.webkit.WebChromeClient)
      onJsPrompt("vib", "<ms>") -> Vibrator.vibrate(ms), so the web page can
      vibrate the phone (Android WebView does not implement navigator.vibrate).

Equivalent Java, for reference:

  public class MainActivity extends Activity {
    protected void onCreate(Bundle b) {
      super.onCreate(b);
      FrameLayout root = new FrameLayout(this);
      root.setFitsSystemWindows(true);
      root.setBackgroundColor(0xff1b1035);
      WebView w = new WebView(this);
      w.setBackgroundColor(0xff1b1035);
      WebSettings s = w.getSettings();
      s.setJavaScriptEnabled(true);
      s.setDomStorageEnabled(true);
      s.setMediaPlaybackRequiresUserGesture(false);
      w.setWebChromeClient(new Bridge(this));
      root.addView(w);
      setContentView(root);
      w.loadUrl("file:///android_asset/index.html?app=1");
    }
  }
  public class Bridge extends WebChromeClient {
    private Context ctx;
    public Bridge(Context c) { ctx = c; }
    public boolean onJsPrompt(WebView v, String url, String msg, String def, JsPromptResult r) {
      if ("vib".equals(msg)) {
        ((Vibrator) ctx.getSystemService("vibrator")).vibrate(Long.parseLong(def));
        r.confirm();
        return true;
      }
      return super.onJsPrompt(v, url, msg, def, r);
    }
  }

Usage: build_dex.py out/classes.dex
"""
import hashlib, struct, sys, zlib

PKG = "Lcom/ash/spinthewheel/"
MAIN = PKG + "MainActivity;"
BRIDGE = PKG + "Bridge;"
BG = 0xFF1B1035

# ---------------------------------------------------------------- references
M = {  # key -> (class, name, return, params)
 "act_init":   ("Landroid/app/Activity;", "<init>", "V", []),
 "act_create": ("Landroid/app/Activity;", "onCreate", "V", ["Landroid/os/Bundle;"]),
 "act_setcv":  ("Landroid/app/Activity;", "setContentView", "V", ["Landroid/view/View;"]),
 "fl_init":    ("Landroid/widget/FrameLayout;", "<init>", "V", ["Landroid/content/Context;"]),
 "fl_fits":    ("Landroid/widget/FrameLayout;", "setFitsSystemWindows", "V", ["Z"]),
 "fl_bg":      ("Landroid/widget/FrameLayout;", "setBackgroundColor", "V", ["I"]),
 "fl_add":     ("Landroid/widget/FrameLayout;", "addView", "V", ["Landroid/view/View;"]),
 "wv_init":    ("Landroid/webkit/WebView;", "<init>", "V", ["Landroid/content/Context;"]),
 "wv_bg":      ("Landroid/webkit/WebView;", "setBackgroundColor", "V", ["I"]),
 "wv_set":     ("Landroid/webkit/WebView;", "getSettings", "Landroid/webkit/WebSettings;", []),
 "wv_chrome":  ("Landroid/webkit/WebView;", "setWebChromeClient", "V", ["Landroid/webkit/WebChromeClient;"]),
 "wv_load":    ("Landroid/webkit/WebView;", "loadUrl", "V", ["Ljava/lang/String;"]),
 "ws_js":      ("Landroid/webkit/WebSettings;", "setJavaScriptEnabled", "V", ["Z"]),
 "ws_dom":     ("Landroid/webkit/WebSettings;", "setDomStorageEnabled", "V", ["Z"]),
 "ws_media":   ("Landroid/webkit/WebSettings;", "setMediaPlaybackRequiresUserGesture", "V", ["Z"]),
 "wcc_init":   ("Landroid/webkit/WebChromeClient;", "<init>", "V", []),
 "wcc_prompt": ("Landroid/webkit/WebChromeClient;", "onJsPrompt", "Z",
                ["Landroid/webkit/WebView;", "Ljava/lang/String;", "Ljava/lang/String;", "Ljava/lang/String;", "Landroid/webkit/JsPromptResult;"]),
 "str_eq":     ("Ljava/lang/String;", "equals", "Z", ["Ljava/lang/Object;"]),
 "ctx_sys":    ("Landroid/content/Context;", "getSystemService", "Ljava/lang/Object;", ["Ljava/lang/String;"]),
 "long_parse": ("Ljava/lang/Long;", "parseLong", "J", ["Ljava/lang/String;"]),
 "vib_vib":    ("Landroid/os/Vibrator;", "vibrate", "V", ["J"]),
 "jpr_ok":     ("Landroid/webkit/JsPromptResult;", "confirm", "V", []),
 # defined methods
 "main_init":  (MAIN, "<init>", "V", []),
 "main_create":(MAIN, "onCreate", "V", ["Landroid/os/Bundle;"]),
 "br_init":    (BRIDGE, "<init>", "V", ["Landroid/content/Context;"]),
 "br_prompt":  (BRIDGE, "onJsPrompt", "Z",
                ["Landroid/webkit/WebView;", "Ljava/lang/String;", "Ljava/lang/String;", "Ljava/lang/String;", "Landroid/webkit/JsPromptResult;"]),
}
F = {"br_ctx": (BRIDGE, "ctx", "Landroid/content/Context;")}
EXTRA_TYPES = ["Landroid/widget/FrameLayout;", "Landroid/webkit/WebView;", "Landroid/os/Vibrator;", BRIDGE, MAIN]
CONST_STRINGS = ["file:///android_asset/index.html?app=1", "vib", "vibrator"]

def shorty_char(t): return "L" if t[0] in "L[" else t
def shorty(ret, params): return shorty_char(ret) + "".join(shorty_char(p) for p in params)

# --- collect pools
types = set(EXTRA_TYPES)
protos = set()
strings = set(CONST_STRINGS)
for c, n, r, ps in M.values():
    types |= {c, r, *ps}; protos.add((r, tuple(ps))); strings.add(n)
for c, n, t in F.values():
    types |= {c, t}; strings.add(n)
for r, ps in protos: strings.add(shorty(r, ps))
strings |= types

def mutf8_key(s): return s.encode("utf-8")  # all ASCII here
strings = sorted(strings, key=mutf8_key)
S = {s: i for i, s in enumerate(strings)}
types = sorted(types, key=lambda t: S[t])
T = {t: i for i, t in enumerate(types)}
protos = sorted(protos, key=lambda p: (T[p[0]], [T[x] for x in p[1]]))
P = {p: i for i, p in enumerate(protos)}
field_list = sorted(F.values(), key=lambda f: (T[f[0]], S[f[1]], T[f[2]]))
FI = {f: i for i, f in enumerate(field_list)}
meth_list = sorted({(c, n, r, tuple(ps)) for c, n, r, ps in M.values()},
                   key=lambda m: (T[m[0]], S[m[1]], P[(m[2], m[3])]))
MI = {m: i for i, m in enumerate(meth_list)}
def mi(k): c, n, r, ps = M[k]; return MI[(c, n, r, tuple(ps))]
def fi(k): return FI[F[k]]

# ---------------------------------------------------------------- assembler
def invoke(op, regs, idx):
    assert len(regs) <= 5
    r = regs + [0] * (5 - len(regs))
    return [(len(regs) << 12) | (r[4] << 8) | op, idx, (r[3] << 12) | (r[2] << 8) | (r[1] << 4) | r[0]]
VIRT, SUPER, DIRECT, STATIC = 0x6e, 0x6f, 0x70, 0x71
def invoke_range(op, first, count, idx): return [(count << 8) | op, idx, first]
def new_inst(a, t): return [(a << 8) | 0x22, T[t]]
def const4(a, v): return [((v & 0xF) << 12) | (a << 8) | 0x12]
def const32(a, v): return [(a << 8) | 0x14, v & 0xFFFF, (v >> 16) & 0xFFFF]
def const_str(a, s): return [(a << 8) | 0x1a, S[s]]
def move_res(a): return [(a << 8) | 0x0a]
def move_res_wide(a): return [(a << 8) | 0x0b]
def move_res_obj(a): return [(a << 8) | 0x0c]
def check_cast(a, t): return [(a << 8) | 0x1f, T[t]]
def iget_obj(a, b, f): return [(b << 12) | (a << 8) | 0x54, f]
def iput_obj(a, b, f): return [(b << 12) | (a << 8) | 0x5b, f]
def if_eqz(a, off): return [(a << 8) | 0x38, off & 0xFFFF]
def ret_void(): return [0x000e]
def ret(a): return [(a << 8) | 0x0f]

def code(regs, ins, outs, parts):
    insns = [u for p in parts for u in p]
    return dict(regs=regs, ins=ins, outs=outs, insns=insns)

# MainActivity.<init>  regs: v0 = this
main_init = code(1, 1, 1, [invoke(DIRECT, [0], mi("act_init")), ret_void()])

# MainActivity.onCreate  regs v0..v3 locals, v4 = this, v5 = bundle
main_create = code(6, 2, 2, [
    invoke(SUPER, [4, 5], mi("act_create")),
    new_inst(0, "Landroid/widget/FrameLayout;"),
    invoke(DIRECT, [0, 4], mi("fl_init")),
    const4(1, 1),
    invoke(VIRT, [0, 1], mi("fl_fits")),
    const32(1, BG),
    invoke(VIRT, [0, 1], mi("fl_bg")),
    new_inst(2, "Landroid/webkit/WebView;"),
    invoke(DIRECT, [2, 4], mi("wv_init")),
    invoke(VIRT, [2, 1], mi("wv_bg")),
    invoke(VIRT, [2], mi("wv_set")),
    move_res_obj(3),
    const4(1, 1),
    invoke(VIRT, [3, 1], mi("ws_js")),
    invoke(VIRT, [3, 1], mi("ws_dom")),
    const4(1, 0),
    invoke(VIRT, [3, 1], mi("ws_media")),
    new_inst(3, BRIDGE),
    invoke(DIRECT, [3, 4], mi("br_init")),
    invoke(VIRT, [2, 3], mi("wv_chrome")),
    invoke(VIRT, [0, 2], mi("fl_add")),
    invoke(VIRT, [4, 0], mi("act_setcv")),
    const_str(3, "file:///android_asset/index.html?app=1"),
    invoke(VIRT, [2, 3], mi("wv_load")),
    ret_void(),
])

# Bridge.<init>(Context)  v0 = this, v1 = ctx
br_init = code(2, 2, 1, [
    invoke(DIRECT, [0], mi("wcc_init")),
    iput_obj(1, 0, fi("br_ctx")),
    ret_void(),
])

# Bridge.onJsPrompt  locals v0..v3, v4=this v5=view v6=url v7=msg v8=def v9=result
head = [const_str(0, "vib"), invoke(VIRT, [0, 7], mi("str_eq")), move_res(0)]
body = [
    iget_obj(0, 4, fi("br_ctx")),
    const_str(1, "vibrator"),
    invoke(VIRT, [0, 1], mi("ctx_sys")),
    move_res_obj(0),
    check_cast(0, "Landroid/os/Vibrator;"),
    invoke(STATIC, [8], mi("long_parse")),
    move_res_wide(2),
    invoke(VIRT, [0, 2, 3], mi("vib_vib")),
    invoke(VIRT, [9], mi("jpr_ok")),
    const4(0, 1),
    ret(0),
]
tail = [invoke_range(SUPER, 4, 6, mi("wcc_prompt")), move_res(0), ret(0)]
skip = 2 + sum(len(p) for p in body)  # if-eqz is 2 units long; jump to tail
br_prompt = code(10, 6, 6, head + [if_eqz(0, skip)] + body + tail)

CLASSES = [  # (type, super, fields[(key, flags)], direct[(key, flags, code)], virtual[...])
    (MAIN, "Landroid/app/Activity;", [], [("main_init", 0x10001, main_init)], [("main_create", 0x0004, main_create)]),
    (BRIDGE, "Landroid/webkit/WebChromeClient;", [("br_ctx", 0x0002)],
     [("br_init", 0x10001, br_init)], [("br_prompt", 0x0001, br_prompt)]),
]

# ---------------------------------------------------------------- writer
def uleb(v):
    out = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        if v: out.append(b | 0x80)
        else: out.append(b); return bytes(out)

def align(buf, n):
    while len(buf) % n: buf.append(0)

HDR = 0x70
n_s, n_t, n_p, n_f, n_m, n_c = len(strings), len(types), len(protos), len(field_list), len(meth_list), len(CLASSES)
off_s = HDR
off_t = off_s + 4 * n_s
off_p = off_t + 4 * n_t
off_f = off_p + 12 * n_p
off_m = off_f + 8 * n_f
off_c = off_m + 8 * n_m
data_off = off_c + 32 * n_c

data = bytearray()
def here(): return data_off + len(data)

# type lists (proto params), 4-aligned
tl_off = {}
tl_start = here(); tl_count = 0
for r, ps in protos:
    if ps and ps not in tl_off:
        align(data, 4)
        tl_off[ps] = here(); tl_count += 1
        data += struct.pack("<I", len(ps)) + b"".join(struct.pack("<H", T[p]) for p in ps)
align(data, 4)

# code items
code_off = {}
code_start = here(); code_count = 0
for _, _, _, direct, virtual in CLASSES:
    for key, _, c in direct + virtual:
        align(data, 4)
        code_off[key] = here(); code_count += 1
        data += struct.pack("<HHHHII", c["regs"], c["ins"], c["outs"], 0, 0, len(c["insns"]))
        data += b"".join(struct.pack("<H", u) for u in c["insns"])
align(data, 4)

# class data
cd_off = {}
cd_start = here()
for cls, _, fields, direct, virtual in CLASSES:
    cd_off[cls] = here()
    data += uleb(0) + uleb(len(fields)) + uleb(len(direct)) + uleb(len(virtual))
    prev = 0
    for key, fl in sorted(fields, key=lambda x: fi(x[0])):
        data += uleb(fi(key) - prev) + uleb(fl); prev = fi(key)
    for lst in (direct, virtual):
        prev = 0
        for key, fl, _ in sorted(lst, key=lambda x: mi(x[0])):
            data += uleb(mi(key) - prev) + uleb(fl) + uleb(code_off[key]); prev = mi(key)

# string data
sd_off = []
sd_start = here()
for s in strings:
    sd_off.append(here())
    data += uleb(len(s)) + s.encode("utf-8") + b"\0"
align(data, 4)

# map list
map_off = here()
items = [
    (0x0000, 1, 0), (0x0001, n_s, off_s), (0x0002, n_t, off_t), (0x0003, n_p, off_p),
    (0x0004, n_f, off_f), (0x0005, n_m, off_m), (0x0006, n_c, off_c),
]
if tl_count: items.append((0x1001, tl_count, tl_start))
items += [(0x2001, code_count, code_start), (0x2000, n_c, cd_start), (0x2002, n_s, sd_start), (0x1000, 1, map_off)]
items.sort(key=lambda x: x[2])
data += struct.pack("<I", len(items)) + b"".join(struct.pack("<HHII", t, 0, sz, off) for t, sz, off in items)

# id sections
ids = bytearray()
ids += b"".join(struct.pack("<I", o) for o in sd_off)
ids += b"".join(struct.pack("<I", S[t]) for t in types)
ids += b"".join(struct.pack("<III", S[shorty(r, ps)], T[r], tl_off.get(ps, 0)) for r, ps in protos)
ids += b"".join(struct.pack("<HHI", T[c], T[t], S[n]) for c, n, t in field_list)
ids += b"".join(struct.pack("<HHI", T[c], P[(r, ps)], S[n]) for c, n, r, ps in meth_list)
for cls, sup, _, _, _ in CLASSES:
    ids += struct.pack("<IIIIIIII", T[cls], 0x0001, T[sup], 0, 0xFFFFFFFF, 0, cd_off[cls], 0)
assert HDR + len(ids) == data_off

file_size = data_off + len(data)
header = bytearray(b"dex\n035\0" + b"\0" * 24)
header += struct.pack("<IIIII", file_size, HDR, 0x12345678, 0, 0)
header += struct.pack("<I", map_off)
header += struct.pack("<II", n_s, off_s) + struct.pack("<II", n_t, off_t) + struct.pack("<II", n_p, off_p)
header += struct.pack("<II", n_f, off_f) + struct.pack("<II", n_m, off_m) + struct.pack("<II", n_c, off_c)
header += struct.pack("<II", len(data), data_off)
assert len(header) == HDR
dex = header + ids + data
dex[12:32] = hashlib.sha1(dex[32:]).digest()
dex[8:12] = struct.pack("<I", zlib.adler32(bytes(dex[12:])) & 0xFFFFFFFF)

out = sys.argv[1] if len(sys.argv) > 1 else "classes.dex"
open(out, "wb").write(dex)
print(f"wrote {out}: {file_size} bytes, {n_s} strings, {n_t} types, {n_m} methods")
