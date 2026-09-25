"""Clickable SVG map using Streamlit's bidirectional component API."""
from .visualization import map_html


MAP_JS = """
const views = new WeakMap();
export default function(component) {
  const {parentElement, data, setTriggerValue} = component;
  const root = parentElement.querySelector('#root');
  root.innerHTML = data.markup;
  const svg = root.querySelector('svg');
  let box = views.get(parentElement) || [-15, 0, 1150, 1250];
  const draw = () => {
    svg.setAttribute('viewBox', box.join(' '));
    views.set(parentElement, box);
  };
  draw();
  const buttons = root.querySelectorAll('header button');
  buttons.forEach(b => b.removeAttribute('onclick'));
  function zoom(f) {
    if (box[2]*f < 60 || box[2]*f > 4000) return;
    box = [box[0]+box[2]*(1-f)/2, box[1]+box[3]*(1-f)/2, box[2]*f, box[3]*f];
    draw();
  }
  buttons[0].onclick = () => zoom(.75);
  buttons[1].onclick = () => zoom(1.333333);
  buttons[2].onclick = () => {box = [-15,0,1150,1250]; draw();};
  const hint = root.querySelector('header span');
  hint.setAttribute('role', 'status');
  hint.textContent = `Đã chọn ${data.selected.length}/${data.limit} tỉnh. Bấm để chọn/bỏ chọn; kéo để di chuyển.`;
  const chosen = new Set(data.selected);
  function select(name) {
    if (!chosen.has(name) && chosen.size >= data.limit) {
      hint.textContent = 'Đã đủ số tỉnh. Bỏ chọn một tỉnh trước khi chọn tỉnh khác.';
      return;
    }
    setTriggerValue('clicked', name);
  }
  svg.querySelectorAll('path').forEach(path => {
    const name = path.dataset.province;
    const selected = chosen.has(name);
    path.style.opacity = selected ? '1' : '.3';
    path.style.cursor = 'pointer';
    path.setAttribute('role', 'button');
    path.setAttribute('aria-pressed', String(selected));
    if (selected && name !== data.active) {
      path.setAttribute('stroke', '#0f766e');
      path.setAttribute('stroke-width', '1.8');
    }
    path.onkeydown = e => {
      if (e.key === 'Enter' || e.key === ' ') {e.preventDefault(); select(name);}
    };
  });
  let drag = null;
  svg.style.touchAction = 'none';
  svg.onpointerdown = e => {
    if (e.button !== 0) return;
    drag = {x:e.clientX, y:e.clientY, box:[...box], name:e.target.closest('path')?.dataset.province, moved:false};
    svg.setPointerCapture(e.pointerId);
  };
  svg.onpointermove = e => {
    if (!drag) return;
    const dx = e.clientX-drag.x, dy = e.clientY-drag.y;
    if (Math.hypot(dx,dy) > 5) drag.moved = true;
    if (!drag.moved) return;
    const scale = Math.max(drag.box[2]/svg.clientWidth, drag.box[3]/svg.clientHeight);
    box = [drag.box[0]-dx*scale, drag.box[1]-dy*scale, drag.box[2], drag.box[3]];
    draw();
  };
  svg.onpointerup = e => {
    const previous = drag; drag = null;
    if (svg.hasPointerCapture(e.pointerId)) svg.releasePointerCapture(e.pointerId);
    if (previous && !previous.moved && previous.name) select(previous.name);
  };
  svg.onpointercancel = () => {drag = null;};
}
"""


def interactive_map(renderer, geojson, coloring, neighbors, active, selected, limit, on_click):
    document = map_html(geojson, coloring, neighbors, active)
    markup = document[document.index('<style>'):document.index('<script>')]
    markup = markup.replace('body{', ':host{')
    return renderer(
        key="province_map",
        data={"markup": markup, "selected": selected, "limit": limit, "active": active},
        on_clicked_change=on_click,
        height=680,
    )
