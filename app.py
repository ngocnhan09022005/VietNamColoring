import json
from html import escape

import streamlit as st
from src.csp import CSP
from src.data import GEOJSON, VARIABLES, NEIGHBORS, COLORS
from src.solver import ALGORITHMS, solve, minimum_coloring
from src.interactive_map import MAP_JS, interactive_map
from src.selection import selected_graph, toggle_province

map_component = st.components.v2.component(
    "province_selection_map", html='<div id="root"></div>', js=MAP_JS,
)


def clear_results():
    st.session_state.runs = None
    st.session_state.comparison = None
    st.session_state.pop("step", None)


def reset_selection():
    st.session_state.selected_provinces = []
    clear_results()


def change_province_count():
    st.session_state.selected_provinces = (
        VARIABLES.copy() if st.session_state.province_count == len(VARIABLES) else []
    )
    clear_results()


def map_clicked():
    province = st.session_state["province_map"].get("clicked")
    previous = st.session_state.selected_provinces
    selected = toggle_province(previous, province, st.session_state.province_count, VARIABLES)
    if selected != previous:
        st.session_state.selected_provinces = selected
        clear_results()


def render_table(rows, *, height=None):
    """Render records without importing pandas/numpy through st.dataframe."""
    if not rows:
        st.caption("Không có dữ liệu.")
        return

    columns = list(rows[0])
    head = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    body = "".join(
        "<tr>" + "".join(
            f"<td>{escape(str(row.get(column, '')))}</td>" for column in columns
        ) + "</tr>"
        for row in rows
    )
    max_height = f"max-height:{height}px;overflow:auto;" if height else ""
    st.html(f"""
    <style>
      .records {{ {max_height} border: 1px solid rgba(128,128,128,.25); border-radius: .5rem; }}
      .records table {{ width: 100%; border-collapse: collapse; font-size: .875rem; }}
      .records th {{ position: sticky; top: 0; background: var(--background-color, white); z-index: 1; }}
      .records th, .records td {{ padding: .45rem .65rem; text-align: left; border-bottom: 1px solid rgba(128,128,128,.2); }}
      .records tr:last-child td {{ border-bottom: 0; }}
    </style>
    <div class="records"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>
    """)

st.set_page_config(page_title="Tô màu bản đồ Việt Nam", page_icon="🇻🇳", layout="wide")
st.title("Tô màu bản đồ Việt Nam")
st.caption("Chủ đề 11 · Bài toán thỏa mãn ràng buộc (CSP) · Bộ dữ liệu 34 tỉnh/thành trong project")
st.session_state.setdefault("runs", None)
st.session_state.setdefault("comparison", None)
st.session_state.setdefault("selected_provinces", VARIABLES.copy())

with st.sidebar:
    st.header("Thiết lập")
    algorithm = st.selectbox("Thuật toán", ALGORITHMS, index=2)
    mode = st.radio("Mục tiêu", ["Tìm số màu tối thiểu", "Thử số màu cố định"])
    k = st.slider("Số màu thử", 1, len(COLORS), 10, disabled=mode == "Tìm số màu tối thiểu")
    st.caption("Chế độ cố định dùng đủ số màu đã chọn (tối đa 10 màu). Chế độ tối thiểu tìm ít màu nhất.")
    province_count = st.number_input("Số tỉnh/thành thử", min_value=1, max_value=len(VARIABLES),
                                     value=len(VARIABLES), step=1, key="province_count",
                                     on_change=change_province_count)
    st.caption("Chọn 34 tỉnh để tự động chọn toàn bộ bản đồ.")
    selected = st.session_state.selected_provinces
    ready = len(selected) == province_count
    st.caption(f"Đã chọn {len(selected)}/{province_count} tỉnh. Bấm vào bản đồ để chọn hoặc bỏ chọn.")
    if not ready:
        st.info(f"Chọn thêm {province_count - len(selected)} tỉnh trên bản đồ để chạy.")
    too_many_colors = k > province_count
    if too_many_colors and mode == "Thử số màu cố định":
        st.warning("Để dùng đủ số màu đã chọn, số tỉnh phải ít nhất bằng số màu. Hãy giảm số màu hoặc tăng số tỉnh.")
    timeout = st.slider("Giới hạn mỗi lượt (giây)", 1, 30, 10)
    run = st.button("Chạy thuật toán", type="primary", width="stretch",
                    disabled=not ready or (too_many_colors and mode == "Thử số màu cố định"))
    compare = st.button("So sánh 3 thuật toán", width="stretch", disabled=not ready or too_many_colors)
    st.button("Bỏ chọn tất cả", on_click=reset_selection, width="stretch")
    if selected:
        st.caption("Đã chọn: " + ", ".join(selected))
    st.caption("So sánh dùng đủ số màu thử trên các tỉnh đã chọn; số màu không được vượt số tỉnh. Cùng MRV và ưu tiên bậc lớn.")
    st.info("AC-3 lọc miền giá trị. Để tìm nghiệm hoàn chỉnh, ứng dụng kết hợp AC-3 với quay lui (MAC).")

