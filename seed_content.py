"""Seed the M³ curriculum from *Mathematics for Machine Learning*
(Deisenroth, Faisal & Ong, 2020). Runs once, on first startup.

Structure: MODULES -> chapters (sections from the book) -> seed problems.
Each seed problem carries a difficulty and a step-by-step official editorial.
Users can add their own modules / chapters / problems on top of these.
"""
from models import db, Module, Chapter, Problem

# (key, icon, part, title, description, [chapters], [seed problems])
# Each seed problem: (chapter_index, title, difficulty, statement, editorial)
CURRICULUM = [
    {
        "key": "linear-algebra", "icon": "➗", "part": "Mathematical Foundations",
        "title": "Linear Algebra",
        "description": "Vectors, matrices, vector spaces and linear mappings — the language ML is written in.",
        "chapters": [
            "Systems of Linear Equations", "Matrices", "Solving Systems of Linear Equations",
            "Vector Spaces", "Linear Independence", "Basis and Rank", "Linear Mappings",
            "Affine Spaces",
        ],
        "problems": [
            (0, "Solve a 2×2 system", "easy",
             "Solve for x and y:\n  2x + y = 5\n  x − y = 1",
             "Add the two equations to eliminate y: (2x+y)+(x−y)=5+1 → 3x=6 → x=2.\n"
             "Substitute into x−y=1: 2−y=1 → y=1.\nSolution: x=2, y=1."),
            (1, "Matrix–vector product", "easy",
             "Compute A·v where A = [[1,2],[0,3]] and v = [4,5]ᵀ.",
             "Row 1: 1·4 + 2·5 = 4+10 = 14.\nRow 2: 0·4 + 3·5 = 0+15 = 15.\nResult: [14, 15]ᵀ."),
            (4, "Test linear independence", "medium",
             "Are the vectors (1,2), (2,4) linearly independent? Justify.",
             "Two vectors are dependent if one is a scalar multiple of the other.\n"
             "(2,4) = 2·(1,2), so they are linearly DEPENDENT. The set spans only a line."),
            (5, "Rank of a matrix", "hard",
             "Find the rank of A = [[1,2,3],[2,4,6],[1,1,1]].",
             "Row-reduce. R2 ← R2 − 2·R1 = [0,0,0]. R3 ← R3 − R1 = [0,−1,−2].\n"
             "Non-zero rows: R1=[1,2,3] and [0,−1,−2] → 2 pivots. Rank(A) = 2."),
        ],
    },
    {
        "key": "analytic-geometry", "icon": "📐", "part": "Mathematical Foundations",
        "title": "Analytic Geometry",
        "description": "Norms, inner products, angles, projections and rotations.",
        "chapters": [
            "Norms", "Inner Products", "Lengths and Distances", "Angles and Orthogonality",
            "Orthonormal Basis", "Orthogonal Complement", "Inner Product of Functions",
            "Orthogonal Projections", "Rotations",
        ],
        "problems": [
            (0, "Euclidean norm", "easy",
             "Compute the Euclidean (ℓ2) norm of x = (3, 4).",
             "‖x‖₂ = √(3² + 4²) = √(9+16) = √25 = 5."),
            (3, "Angle between vectors", "medium",
             "Find the angle between u = (1,0) and v = (1,1).",
             "cos θ = (u·v)/(‖u‖‖v‖) = (1)/(1·√2) = 1/√2.\nθ = 45° (π/4 radians)."),
            (7, "Orthogonal projection", "hard",
             "Project b = (2,3) onto the line spanned by a = (1,0).",
             "proj_a(b) = ((a·b)/(a·a)) a = (2/1)(1,0) = (2,0).\n"
             "The projection keeps only the component of b along a."),
        ],
    },
    {
        "key": "matrix-decompositions", "icon": "🧩", "part": "Mathematical Foundations",
        "title": "Matrix Decompositions",
        "description": "Determinants, eigenvalues, eigendecomposition, SVD and low-rank approximation.",
        "chapters": [
            "Determinant and Trace", "Eigenvalues and Eigenvectors", "Cholesky Decomposition",
            "Eigendecomposition and Diagonalization", "Singular Value Decomposition",
            "Matrix Approximation", "Matrix Phylogeny",
        ],
        "problems": [
            (0, "Determinant of a 2×2", "easy",
             "Compute det(A) for A = [[3,8],[4,6]].",
             "det = ad − bc = 3·6 − 8·4 = 18 − 32 = −14."),
            (1, "Find the eigenvalues", "medium",
             "Find the eigenvalues of A = [[2,0],[0,3]].",
             "For a diagonal matrix the eigenvalues are the diagonal entries: λ₁=2, λ₂=3.\n"
             "(Check: det(A−λI)=(2−λ)(3−λ)=0.)"),
            (4, "SVD intuition", "hard",
             "Explain what the singular values of a matrix represent geometrically.",
             "SVD writes A = UΣVᵀ. The singular values (diagonal of Σ) are the lengths of the "
             "semi-axes of the ellipse that the unit circle maps to under A. Larger singular "
             "values = directions of greatest stretch; small ones can be dropped for low-rank "
             "approximation."),
        ],
    },
    {
        "key": "vector-calculus", "icon": "📈", "part": "Mathematical Foundations",
        "title": "Vector Calculus",
        "description": "Derivatives, gradients, the chain rule and backpropagation.",
        "chapters": [
            "Differentiation of Univariate Functions", "Partial Differentiation and Gradients",
            "Gradients of Vector-Valued Functions", "Gradients of Matrices",
            "Useful Identities for Computing Gradients",
            "Backpropagation and Automatic Differentiation", "Higher-Order Derivatives",
            "Linearization and Multivariate Taylor Series",
        ],
        "problems": [
            (0, "Basic derivative", "easy",
             "Differentiate f(x) = 3x² + 2x − 5.",
             "f'(x) = 6x + 2. (Power rule term by term; the constant vanishes.)"),
            (1, "Gradient of a function", "medium",
             "Find ∇f for f(x,y) = x²y + y³.",
             "∂f/∂x = 2xy.\n∂f/∂y = x² + 3y².\n∇f = (2xy, x² + 3y²)."),
            (5, "Chain rule / backprop", "hard",
             "For z = (2x+1)³, use the chain rule to find dz/dx.",
             "Let u = 2x+1, z = u³. dz/du = 3u², du/dx = 2.\n"
             "dz/dx = 3u²·2 = 6(2x+1)². This nesting is exactly what backprop automates."),
        ],
    },
    {
        "key": "probability", "icon": "🎲", "part": "Mathematical Foundations",
        "title": "Probability and Distributions",
        "description": "Probability spaces, Bayes' theorem, expectation, variance and the Gaussian.",
        "chapters": [
            "Construction of a Probability Space", "Discrete and Continuous Probabilities",
            "Sum Rule, Product Rule, and Bayes' Theorem", "Summary Statistics and Independence",
            "Gaussian Distribution", "Conjugacy and the Exponential Family",
            "Change of Variables / Inverse Transform",
        ],
        "problems": [
            (1, "Basic probability", "easy",
             "A fair die is rolled. What is P(even number)?",
             "Even outcomes = {2,4,6} → 3 favourable of 6. P = 3/6 = 1/2."),
            (2, "Apply Bayes' theorem", "hard",
             "A test is 99% accurate. A disease affects 1 in 1000. If you test positive, what is "
             "the probability you actually have it? (Assume 1% false-positive rate.)",
             "P(D)=0.001, P(+|D)=0.99, P(+|¬D)=0.01.\n"
             "P(+) = 0.99·0.001 + 0.01·0.999 = 0.00099 + 0.00999 = 0.01098.\n"
             "P(D|+) = 0.00099 / 0.01098 ≈ 0.090 → about 9%. Base rates dominate."),
            (3, "Expectation and variance", "medium",
             "For X with P(X=1)=0.5 and P(X=3)=0.5, find E[X] and Var(X).",
             "E[X] = 1·0.5 + 3·0.5 = 2.\nE[X²] = 1·0.5 + 9·0.5 = 5.\n"
             "Var(X) = E[X²] − E[X]² = 5 − 4 = 1."),
        ],
    },
    {
        "key": "optimization", "icon": "⛰️", "part": "Mathematical Foundations",
        "title": "Continuous Optimization",
        "description": "Gradient descent, constrained optimization with Lagrange multipliers, convexity.",
        "chapters": [
            "Optimization Using Gradient Descent",
            "Constrained Optimization and Lagrange Multipliers", "Convex Optimization",
        ],
        "problems": [
            (0, "One gradient-descent step", "medium",
             "Minimise f(x)=x². Starting at x=4 with learning rate η=0.1, compute x after one step.",
             "f'(x)=2x → gradient at x=4 is 8.\nUpdate: x ← x − η·f'(x) = 4 − 0.1·8 = 3.2.\n"
             "Each step moves downhill toward the minimum at x=0."),
            (0, "Minimum of a quadratic", "easy",
             "Where is the minimum of f(x) = (x−3)² + 2?",
             "A squared term is smallest when it is zero: x−3=0 → x=3, giving f=2. Minimum at (3, 2)."),
            (2, "Check convexity", "hard",
             "Is f(x) = x⁴ convex? Justify with the second derivative.",
             "f'(x)=4x³, f''(x)=12x² ≥ 0 for all x. A non-negative second derivative means f is "
             "convex everywhere."),
        ],
    },
    {
        "key": "models-and-data", "icon": "🧠", "part": "Central ML Problems",
        "title": "When Models Meet Data",
        "description": "Empirical risk minimization, parameter estimation, inference and model selection.",
        "chapters": [
            "Data, Models, and Learning", "Empirical Risk Minimization", "Parameter Estimation",
            "Probabilistic Modeling and Inference", "Directed Graphical Models", "Model Selection",
        ],
        "problems": [
            (1, "Mean squared error", "easy",
             "Predictions ŷ=(2,4), targets y=(3,2). Compute the mean squared error.",
             "Errors: (2−3)²=1, (4−2)²=4. MSE = (1+4)/2 = 2.5."),
            (5, "Overfitting vs underfitting", "medium",
             "Training error is tiny but test error is large. Name the problem and one fix.",
             "This is OVERFITTING — the model memorised the training set. Fixes: regularisation, "
             "more data, a simpler model, or cross-validation for model selection."),
        ],
    },
    {
        "key": "linear-regression", "icon": "📉", "part": "Central ML Problems",
        "title": "Linear Regression",
        "description": "Least squares, maximum likelihood, and Bayesian linear regression.",
        "chapters": [
            "Problem Formulation", "Parameter Estimation", "Bayesian Linear Regression",
            "Maximum Likelihood as Orthogonal Projection",
        ],
        "problems": [
            (1, "Fit a line through two points", "easy",
             "Find the slope and intercept of the line through (0,1) and (2,5).",
             "slope m = (5−1)/(2−0) = 2. Intercept b: at x=0, y=1 → b=1. Line: y = 2x + 1."),
            (1, "Normal equations", "hard",
             "State the closed-form least-squares solution for θ in y = Xθ, and say why XᵀX must be invertible.",
             "θ = (XᵀX)⁻¹Xᵀy. It minimises ‖y − Xθ‖².\nXᵀX must be invertible (columns of X "
             "linearly independent) for a unique solution; otherwise use a pseudo-inverse or add "
             "regularisation."),
        ],
    },
    {
        "key": "pca", "icon": "🔻", "part": "Central ML Problems",
        "title": "Dimensionality Reduction (PCA)",
        "description": "Principal Component Analysis via maximum variance and projection.",
        "chapters": [
            "Problem Setting", "Maximum Variance Perspective", "Projection Perspective",
            "Eigenvector Computation and Low-Rank Approximations", "PCA in High Dimensions",
            "Key Steps of PCA in Practice", "Latent Variable Perspective",
        ],
        "problems": [
            (5, "Steps of PCA", "medium",
             "List the main steps to reduce data to k dimensions with PCA.",
             "1) Centre the data (subtract the mean).\n2) Compute the covariance matrix.\n"
             "3) Find its eigenvectors/eigenvalues.\n4) Keep the k eigenvectors with the largest "
             "eigenvalues.\n5) Project the centred data onto those eigenvectors."),
            (1, "Why maximise variance?", "hard",
             "In PCA, why do we choose directions that maximise the projected variance?",
             "High-variance directions retain the most information about how samples differ. "
             "Projecting onto them minimises reconstruction error (equivalently maximises retained "
             "variance), giving the best low-rank summary of the data."),
        ],
    },
    {
        "key": "gmm", "icon": "🔔", "part": "Central ML Problems",
        "title": "Density Estimation (GMM)",
        "description": "Gaussian Mixture Models and the Expectation–Maximization algorithm.",
        "chapters": [
            "Gaussian Mixture Model", "Parameter Learning via Maximum Likelihood",
            "EM Algorithm", "Latent-Variable Perspective",
        ],
        "problems": [
            (0, "What is a GMM?", "easy",
             "In one or two sentences, what does a Gaussian Mixture Model represent?",
             "A GMM models data as coming from a weighted sum of several Gaussian distributions, "
             "each with its own mean and covariance. It captures multi-modal data a single Gaussian "
             "cannot."),
            (2, "The two EM steps", "medium",
             "Name and describe the two steps of the EM algorithm.",
             "E-step: given current parameters, compute the responsibility (posterior probability) "
             "of each component for each point.\nM-step: given those responsibilities, re-estimate "
             "each component's weight, mean and covariance. Repeat until convergence."),
        ],
    },
    {
        "key": "svm", "icon": "🚧", "part": "Central ML Problems",
        "title": "Classification (SVM)",
        "description": "Separating hyperplanes, margins, the dual formulation and kernels.",
        "chapters": [
            "Separating Hyperplanes", "Primal Support Vector Machine",
            "Dual Support Vector Machine", "Kernels", "Numerical Solution",
        ],
        "problems": [
            (0, "Margin idea", "easy",
             "In an SVM, what is the 'margin' and what does the SVM do with it?",
             "The margin is the distance between the separating hyperplane and the nearest data "
             "points (support vectors). An SVM chooses the hyperplane that MAXIMISES this margin, "
             "which tends to generalise better."),
            (3, "The kernel trick", "hard",
             "Explain the kernel trick in one short paragraph.",
             "Instead of explicitly mapping data into a high-dimensional feature space φ(x), a "
             "kernel k(x,x') computes the inner product ⟨φ(x),φ(x')⟩ directly and cheaply. This lets "
             "an SVM learn non-linear boundaries without ever forming φ(x) — e.g. the RBF kernel "
             "corresponds to an infinite-dimensional space."),
        ],
    },
]


