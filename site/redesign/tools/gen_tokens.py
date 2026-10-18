import json, sys, re
ref=lambda v: re.sub(r"\{([a-z0-9-]+)\}", r"var(--\1)", v) if isinstance(v,str) else v
t = json.load(open(sys.argv[1]))
out = sys.argv[2]
themes = ["light", "dark", "light-hc", "dark-hc"]
static, themed = [], {th: [] for th in themes}
def emit(name, value):
    if isinstance(value, dict):
        for th in themes:
            themed[th].append(f"  --{name}: {ref(value.get(th, value.get('light')))};")
    else:
        static.append(f"  --{name}: {ref(value)};")
for tok in t["color"]["tokens"]:
    emit(tok["name"], tok["value"])
for grp in ["spacing", "radius", "shadow", "size", "blur"]:
    for tok in t[grp]["tokens"]:
        emit(tok["name"], tok["value"])
fam = t["type"]["families"]
for k, v in fam.items():
    static.append(f"  --font-{k}: {v};")
classes = []
for g in t["type"]["groups"]:
    f = g.get("family", "sans")
    for s in g["styles"]:
        n = s["name"]
        static.append(f"  --{n}-size: {s['fontSize']}; --{n}-line: {s['lineHeight']}; --{n}-weight: {s['fontWeight']}; --{n}-tracking: {s.get('letterSpacing','0')};")
        classes.append(f".t-{n} {{ font-family: var(--font-{s.get('family', f)}, var(--font-sans)); font-size: var(--{n}-size); line-height: var(--{n}-line); font-weight: var(--{n}-weight); letter-spacing: var(--{n}-tracking); }}")
def block(sel, lines): return sel + " {\n" + "\n".join(lines) + "\n}\n"
css = "/* Generated from HIG Native tokens.json. Do not edit by hand. */\n"
css += block(":root", static)
css += block(':root, :root[data-theme="light"]', themed["light"] + ["  color-scheme: light;"])
css += "@media (prefers-color-scheme: dark) {\n" + block(':root:not([data-theme="light"])', themed["dark"] + ["  color-scheme: dark;"]) + "}\n"
css += "@media (prefers-contrast: more) {\n" + block(':root:not([data-theme="light"]):not([data-theme="dark"])', themed["light-hc"]) + "}\n"
css += "@media (prefers-color-scheme: dark) and (prefers-contrast: more) {\n" + block(':root:not([data-theme="light"]):not([data-theme="dark"])', themed["dark-hc"]) + "}\n"
for th in themes:
    css += block(f':root[data-theme="{th}"]', themed[th] + [f"  color-scheme: {'dark' if 'dark' in th else 'light'};"])
css += "\n".join(classes) + "\n"
open(out, "w").write(css)
print(len(static), sum(len(v) for v in themed.values()), len(classes))
