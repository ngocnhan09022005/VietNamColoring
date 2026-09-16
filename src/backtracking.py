def backtracking_search(csp):
    from .solver import solve
    return solve(csp, "Backtracking").solution

