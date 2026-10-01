"""The Components board every design gets: the magnet rail, the glass switch, icons, type, palettes.

It is the build reference for the team. It uses the design's own tokens, so it themes with the
switch like every other board.
"""
from __future__ import annotations

import kit
from kit import PAGES, ICON_FOR, esc, ferro_svg, squircle

COMP_CSS = """
.cmp{padding:88px 96px 96px 140px;display:flex;flex-direction:column;gap:72px}
.cmp h1{margin:0;font-size:52px;line-height:1.05;letter-spacing:-.02em}
.cmp h2{margin:0 0 20px;font-size:28px;letter-spacing:-.01em}
.cmp p,.cmp li{font-size:17px;line-height:1.55;color:var(--body)}
.cmp ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px}
.frames{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}
.frame{position:relative;height:420px;border:1px solid var(--line);border-radius:18px;background:var(--bg);overflow:hidden}
.frame .cap{position:absolute;left:18px;bottom:14px;font-size:15px;font-weight:600;color:var(--ink)}
.frame .mag-fluid{opacity:1!important;transform:none!important}
.frame .mag{top:20px}
.cursor{position:absolute;width:22px;height:22px}
.sw-row{display:flex;gap:56px;align-items:flex-end}
.sw-demo{display:flex;flex-direction:column;align-items:center;gap:14px;font-size:15px;color:var(--muted)}
.swatches{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:12px}
.swatch{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--muted)}
.swatch span:first-child{height:56px;border-radius:12px;border:1px solid var(--line)}
.icons{display:flex;gap:28px;flex-wrap:wrap}
.icons div{display:flex;flex-direction:column;align-items:center;gap:8px;font-size:14px;color:var(--muted)}
"""

CURSOR = ('<svg class="cursor" width="22" height="22" viewBox="0 0 22 22" style="left:{x}px;top:{y}px" aria-hidden="true">'
          '<path d="M3,2 L3,18 L7.5,13.5 L10.5,20 L13,19 L10,12.5 L16,12.5 Z" style="fill:#FFFFFF;stroke:#000000;stroke-width:1.4;stroke-linejoin:round"></path></svg>')


def rail_frame(state, side):
    links = "".join(f'<a href="#"{" aria-current=page" if s == "Main" else ""}>{l}</a>' for s, l, _ in PAGES)
    fluid = ""
    link_box = ""
    cursor = CURSOR.format(x=300 if side == "l" else 60, y=190)
    if state == "near":
        fluid = ferro_svg(side, strength=0.55, uid=f"c{state}")
        cursor = CURSOR.format(x=150 if side == "l" else 250, y=190)
    if state == "open":
        fluid = ferro_svg(side, strength=1.0, uid=f"c{state}")
        link_box = f'<div class="mag-links" style="opacity:1">{links}</div>'
        cursor = CURSOR.format(x=70 if side == "l" else 330, y=150)
    cap = {"idle": "Cursor far away: quiet rail, current page bead",
           "near": "Cursor approaching: fluid wells up, spikes lean toward it",
           "open": "Cursor at the rail: spikes at full length, page links shown"}[state]
    return (f'<div class="frame"><nav class="mag {side}" aria-label="Pages (demo)"><span class="mag-bar"></span>{fluid}'
            f'<span class="mag-bead" style="top:44px"></span>{link_box}</nav>{cursor}<span class="cap">{cap}</span></div>')


def switch_demo(state):
    scale = 2
    tw, th, k = 52 * scale, 32 * scale, 28 * scale
    on = state in ("on", "pressed")
    track = "#30D158" if on else "var(--track-off)"
    knob_x = (20 * scale + 2 * scale) if state == "on" else (2 * scale if state == "off" else 9 * scale)
    if state == "pressed":
        lens_w = 40 * scale
        knob = (f'<span style="position:absolute;top:-6px;left:{knob_x}px;width:{lens_w}px;height:{th + 12}px;border-radius:{(th + 12) // 2}px;'
                f'background:rgba(255,255,255,.45);box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.9),inset 0 -10px 18px rgba(255,255,255,.35),'
                f'0 10px 24px rgba(0,0,0,.25);backdrop-filter:blur(1px) saturate(1.15) brightness(1.08)"></span>'
                f'<svg width="{lens_w}" height="{th + 12}" style="position:absolute;top:-6px;left:{knob_x}px" aria-hidden="true">'
                f'<defs><linearGradient id="rb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF6B6B" stop-opacity=".55"></stop>'
                f'<stop offset=".35" stop-color="#FFD93D" stop-opacity=".45"></stop><stop offset=".65" stop-color="#6BCBFF" stop-opacity=".5"></stop>'
                f'<stop offset="1" stop-color="#C77DFF" stop-opacity=".5"></stop></linearGradient></defs>'
                f'<rect x="2" y="2" width="{lens_w - 4}" height="{th + 8}" rx="{(th + 8) // 2}" style="fill:none;stroke:url(#rb);stroke-width:2.5"></rect></svg>')
    else:
        knob = (f'<span style="position:absolute;top:{2 * scale}px;left:{knob_x}px;width:{k}px;height:{k}px;border-radius:{k // 2}px;'
                f'background:#FFFFFF;box-shadow:0 6px 14px rgba(0,0,0,.2),0 2px 2px rgba(0,0,0,.12)"></span>')
    label = {"off": "Off: light mode", "on": "On: dark mode", "pressed": "Pressed or dragged: the knob becomes a glass lens"}[state]
    return (f'<div class="sw-demo"><span style="position:relative;display:block;width:{tw}px;height:{th}px;border-radius:{th // 2}px;'
            f'background:{track}">{knob}</span><span>{label}</span></div>')


