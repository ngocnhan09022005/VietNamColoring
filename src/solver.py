"""Complete search: backtracking, forward checking, or AC-3/MAC."""
from collections import Counter, deque
from dataclasses import dataclass, field
from time import perf_counter
from .csp import CSP

ALGORITHMS = ["Backtracking", "Forward Checking", "AC-3 (MAC)"]


@dataclass
class Result:
    solution: dict | None = None
    status: str = "unsatisfiable"
    nodes: int = 0
    backtracks: int = 0
    pruned: int = 0
    arcs: int = 0
    seconds: float = 0
    trace: list = field(default_factory=list)
    trace_truncated: bool = False


def solve(csp, algorithm="AC-3 (MAC)", *, timeout=10, trace_limit=1500,
          require_all_colors=False):
    if algorithm not in ALGORITHMS:
        raise ValueError("Unknown algorithm")
    result = Result()
    start = perf_counter()
    assignment = {}
    required_colors = {c for domain in csp.domains.values() for c in domain} if require_all_colors else set()

    def check_time():
        if perf_counter() - start >= timeout:
            raise TimeoutError

    def record(event, variable, domains):
        if len(result.trace) < trace_limit:
            result.trace.append(dict(event=event, variable=variable,
                                     assignment=assignment.copy(),
                                     domains={v: list(d) for v, d in domains.items()}))
        else:
            result.trace_truncated = True
    def propagate(domains, queue):
        while queue:
            check_time()
            a, b = queue.popleft()
            result.arcs += 1
            remaining = [x for x in domains[a] if any(x != y for y in domains[b])]
            if len(remaining) != len(domains[a]):
                result.pruned += len(domains[a]) - len(remaining)
                domains[a] = remaining
                record("AC-3: thu hẹp miền", a, domains)
                if not remaining:
                    return False
                queue.extend((n, a) for n in csp.neighbors[a] if n != b)
        return True


    def search(domains):
        check_time()
        missing = required_colors - set(assignment.values())
        if len(missing) > len(csp.variables) - len(assignment):
            return None
        if len(assignment) == len(csp.variables):
            return assignment.copy()
        # Same MRV + degree ordering for a fair comparison.
        legal = {v: [x for x in domains[v] if csp.is_consistent(v, x, assignment)]
                 for v in csp.variables if v not in assignment}
        v = min(legal, key=lambda n: (len(legal[n]),
                -sum(x not in assignment for x in csp.neighbors[n]), n))
        # Spread colors across provinces while retaining every legal branch.
        # Unused colors naturally come first, including in exact-color mode.
        usage = Counter(assignment.values())
        choices = sorted(legal[v], key=lambda color: usage[color])
        for color in choices:
            result.nodes += 1
            assignment[v] = color
            child = {n: list(d) for n, d in domains.items()}
            child[v] = [color]
            record("Gán màu", v, child)
            ok = True
            if algorithm == "Forward Checking":
                for n in csp.neighbors[v]:
                    if n not in assignment and color in child[n]:
                        child[n].remove(color)
                        result.pruned += 1
                        record("FC: loại màu ở hàng xóm", n, child)
                        if not child[n]:
                            ok = False
                            break
            elif algorithm == "AC-3 (MAC)":
                ok = propagate(child, deque((n, v) for n in csp.neighbors[v]))
            if ok:
                answer = search(child)
                if answer is not None:
                    return answer
            del assignment[v]
            result.backtracks += 1
            record("Quay lui: khôi phục miền", v, domains)
        return None

    domains = {v: list(d) for v, d in csp.domains.items()}
    record("Khởi tạo", None, domains)
    try:
        ok = all(domains.values())
        if ok and algorithm == "AC-3 (MAC)":
            ok = propagate(domains, deque((v, n) for v in csp.variables for n in csp.neighbors[v]))
        if ok:
            result.solution = search(domains)
        if result.solution is not None:
            if (not csp.validate(result.solution)
                    or not required_colors.issubset(result.solution.values())):
                raise RuntimeError("Invalid coloring returned")
            result.status = "solved"
    except TimeoutError:
        result.status = "timeout"
    result.seconds = perf_counter() - start
    return result


def minimum_coloring(variables, neighbors, colors, algorithm="AC-3 (MAC)", **kwargs):
    """Ascending exhaustive k searches. Timeout never proves optimality."""
    attempts = []
    for k in range(1, len(colors) + 1):
        csp = CSP(variables, {v: colors[:k] for v in variables}, neighbors)
        result = solve(csp, algorithm, **kwargs)
        attempts.append((k, result))
        if result.status != "unsatisfiable":
            break
    return attempts

