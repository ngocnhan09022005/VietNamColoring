"""Offline SVG map: no tiles, CDN, API key or network needed."""
from html import escape
from .data import COLOR_HEX


def map_html(geojson, coloring, neighbors, active=None):
    paths = []
    for feature in geojson["features"]:
        name = feature["properties"]["TinhThanh"]
        geom = feature["geometry"]
        polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        commands = []
        for polygon in polygons:
            for ring in polygon:
                commands.append("M" + " L".join(f"{(x-102)*70:.2f},{(24-y)*75:.2f}" for x, y, *_ in ring) + " Z")
        color = COLOR_HEX.get(coloring.get(name), "#e2e8f0")
        title = escape(f"{name} | {coloring.get(name, 'Chưa gán')} | Giáp: {', '.join(neighbors[name])}")
        stroke = "#111827" if name == active else "#64748b"
        weight = 2.5 if name == active else 0.65
        paths.append(f'<path data-province="{escape(name, quote=True)}" aria-label="{escape(name, quote=True)}" d="{" ".join(commands)}" fill="{color}" stroke="{stroke}" stroke-width="{weight}" fill-rule="evenodd" tabindex="0"><title>{title}</title></path>')
    legend = "".join(f'<span><i style="background:{h}"></i>{c}</span>' for c, h in COLOR_HEX.items() if c in coloring.values())
    return """<!doctype html><html lang="vi"><meta charset="utf-8">
<style>
body{margin:0;font:14px system-ui;color:#24324b;background:#f8fafc}
header{display:flex;gap:8px;align-items:center;padding:10px;flex-wrap:wrap}
button{padding:6px 14px;background:white;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer}
svg{width:100%;height:560px;display:block}path:hover,path:focus{stroke:#0f172a;stroke-width:2.5;filter:brightness(.94)}
footer{display:flex;gap:16px;padding:10px;flex-wrap:wrap}i{display:inline-block;width:13px;height:13px;margin-right:5px;border-radius:3px}
</style><header><button onclick="zoom(.75)" aria-label="Phóng to">+</button>
<button onclick="zoom(1.333333)" aria-label="Thu nhỏ">−</button>
<button onclick="reset()">Toàn bản đồ</button><span>Rê chuột vào tỉnh để xem màu và các tỉnh giáp ranh. Kéo để di chuyển.</span></header>
<svg id="map" viewBox="-15 0 1150 1250" role="img" aria-label="Bản đồ tô màu các tỉnh Việt Nam">
""" + "".join(paths) + """</svg><footer>""" + legend + """<span><i style="background:#e2e8f0"></i>Chưa gán</span></footer>
<script>
const svg=document.getElementById('map');let box=[-15,0,1150,1250],drag=null;
function draw(){svg.setAttribute('viewBox',box.join(' '))}
function reset(){box=[-15,0,1150,1250];draw()}
function zoom(f){if(box[2]*f<60||box[2]*f>4000)return;box[0]+=box[2]*(1-f)/2;box[1]+=box[3]*(1-f)/2;box[2]*=f;box[3]*=f;draw()}
svg.style.touchAction='none';
svg.onpointerdown=e=>{drag=[e.clientX,e.clientY,...box];svg.setPointerCapture(e.pointerId)};
svg.onpointermove=e=>{if(!drag)return;const scale=Math.max(box[2]/svg.clientWidth,box[3]/svg.clientHeight);box[0]=drag[2]-(e.clientX-drag[0])*scale;box[1]=drag[3]-(e.clientY-drag[1])*scale;draw()};
svg.onpointerup=svg.onpointercancel=()=>drag=null;
</script></html>"""