def components_body(d):
    side = d.rail_side
    icons = "".join(f'<div>{squircle(ICON_FOR[s], 64, **d.icon_style(s))}{esc(l)}</div>' for s, l, _ in PAGES)
    icons += f'<div>{squircle("slow", 64, **d.icon_style("slow"))}Slow factor</div><div>{squircle("fast", 64, **d.icon_style("fast"))}Fast factor</div>'

    def swatches(tok, title):
        keys = ["bg", "surf", "raised", "line", "ink", "body", "muted", "acc"]
        cells = "".join(f'<div class="swatch"><span style="background:{tok[k]}"></span><span>{k}  {tok[k]}</span></div>' for k in keys)
        return f'<div style="display:flex;flex-direction:column;gap:12px"><b style="font-size:17px">{title}</b><div class="swatches">{cells}</div></div>'

    body = f"""
<div class="cmp">
  <div style="display:flex;flex-direction:column;gap:14px;max-width:900px">
    <h1 style="font-family:{d.display_font}">Components</h1>
    <p>The pieces every page of {esc(d.name)} shares. Build the magnet navigation and the switch once in the shared folder, then theme them with this design's tokens.</p>
  </div>
  <section>
    <h2 style="font-family:{d.display_font}">Magnet navigation ({'left' if side == 'l' else 'right'} edge)</h2>
    <div class="frames">{rail_frame('idle', side)}{rail_frame('near', side)}{rail_frame('open', side)}</div>
    <ul style="margin-top:22px">
      <li>A slim metal rail stays quiet until the cursor is within about 140 px. The fluid then flows out and bristles into spikes that lean toward the cursor; closer means longer spikes.</li>
      <li>Moving away pulls the fluid back. The current page keeps a small bead of fluid on the rail.</li>
      <li>One canvas the size of the rail only. The animation loop starts on approach and stops completely when the fluid has settled.</li>
      <li>Keyboard focus opens it; touch screens get a tap-to-open handle; with reduced motion on, the links simply fade in.</li>
      <li>In dark mode the fluid stays black and gets glossy highlights so it stays visible.</li>
    </ul>
  </section>
  <section>
    <h2 style="font-family:{d.display_font}">Light and dark switch (top-right on every page)</h2>
    <div class="sw-row">{switch_demo('off')}{switch_demo('on')}{switch_demo('pressed')}</div>
    <ul style="margin-top:26px">
      <li>iPhone proportions (51 × 31), white knob, Apple green track when on. On means dark mode.</li>
      <li>Pressing or dragging grows the knob into a clear glass lens that refracts the track with a faint rainbow edge and squishes as it moves, then settles back on release.</li>
      <li>A real switch for screen readers: Space or Enter toggles it, with a visible focus ring. Reduced motion: it slides without the squish.</li>
      <li>First visit follows the system setting; after that the choice is remembered on every page, with no flash of the wrong theme.</li>
    </ul>
  </section>
  <section>
    <h2 style="font-family:{d.display_font}">Icons</h2>
    <div class="icons">{icons}</div>
  </section>
  <section>
    <h2 style="font-family:{d.display_font}">Type</h2>
    <div style="display:flex;flex-direction:column;gap:12px">
      <span style="font-family:{d.display_font};font-size:64px;line-height:1.05;letter-spacing:-.02em;color:var(--ink)">{esc(d.type_sample)}</span>
      <span style="font-size:18px;color:var(--body)">{esc(d.type_note)}</span>
    </div>
  </section>
  <section style="display:flex;flex-direction:column;gap:28px">
    <h2 style="font-family:{d.display_font};margin:0">Colour</h2>
    {swatches(d.light, 'Light theme')}
    {swatches(d.dark, 'Dark theme')}
    <p style="margin:0">Up and down are always green and red, tuned per theme for contrast. Candlesticks are green when the day closed higher and red when it closed lower.</p>
  </section>
</div>
"""
    return body
