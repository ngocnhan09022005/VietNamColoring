"""Selection rules shared by the map and the solver inputs."""


def toggle_province(selected, province, limit, variables):
    selected = list(dict.fromkeys(v for v in selected if v in variables))
    if province in selected:
        selected.remove(province)
    elif province in variables and len(selected) < limit:
        selected.append(province)
    return selected


def selected_graph(selected, variables, neighbors):
    chosen = set(selected)
    vertices = [v for v in variables if v in chosen]
    return vertices, {v: [n for n in neighbors[v] if n in chosen] for v in vertices}
