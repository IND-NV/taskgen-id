"""Kategori matematika TaskGen-ID."""

CATEGORY = {
    "id": "math",
    "name": "Matematika",
    "domains": [
        {"name": "Algebra", "subdomains": ["linear_equations", "polynomials", "inequalities", "matrices", "abstract_algebra"]},
        {"name": "Calculus", "subdomains": ["derivatives", "integrals", "limits", "series", "multivariable"]},
        {"name": "Probability", "subdomains": ["bayesian", "distributions", "combinatorics", "stochastic_processes", "markov_chains"]},
        {"name": "Statistics", "subdomains": ["hypothesis_testing", "regression", "anova", "descriptive", "bayesian_stats"]},
        {"name": "Geometry", "subdomains": ["euclidean", "analytic", "differential", "topology", "trigonometry"]},
        {"name": "Number Theory", "subdomains": ["primes", "modular_arithmetic", "diophantine", "cryptographic", "algebraic_nt"]},
        {"name": "Discrete Math", "subdomains": ["graph_theory", "combinatorics", "logic", "set_theory", "recurrence"]},
        {"name": "Linear Algebra", "subdomains": ["vector_spaces", "eigenvalues", "transformations", "inner_product", "decompositions"]},
    ],
}
