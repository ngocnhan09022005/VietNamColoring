import json
from html import escape

import streamlit as st
from src.csp import CSP
from src.data import GEOJSON, VARIABLES, NEIGHBORS, COLORS
from src.solver import ALGORITHMS, solve, minimum_coloring
from src.visualization import map_html


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

with st.sidebar:
    st.header("Thiết lập")
    algorithm = st.selectbox("Thuật toán", ALGORITHMS, index=2)
    mode = st.radio("Mục tiêu", ["Tìm số màu tối thiểu", "Thử số màu cố định"])
    k = st.slider("Số màu thử", 1, 5, 4, disabled=mode == "Tìm số màu tối thiểu")
    timeout = st.slider("Giới hạn mỗi lượt (giây)", 1, 30, 10)
    run = st.button("Chạy thuật toán", type="primary", width="stretch")
    compare = st.button("So sánh 3 thuật toán", width="stretch")
    st.caption("So sánh dùng số màu thử; cùng MRV và ưu tiên bậc lớn. Thời gian có tính ghi nhật ký.")
    st.info("AC-3 lọc miền giá trị. Để tìm nghiệm hoàn chỉnh, ứng dụng kết hợp AC-3 với quay lui (MAC).")

config = (algorithm, mode, k, timeout)
if st.session_state.get("config") != config:
    st.session_state.runs = None
    st.session_state.comparison = None
    st.session_state.config = config

if run:
    with st.spinner("Đang tìm kiếm và kiểm tra ràng buộc…"):
        if mode == "Tìm số màu tối thiểu":
            runs = minimum_coloring(VARIABLES, NEIGHBORS, COLORS, algorithm, timeout=timeout)
        else:
            csp = CSP(VARIABLES, {v: COLORS[:k] for v in VARIABLES}, NEIGHBORS)
            runs = [(k, solve(csp, algorithm, timeout=timeout))]
        st.session_state.runs = runs
        st.session_state.pop("step", None)

if compare:
    with st.spinner("Đang chạy trên cùng dữ liệu…"):
        rows = []
        for name in ALGORITHMS:
            result = solve(CSP(VARIABLES, {v: COLORS[:k] for v in VARIABLES}, NEIGHBORS),
                           name, timeout=timeout)
            rows.append({"Thuật toán": name, "Số màu thử": k, "Trạng thái": result.status,
                         "Thời gian (ms)": round(result.seconds * 1000, 3),
                         "Lần gán": result.nodes, "Quay lui": result.backtracks,
                         "Giá trị bị loại": result.pruned, "Cung AC-3": result.arcs})
        st.session_state.comparison = rows

cols = st.columns(3)
cols[0].metric("Tỉnh / thành", len(VARIABLES))
cols[1].metric("Cặp giáp ranh trong GeoJSON", sum(map(len, NEIGHBORS.values())) // 2)
cols[2].metric("Ràng buộc", "Hai tỉnh giáp nhau khác màu")

map_tab, detail_tab, theory_tab = st.tabs(["Bản đồ & từng bước", "Dữ liệu & so sánh", "Thuật toán & hướng dẫn"])
with map_tab:
    coloring, active = {}, None
    runs = st.session_state.runs
    if runs:
        last_k, result = runs[-1]
        if result.status == "solved":
            if mode == "Tìm số màu tối thiểu":
                st.success(f"Số màu tối thiểu của đồ thị dữ liệu: {last_k}. Đã loại trừ tất cả số màu nhỏ hơn.")
            else:
                st.success(f"Nghiệm hợp lệ với {len(set(result.solution.values()))} màu được dùng trong {last_k} màu cho phép.")
            st.caption("Đã kiểm tra đủ tỉnh, màu thuộc miền và mọi cặp giáp ranh khác màu.")
            coloring = result.solution
            st.download_button("Tải kết quả JSON", json.dumps({
                "algorithm": algorithm, "mode": mode, "colors_allowed": last_k,
                "minimum_proven": mode == "Tìm số màu tối thiểu",
                "dataset": "assets/vietnam_provinces.geojson (corrected names)",
                "solution": coloring, "neighbors": NEIGHBORS
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
                          for v in VARIABLES], height=230)
    else:
        st.info("Chọn thuật toán rồi nhấn Chạy. Bản đồ ban đầu chưa gán màu.")
    st.iframe(map_html(GEOJSON, coloring, NEIGHBORS, active), height=680)
    with st.container(border=True):
        st.markdown("#### Giải thích bản đồ")
        st.markdown("""
- Mỗi vùng trên bản đồ đại diện cho một **tỉnh hoặc thành phố** trong bộ dữ liệu.
- Các màu **đỏ, xanh lá, xanh dương, vàng và tím** là màu do thuật toán CSP gán; hai tỉnh có chung đường biên phải mang màu khác nhau.
- Vùng **màu xám** là tỉnh chưa được gán màu. Khi xem từng bước, tỉnh đang được xử lý có **đường viền đậm**.
- Rê chuột lên một tỉnh để xem tên, màu đã gán và danh sách các tỉnh giáp ranh. Có thể dùng các nút **+**, **−**, **Toàn bản đồ** hoặc kéo bản đồ để quan sát.

Kết quả tô màu phản ánh quan hệ giáp ranh được trích từ tệp GeoJSON của project, không thể hiện vùng miền, dân số hoặc đơn vị hành chính theo màu.
""")

with detail_tab:
    st.subheader("Đồ thị ràng buộc")
    st.caption("Hai vùng có chung đoạn biên trong GeoJSON được coi là giáp ranh; tiếp xúc tại một điểm không tạo cạnh.")
    province = st.selectbox("Tra cứu tỉnh / thành", sorted(VARIABLES))
    st.write(", ".join(NEIGHBORS[province]) or "Không có hàng xóm trong dữ liệu.")
    render_table([{"Tỉnh / thành": v, "Bậc": len(NEIGHBORS[v]),
                   "Giáp ranh": ", ".join(NEIGHBORS[v])} for v in VARIABLES])
    st.download_button("Tải danh sách giáp ranh", json.dumps(NEIGHBORS, ensure_ascii=False, indent=2),
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

Cả ba dùng **MRV** (chọn tỉnh có ít màu hợp lệ nhất), hòa thì chọn tỉnh có nhiều hàng xóm chưa gán nhất. Miền được sao chép theo nhánh để khôi phục chính xác khi quay lui.

**Vì sao AC-3 đơn lẻ chưa đủ?** Tam giác có miền {đỏ, xanh} ở cả ba đỉnh vẫn nhất quán cung, nhưng không thể tô bằng hai màu. Vì vậy không được lấy tùy ý màu đầu tiên sau AC-3.

### Gợi ý trình bày
Chạy tìm tối thiểu → xem một lượt vô nghiệm → xem sự kiện xóa miền và quay lui → so sánh ba thuật toán ở cùng số màu → tải nghiệm và danh sách cạnh.

### Giới hạn
Kết quả tối ưu áp dụng cho đồ thị trích từ tệp của project. Sai số hoặc thiếu đường biên trong dữ liệu có thể làm thay đổi đồ thị. Tọa độ được giản lược chỉ khi hiển thị. Bộ giải dừng theo giới hạn thời gian và không coi timeout là vô nghiệm.
""")

