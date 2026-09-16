from itertools import combinations, product
import pytest
from src.csp import CSP
from src.ac3 import ac3, ac3_search
from src.solver import ALGORITHMS, solve, minimum_coloring


def graph(n, edges, k):
    variables = [str(i) for i in range(n)]
    neighbors = {v: [] for v in variables}
    for a, b in edges:
        neighbors[str(a)].append(str(b))
        neighbors[str(b)].append(str(a))
    return CSP(variables, {v: list(range(k)) for v in variables}, neighbors)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_all_four_vertex_graphs_against_brute_force(algorithm):
    edges = list(combinations(range(4), 2))
    for mask in range(1 << len(edges)):
        selected = [e for i, e in enumerate(edges) if mask & (1 << i)]
        for k in (1, 2, 3, 4):
            expected = any(all(values[a] != values[b] for a, b in selected)
                           for values in product(range(k), repeat=4))
            csp = graph(4, selected, k)
            before = {v: d.copy() for v, d in csp.domains.items()}
            result = solve(csp, algorithm)
            assert (result.status == "solved") == expected
            if expected:
                assert csp.validate(result.solution)
            assert csp.domains == before


def test_arc_consistency_is_not_a_solution():
    csp = graph(3, [(0, 1), (1, 2), (0, 2)], 2)
    assert ac3(csp)
    assert ac3_search(csp) is None


def test_ac3_cascade_and_empty_domain():
    csp = graph(3, [(0, 1), (1, 2)], 2)
    csp.domains["0"] = [0]
    assert ac3(csp)
    assert csp.domains == {"0": [0], "1": [1], "2": [0]}
    isolated = graph(1, [], 0)
    assert not ac3(isolated)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_minimum_k4_and_timeout(algorithm):
    csp = graph(4, list(combinations(range(4), 2)), 4)
    results = minimum_coloring(csp.variables, csp.neighbors, list(range(4)), algorithm)
    assert [r.status for _, r in results] == ["unsatisfiable"] * 3 + ["solved"]
    limited = minimum_coloring(csp.variables, csp.neighbors, list(range(4)), algorithm, timeout=0)
    assert len(limited) == 1 and limited[0][1].status == "timeout"


def test_invalid_graph_rejected():
    with pytest.raises(ValueError):
        CSP(["a", "b"], {"a": [0], "b": [0]}, {"a": ["b"], "b": []})


def test_map_coverage_and_validated_optimum():
    from src.data import GEOJSON, VARIABLES, NEIGHBORS, COLORS
    assert len(VARIABLES) == len(set(VARIABLES)) == len(GEOJSON["features"]) == 34
    assert "Đồng Tháp" in VARIABLES
    assert len(NEIGHBORS["Đồng Tháp"]) == 5
    assert "Cần Thơ" in NEIGHBORS["Đồng Tháp"]
    assert "Cần Thơ" not in NEIGHBORS["Lạng Sơn"]
    csp = CSP(VARIABLES, {v: COLORS for v in VARIABLES}, NEIGHBORS)
    results = minimum_coloring(VARIABLES, NEIGHBORS, COLORS)
    assert results[-1][0] == 4
    assert csp.validate(results[-1][1].solution)
    assert all(r.status == "unsatisfiable" for _, r in results[:-1])

