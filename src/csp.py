class CSP:
    """Graph coloring CSP with copied domains and undirected edges."""
    def __init__(self, variables, domains, neighbors):
        self.variables = list(variables)
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("Duplicate variables")
        if set(domains) != set(self.variables) or set(neighbors) != set(self.variables):
            raise ValueError("Variables, domains and neighbors must match")
        self.domains = {v: list(domains[v]) for v in self.variables}
        self.neighbors = {v: list(neighbors[v]) for v in self.variables}
        for v in self.variables:
            for n in self.neighbors[v]:
                if n == v or n not in self.neighbors or v not in self.neighbors[n]:
                    raise ValueError("Edges must be symmetric without self loops")

    def is_consistent(self, variable, value, assignment):
        return all(assignment.get(n) != value for n in self.neighbors[variable])

    def validate(self, assignment):
        return (assignment is not None and set(assignment) == set(self.variables)
                and all(assignment[v] in self.domains[v]
                        and self.is_consistent(v, assignment[v], assignment)
                        for v in self.variables))