variables, neighbors = selected_graph(selected, VARIABLES, NEIGHBORS)
config = (algorithm, mode, k, timeout, tuple(variables), "balanced-colors")
if st.session_state.get("config") != config:
    st.session_state.runs = None
    st.session_state.comparison = None
    st.session_state.config = config

if run:
    with st.spinner("Đang tìm kiếm và kiểm tra ràng buộc…"):
        if mode == "Tìm số màu tối thiểu":
            runs = minimum_coloring(variables, neighbors, COLORS, algorithm, timeout=timeout)
        else:
            csp = CSP(variables, {v: COLORS[:k] for v in variables}, neighbors)
            runs = [(k, solve(csp, algorithm, timeout=timeout, require_all_colors=True))]
        st.session_state.runs = runs
        st.session_state.pop("step", None)

if compare:
    with st.spinner("Đang chạy trên cùng dữ liệu…"):
        rows = []
        for name in ALGORITHMS:
            result = solve(CSP(variables, {v: COLORS[:k] for v in variables}, neighbors),
                           name, timeout=timeout, require_all_colors=True)
            rows.append({"Thuật toán": name, "Số màu thử": k, "Trạng thái": result.status,
                         "Thời gian (ms)": round(result.seconds * 1000, 3),
                         "Lần gán": result.nodes, "Quay lui": result.backtracks,
                         "Giá trị bị loại": result.pruned, "Cung AC-3": result.arcs})
        st.session_state.comparison = rows

