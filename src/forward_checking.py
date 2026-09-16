def forward_checking_search(csp):
    from .solver import solve
    return solve(csp, "Forward Checking").solution

