from collections import deque


def revise(csp, xi, xj):
    remaining = [x for x in csp.domains[xi] if any(x != y for y in csp.domains[xj])]
    changed = remaining != csp.domains[xi]
    csp.domains[xi] = remaining
    return changed


def ac3(csp):
    """Filter domains in place. True means arc-consistent, not solved."""
    if any(not csp.domains[v] for v in csp.variables):
        return False
    queue = deque((v, n) for v in csp.variables for n in csp.neighbors[v])
    while queue:
        a, b = queue.popleft()
        if revise(csp, a, b):
            if not csp.domains[a]:
                return False
            queue.extend((n, a) for n in csp.neighbors[a] if n != b)
    return True


def ac3_search(csp):
    """Return a complete assignment using backtracking + AC-3 (MAC)."""
    from .solver import solve
    return solve(csp, "AC-3 (MAC)").solution

