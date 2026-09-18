"""Auto-generate a large bank of answer-checkable practice problems per module.

Each generated problem is a randomized instance of a template themed to its module,
with a deterministically computed numeric answer (so solutions can be auto-verified)
and a short worked editorial. Templates are spread across a module's chapters and
across easy/medium/hard difficulty tiers.
"""
import random

# ---- number helpers -------------------------------------------------------
def _rng_for(diff, R):
    return {"easy": (1, 12), "medium": (5, 30), "hard": (12, 80)}[diff]


def T_add(diff, R):
    lo, hi = _rng_for(diff, R); a, b = R.randint(lo, hi), R.randint(lo, hi)
    return (f"Evaluate {a} + {b}", f"Compute the sum {a} + {b}.", str(a + b),
            f"{a} + {b} = {a + b}.")

def T_sub(diff, R):
    lo, hi = _rng_for(diff, R); a, b = R.randint(lo, hi), R.randint(lo, hi)
    if b > a: a, b = b, a
    return (f"Evaluate {a} − {b}", f"Compute {a} − {b}.", str(a - b), f"{a} − {b} = {a - b}.")

def T_mul(diff, R):
    lo, hi = _rng_for(diff, R); a, b = R.randint(lo, hi), R.randint(2, max(3, hi // 3))
    return (f"Evaluate {a} × {b}", f"Compute the product {a} × {b}.", str(a * b),
            f"{a} × {b} = {a * b}.")

def T_divexact(diff, R):
    lo, hi = _rng_for(diff, R); b = R.randint(2, 12); q = R.randint(lo, hi); a = b * q
    return (f"Evaluate {a} ÷ {b}", f"Compute {a} ÷ {b} (it divides evenly).", str(q),
            f"{a} ÷ {b} = {q}.")

def T_percent(diff, R):
    p = R.choice([10, 20, 25, 50, 5, 40]); base = R.randint(2, 40) * 10
    return (f"{p}% of {base}", f"What is {p}% of {base}?", str(p * base // 100),
            f"{p}% of {base} = {p}/100 × {base} = {p * base // 100}.")

def T_avg(diff, R):
    n = 2 if diff == "easy" else 3
    xs = [R.randint(2, 40) * (1 if diff != "hard" else 2) for _ in range(n)]
    while sum(xs) % n: xs[0] += 1
    return (f"Mean of {', '.join(map(str, xs))}", f"Find the mean of {', '.join(map(str, xs))}.",
            str(sum(xs) // n), f"Mean = ({' + '.join(map(str, xs))}) / {n} = {sum(xs) // n}.")

def T_linear_solve(diff, R):
    a = R.randint(2, 9); x = R.randint(1, 12); b = R.randint(1, 20); c = a * x + b
    return (f"Solve {a}x + {b} = {c}", f"Solve for x:  {a}x + {b} = {c}.", str(x),
            f"{a}x = {c} − {b} = {c - b}; x = {c - b}/{a} = {x}.")

def T_eval_poly(diff, R):
    a = R.randint(1, 6); b = R.randint(1, 9); x = R.randint(1, 6 if diff != "hard" else 10)
    val = a * x * x + b * x
    return (f"Evaluate {a}x²+{b}x at x={x}", f"Evaluate f(x) = {a}x² + {b}x at x = {x}.",
            str(val), f"f({x}) = {a}·{x}² + {b}·{x} = {a * x * x} + {b * x} = {val}.")

def T_derivative(diff, R):
    a = R.randint(1, 8); b = R.randint(1, 9); x = R.randint(1, 8)
    # d/dx(ax^2+bx)=2ax+b
    val = 2 * a * x + b
    return (f"f'(x) for {a}x²+{b}x at x={x}",
            f"For f(x) = {a}x² + {b}x, compute f'(x) at x = {x}.", str(val),
            f"f'(x) = {2 * a}x + {b}; at x={x}: {2 * a}·{x} + {b} = {val}.")

def T_gd_step(diff, R):
    x = R.randint(2, 10); lr = R.choice([0.1, 0.2, 0.5])
    # f=x^2, grad=2x, x' = x - lr*2x
    nx = round(x - lr * 2 * x, 2)
    return (f"Gradient-descent step from x={x}",
            f"Minimise f(x)=x². From x={x} with learning rate η={lr}, give x after one step.",
            str(nx), f"grad = 2x = {2 * x}; x ← {x} − {lr}·{2 * x} = {nx}.")

def T_quad_min(diff, R):
    h = R.randint(1, 9); k = R.randint(0, 9)
    return (f"Minimum x of (x−{h})²+{k}", f"At what x is f(x) = (x − {h})² + {k} minimised?",
            str(h), f"A square is smallest at 0: x − {h} = 0 → x = {h}.")

def T_dot2(diff, R):
    lo, hi = _rng_for(diff, R)
    a, b, c, d = (R.randint(1, hi) for _ in range(4))
    return (f"Dot product ({a},{b})·({c},{d})",
            f"Compute the dot product ({a}, {b}) · ({c}, {d}).", str(a * c + b * d),
            f"= {a}·{c} + {b}·{d} = {a * c} + {b * d} = {a * c + b * d}.")

def T_norm2(diff, R):
    pairs = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15)]
    a, b, n = R.choice(pairs)
    return (f"Norm of ({a},{b})", f"Compute the Euclidean norm ‖({a}, {b})‖.", str(n),
            f"√({a}² + {b}²) = √{a * a + b * b} = {n}.")

def T_det2(diff, R):
    lo, hi = _rng_for(diff, R)
    a, b, c, d = (R.randint(1, hi) for _ in range(4))
    return (f"det [[{a},{b}],[{c},{d}]]", f"Compute det([[{a}, {b}], [{c}, {d}]]).",
            str(a * d - b * c), f"det = ad − bc = {a}·{d} − {b}·{c} = {a * d - b * c}.")

def T_trace2(diff, R):
    lo, hi = _rng_for(diff, R)
    a, d = R.randint(1, hi), R.randint(1, hi)
    b, c = R.randint(1, hi), R.randint(1, hi)
    return (f"trace [[{a},{b}],[{c},{d}]]", f"Compute the trace of [[{a}, {b}], [{c}, {d}]].",
            str(a + d), f"trace = sum of diagonal = {a} + {d} = {a + d}.")

def T_prob_fraction(diff, R):
    total = R.choice([6, 8, 10, 12, 20]); fav = R.randint(1, total - 1)
    from math import gcd
    g = gcd(fav, total)
    return (f"P = {fav}/{total} as %", f"An event has {fav} favourable of {total} outcomes. "
            f"Give the probability as a percentage (integer).",
            str(round(100 * fav / total)),
            f"P = {fav}/{total} = {round(100 * fav / total)}%.")

def T_expectation(diff, R):
    a, b = R.randint(1, 8), R.randint(1, 8)
    # equal 0.5/0.5 → mean
    if (a + b) % 2: b += 1
    return (f"E[X] for X∈{{{a},{b}}} equally likely",
            f"X takes value {a} or {b}, each with probability 0.5. Find E[X].",
            str((a + b) // 2), f"E[X] = 0.5·{a} + 0.5·{b} = {(a + b) // 2}.")

def T_bayes(diff, R):
    # keep clean: prior 1/ n, sensitivity 100%, ask posterior count style — simplify to complement
    p = R.choice([10, 20, 25, 40, 50])
    return (f"Complement of {p}%", f"If P(A) = {p}%, what is P(not A) as a percentage?",
            str(100 - p), f"P(not A) = 100% − {p}% = {100 - p}%.")

def T_mse(diff, R):
    y1, y2 = R.randint(1, 9), R.randint(1, 9)
    p1, p2 = y1 + R.choice([-2, -1, 1, 2]), y2 + R.choice([-2, -1, 1, 2])
    mse2 = (p1 - y1) ** 2 + (p2 - y2) ** 2
    if mse2 % 2: p1 += 1; mse2 = (p1 - y1) ** 2 + (p2 - y2) ** 2
    return (f"MSE of preds ({p1},{p2}) vs ({y1},{y2})",
            f"Predictions ŷ=({p1},{p2}), targets y=({y1},{y2}). Compute the mean squared error.",
            str(mse2 // 2),
            f"errors² = {(p1 - y1) ** 2} + {(p2 - y2) ** 2}; MSE = {mse2}/2 = {mse2 // 2}.")

def T_line_predict(diff, R):
    m = R.randint(1, 5); b = R.randint(0, 8); x = R.randint(1, 9)
    return (f"Predict y=({m})x+{b} at x={x}", f"For the line y = {m}x + {b}, predict y at x = {x}.",
            str(m * x + b), f"y = {m}·{x} + {b} = {m * x + b}.")

def T_slope(diff, R):
    x1, y1 = R.randint(0, 4), R.randint(0, 6)
    dx = R.randint(1, 5); m = R.randint(1, 5)
    x2, y2 = x1 + dx, y1 + m * dx
    return (f"Slope through ({x1},{y1}),({x2},{y2})",
            f"Find the slope of the line through ({x1},{y1}) and ({x2},{y2}).", str(m),
            f"m = (y₂−y₁)/(x₂−x₁) = ({y2}−{y1})/({x2}−{x1}) = {m}.")

def T_weighted(diff, R):
    w = R.choice([0.5, 0.25, 0.75]); a, b = R.randint(2, 10), R.randint(2, 10)
    val = round(w * a + (1 - w) * b, 2)
    return (f"Weighted mean {w}·{a}+{round(1-w,2)}·{b}",
            f"A mixture weights component means {a} and {b} by {w} and {round(1-w,2)}. "
            f"Give the mixture mean.", str(val),
            f"{w}·{a} + {round(1 - w, 2)}·{b} = {val}.")

def T_variance_retained(diff, R):
    evs = sorted([R.randint(1, 9) for _ in range(3)], reverse=True)
    tot = sum(evs); top = evs[0]
    return (f"PCA variance kept by top component",
            f"Eigenvalues are {evs}. What percentage of variance does the top principal "
            f"component retain? (integer %)", str(round(100 * top / tot)),
            f"{top}/{tot} = {round(100 * top / tot)}%.")

def T_distance_line(diff, R):
    # distance of point to x-axis style: |c| for line y=0 → use simple |value|
    d = R.randint(1, 9)
    return (f"Distance from ({d}, {d}) to x-axis",
            f"What is the distance from the point ({R.randint(0,9)}, {d}) to the x-axis?", str(d),
            f"Distance to the x-axis is |y| = {d}.")

TEMPLATES = {
    "add": T_add, "sub": T_sub, "mul": T_mul, "div": T_divexact, "percent": T_percent,
    "avg": T_avg, "linsolve": T_linear_solve, "evalpoly": T_eval_poly, "deriv": T_derivative,
    "gd": T_gd_step, "quadmin": T_quad_min, "dot2": T_dot2, "norm2": T_norm2, "det2": T_det2,
    "trace2": T_trace2, "probfrac": T_prob_fraction, "expect": T_expectation, "bayes": T_bayes,
    "mse": T_mse, "linepred": T_line_predict, "slope": T_slope, "weighted": T_weighted,
    "varret": T_variance_retained, "distline": T_distance_line,
}

# which templates suit each module (themed)
MODULE_TEMPLATES = {
    "linear-algebra": ["linsolve", "dot2", "add", "sub", "mul", "det2"],
    "analytic-geometry": ["norm2", "dot2", "distline", "add", "mul"],
    "matrix-decompositions": ["det2", "trace2", "mul", "add", "evalpoly"],
    "vector-calculus": ["deriv", "evalpoly", "gd", "mul", "add"],
    "probability": ["probfrac", "expect", "bayes", "avg", "percent"],
    "optimization": ["gd", "quadmin", "deriv", "evalpoly", "linsolve"],
    "models-and-data": ["mse", "avg", "percent", "add", "linepred"],
    "linear-regression": ["slope", "linepred", "mse", "evalpoly", "add"],
    "pca": ["varret", "avg", "det2", "percent", "norm2"],
    "gmm": ["weighted", "avg", "expect", "percent", "probfrac"],
    "svm": ["dot2", "distline", "norm2", "linepred", "add"],
}
DIFFS = ["easy", "medium", "hard"]


def generate(module_key, chapter_titles, count=1000, seed=0):
    """Yield `count` problem dicts for a module, spread across chapters + difficulties."""
    R = random.Random(hash((module_key, seed)) & 0xffffffff)
    tmpl_keys = MODULE_TEMPLATES.get(module_key, ["add", "sub", "mul", "avg", "percent"])
    n_ch = max(1, len(chapter_titles))
    out = []
    for i in range(count):
        ch_idx = i % n_ch
        diff = DIFFS[i % 3]
        key = tmpl_keys[i % len(tmpl_keys)]
        title, statement, answer, editorial = TEMPLATES[key](diff, R)
        # tie the statement to its topic so it reads as belonging to the chapter
        topic = chapter_titles[ch_idx]
        out.append({
            "chapter_idx": ch_idx, "difficulty": diff,
            "title": f"{title}",
            "statement": f"[{topic}]  {statement}",
            "answer": answer, "editorial": editorial,
        })
    return out