cols = st.columns(3)
cols[0].metric("Tỉnh / thành đã chọn", f"{len(variables)}/{province_count}")
cols[1].metric("Cặp giáp ranh trong nhóm đã chọn", sum(map(len, neighbors.values())) // 2)
cols[2].metric("Ràng buộc", "Hai tỉnh giáp nhau khác màu")

map_tab, detail_tab, theory_tab = st.tabs(["Bản đồ & từng bước", "Dữ liệu & so sánh", "Thuật toán & hướng dẫn"])
with map_tab:
    coloring, active = {}, None
    runs = st.session_state.runs
    if runs:
        last_k, result = runs[-1]
        if result.status == "solved":
            if mode == "Tìm số màu tối thiểu":
                st.success(f"Số màu tối thiểu của {len(variables)} tỉnh đã chọn: {last_k}. Đã loại trừ tất cả số màu nhỏ hơn.")
            else:
                st.success(f"Nghiệm hợp lệ, đã dùng đủ {last_k} màu đã chọn.")
            st.caption("Đã kiểm tra đủ các tỉnh đã chọn, màu thuộc miền và mọi cặp giáp ranh trong nhóm khác màu.")
            coloring = result.solution
            st.download_button("Tải kết quả JSON", json.dumps({
                "algorithm": algorithm, "mode": mode, "colors_allowed": last_k,
                "minimum_proven": mode == "Tìm số màu tối thiểu",
                "require_all_colors": mode == "Thử số màu cố định",
                "dataset": "assets/vietnam_provinces.geojson (corrected names)",
                "selected_provinces": variables,
                "solution": coloring, "neighbors": neighbors
            }, ensure_ascii=False, indent=2), "coloring.json", "application/json")
        elif result.status == "timeout":
            st.warning("Đã hết thời gian. Chưa thể kết luận vô nghiệm hoặc số màu tối thiểu.")
        else:
            st.error(f"Không có nghiệm trong phạm vi màu đã thử (đến {last_k} màu).")
        render_table([{"Số màu": count, "Trạng thái": r.status, "Lần gán": r.nodes,
                       "Quay lui": r.backtracks, "Loại giá trị": r.pruned,
                       "Cung AC-3": r.arcs, "Thời gian (ms)": round(r.seconds*1000, 3)}
                      for count, r in runs])
        replay = st.checkbox("Xem từng bước thuật toán")
        if replay:
            attempt = st.selectbox("Lượt tìm kiếm", range(len(runs)),
                                   format_func=lambda i: f"{runs[i][0]} màu", index=len(runs)-1)
            traced = runs[attempt][1]
            if traced.trace_truncated:
                st.warning("Chỉ lưu 1.500 sự kiện đầu; bộ giải vẫn tiếp tục chạy đến khi kết thúc.")
            step = st.slider("Bước", 0, max(1, len(traced.trace)-1), 0, key="step")
            event = traced.trace[min(step, len(traced.trace)-1)]
            coloring, active = event["assignment"], event["variable"]
            st.write(f"**{event['event']}** · {active or 'Toàn bộ đồ thị'}")
            render_table([{"Tỉnh": v, "Màu đã gán": coloring.get(v, "—"),
                           "Miền đang lưu": ", ".join(event["domains"][v]) or "∅"}
                          for v in variables], height=230)
    else:
        st.info("Chọn đủ số tỉnh bằng cách bấm bản đồ, rồi nhấn Chạy thuật toán. Bấm lại một tỉnh để bỏ chọn.")
    st.caption("Tỉnh đã chọn có viền xanh đậm; tỉnh ngoài nhóm hiển thị mờ và không tham gia bài toán.")
    interactive_map(map_component, GEOJSON, coloring, NEIGHBORS, active, selected, province_count, map_clicked)
    with st.container(border=True):
        st.markdown("#### Giải thích bản đồ")
        st.markdown("""
- Mỗi vùng trên bản đồ đại diện cho một **tỉnh hoặc thành phố** trong bộ dữ liệu.
- Bảng màu gồm **đỏ, xanh lá, xanh dương, vàng, tím, cam, hồng, xanh ngọc, nâu và ô liu**; hai tỉnh có chung đường biên phải mang màu khác nhau.
- Vùng **màu xám** là tỉnh chưa được gán màu. Khi xem từng bước, tỉnh đang được xử lý có **đường viền đậm**.
- Chọn số tỉnh ở thanh bên rồi bấm vào bản đồ để chọn đúng số lượng. Chỉ các tỉnh đã chọn và các cạnh giáp ranh giữa chúng tham gia thuật toán; tỉnh ngoài nhóm được làm mờ.
- Rê chuột lên một tỉnh để xem tên, màu đã gán và danh sách các tỉnh giáp ranh. Có thể dùng các nút **+**, **−**, **Toàn bản đồ** hoặc kéo bản đồ để quan sát.

Kết quả tô màu phản ánh quan hệ giáp ranh được trích từ tệp GeoJSON của project, không thể hiện vùng miền, dân số hoặc đơn vị hành chính theo màu.
""")

with detail_tab:
    st.subheader("Đồ thị ràng buộc của nhóm đã chọn")
    st.caption("Hai vùng có chung đoạn biên trong GeoJSON được coi là giáp ranh; tiếp xúc tại một điểm không tạo cạnh.")
    province = st.selectbox("Tra cứu tỉnh / thành", sorted(variables))
    if province:
        st.write(", ".join(neighbors[province]) or "Không có hàng xóm trong nhóm đã chọn.")
    render_table([{"Tỉnh / thành": v, "Bậc": len(neighbors[v]),
                   "Giáp ranh": ", ".join(neighbors[v])} for v in variables])
    st.download_button("Tải danh sách giáp ranh", json.dumps(neighbors, ensure_ascii=False, indent=2),
                       "neighbors.json", "application/json")
    st.warning("Nguồn có vùng mã 31 ở miền Tây bị ghi nhầm Lạng Sơn. Ứng dụng hiệu chỉnh tên thành Đồng Tháp khi đọc; giữ nguyên tệp gốc. Quan hệ giáp ranh là kết quả hình học, chưa phải danh mục địa giới đã được thẩm định.")
    if st.session_state.comparison:
        st.subheader("So sánh cùng số màu")
        render_table(st.session_state.comparison)
        st.caption("solved: có nghiệm · unsatisfiable: đã duyệt và không có nghiệm · timeout: chưa kết luận.")

with theory_tab:
    st.subheader("Mô hình CSP")
    st.markdown("""
- **Biến:** mỗi tỉnh/thành là một biến.
- **Miền:** danh sách màu cho phép.
- **Ràng buộc:** với mọi cạnh (A, B), màu(A) ≠ màu(B).
- **Mục tiêu:** thử k = 1, 2, …; k đầu tiên có nghiệm là tối thiểu nếu mọi lượt trước đã chứng minh vô nghiệm.

### Ba phương pháp
1. **Backtracking:** gán màu phù hợp; nếu không thể đi tiếp thì quay lui.
2. **Forward Checking:** sau khi gán màu, xóa màu đó khỏi miền các hàng xóm chưa gán. Miền rỗng khiến nhánh bị loại ngay.
3. **AC-3 (MAC):** với mỗi cung A → B, xóa màu của A nếu không có màu khác trong miền B hỗ trợ; khi miền A đổi, đưa các cung liên quan vào hàng đợi. Lặp lại sau mỗi lần gán.

Cả ba dùng **MRV** (chọn tỉnh có ít màu hợp lệ nhất), hòa thì chọn tỉnh có nhiều hàng xóm chưa gán nhất. Khi gán, ưu tiên màu hợp lệ đang được dùng ít nhất để phân bố màu đều hơn; không bảo đảm số tỉnh mỗi màu bằng nhau. Miền được sao chép theo nhánh để khôi phục chính xác khi quay lui.

**Vì sao AC-3 đơn lẻ chưa đủ?** Tam giác có miền {đỏ, xanh} ở cả ba đỉnh vẫn nhất quán cung, nhưng không thể tô bằng hai màu. Vì vậy không được lấy tùy ý màu đầu tiên sau AC-3.

### Gợi ý trình bày
Chạy tìm tối thiểu → xem một lượt vô nghiệm → xem sự kiện xóa miền và quay lui → so sánh ba thuật toán ở cùng số màu → tải nghiệm và danh sách cạnh.

### Giới hạn
Kết quả tối ưu áp dụng cho đồ thị trích từ tệp của project. Sai số hoặc thiếu đường biên trong dữ liệu có thể làm thay đổi đồ thị. Tọa độ được giản lược chỉ khi hiển thị. Bộ giải dừng theo giới hạn thời gian và không coi timeout là vô nghiệm.
""")