PROBLEMS_PER_MODULE = 1000  # auto-generated practice problems per module


def seed(app):
    import problem_bank
    with app.app_context():
        if Module.query.first():
            return  # already seeded
        for mi, m in enumerate(CURRICULUM):
            module = Module(key=m["key"], icon=m["icon"], part=m["part"],
                            title=m["title"], description=m["description"], order=mi)
            db.session.add(module)
            db.session.flush()
            chapter_objs = []
            for ci, ctitle in enumerate(m["chapters"]):
                ch = Chapter(module_id=module.id, title=ctitle, order=ci)
                db.session.add(ch)
                chapter_objs.append(ch)
            db.session.flush()

            # curated problems (with worked editorials)
            curated = 0
            for (cidx, title, diff, stmt, editorial) in m["problems"]:
                cidx = min(cidx, len(chapter_objs) - 1)
                db.session.add(Problem(chapter_id=chapter_objs[cidx].id, module_id=module.id,
                                       title=title, statement=stmt, difficulty=diff,
                                       official_editorial=editorial))
                curated += 1

            # top up to PROBLEMS_PER_MODULE with generated, answer-checkable problems
            n_gen = max(0, PROBLEMS_PER_MODULE - curated)
            gen = problem_bank.generate(m["key"], m["chapters"], count=n_gen)
            objs = [Problem(chapter_id=chapter_objs[g["chapter_idx"]].id, module_id=module.id,
                            title=g["title"], statement=g["statement"], difficulty=g["difficulty"],
                            answer=g["answer"], official_editorial=g["editorial"]) for g in gen]
            db.session.bulk_save_objects(objs)
            db.session.commit()
