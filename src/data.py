"""Derive adjacency from the same unsimplified geometry used for the map."""
import json
from functools import lru_cache
from pathlib import Path
from shapely.geometry import shape, mapping

COLORS = ["Red", "Green", "Blue", "Yellow", "Purple"]
COLOR_HEX = dict(zip(COLORS, ["#ef6461", "#43aa8b", "#4d8fdf", "#f6ce60", "#a879d8"]))
DATA_PATH = Path(__file__).resolve().parents[1] / "assets" / "vietnam_provinces.geojson"


@lru_cache(maxsize=1)
def load_map():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    geometries, names = [], []
    for feature in data["features"]:
        props = feature["properties"]
        geom = shape(feature["geometry"])
        # Source Ma=31 copied Lang Son metadata onto southern Dong Thap geometry.
        # Guard on source ID and location. Keep the original asset untouched.
        if str(props.get("Ma")) == "31" and props["TinhThanh"] == "Lạng Sơn" and geom.bounds[3] < 12:
            feature["properties"] = {"Ma": "31", "TinhThanh": "Đồng Tháp",
                                     "data_note": "Hiệu chỉnh tên bị trùng Lạng Sơn trong nguồn"}
        name = feature["properties"]["TinhThanh"]
        if name in names or not geom.is_valid or geom.is_empty:
            raise ValueError(f"Invalid or duplicate province: {name}")
        names.append(name)
        geometries.append(geom)
    neighbors = {n: [] for n in names}
    for i, a in enumerate(geometries):
        for j in range(i):
            b = geometries[j]
            # A shared line is a border; a shared point alone is not.
            if a.intersects(b) and a.boundary.intersection(b.boundary).length > 1e-8:
                neighbors[names[i]].append(names[j])
                neighbors[names[j]].append(names[i])
    for feature, geom in zip(data["features"], geometries):
        # Simplify display only, never the constraint graph.
        feature["geometry"] = mapping(geom.simplify(0.003, preserve_topology=True))
    return data, names, neighbors


GEOJSON, VARIABLES, NEIGHBORS = load_map()
DOMAINS = {v: COLORS.copy() for v in VARIABLES}

