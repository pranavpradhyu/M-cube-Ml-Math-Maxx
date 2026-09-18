"""Database models for M³ (ML Math Maxx)."""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

MEDALS = [
    (10000, "Platinum", "💎"),
    (5000, "Gold", "🥇"),
    (1000, "Silver", "🥈"),
]
# point rules
POINTS_DAILY_LOGIN = 1
POINTS_CORRECT_SOLVE = 10
POINTS_EDITORIAL_UNLOCK = -10


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(300), nullable=False)
    photo = db.Column(db.String(300))
    points = db.Column(db.Integer, default=0)              # streak points (stored)
    last_login_award = db.Column(db.Date)                  # last day a login point was granted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def add_points(self, n):
        self.points = max(0, (self.points or 0) + n)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self):
        a = (self.first_name or " ")[0]
        b = (self.last_name or " ")[0]
        return (a + b).upper()

    @property
    def streak_points(self):
        return self.points or 0

    @property
    def medal(self):
        pts = self.streak_points
        for threshold, name, icon in MEDALS:
            if pts >= threshold:
                return {"name": name, "icon": icon, "threshold": threshold}
        return None

    @property
    def next_medal(self):
        pts = self.streak_points
        for threshold, name, icon in sorted(MEDALS):
            if pts < threshold:
                return {"name": name, "icon": icon, "threshold": threshold, "remaining": threshold - pts}
        return None

    @property
    def problems_solved(self):
        return ProblemSolve.query.filter_by(user_id=self.id).count()

    @property
    def modules_completed(self):
        """Modules in which the user has solved at least one problem."""
        rows = (db.session.query(Problem.module_id)
                .join(ProblemSolve, ProblemSolve.problem_id == Problem.id)
                .filter(ProblemSolve.user_id == self.id).distinct().all())
        return len(rows)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(16), default="📘")
    part = db.Column(db.String(120), default="Custom")
    description = db.Column(db.Text, default="")
    order = db.Column(db.Integer, default=100)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    chapters = db.relationship("Chapter", backref="module", cascade="all, delete-orphan",
                               order_by="Chapter.order")
    author = db.relationship("User")

    @property
    def is_custom(self):
        return self.created_by is not None


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("module.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    order = db.Column(db.Integer, default=100)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    problems = db.relationship("Problem", backref="chapter", cascade="all, delete-orphan",
                               order_by="Problem.id")
    author = db.relationship("User")

    @property
    def is_custom(self):
        return self.created_by is not None


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("module.id"), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    statement = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(10), default="medium")
    answer = db.Column(db.String(120))                       # expected answer (for auto-check)
    official_editorial = db.Column(db.Text, default="")      # locked step-by-step solution
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    module = db.relationship("Module")
    author = db.relationship("User")
    submissions = db.relationship("Submission", backref="problem", cascade="all, delete-orphan",
                                  order_by="Submission.created_at.desc()")
    messages = db.relationship("DiscussionMessage", backref="problem", cascade="all, delete-orphan",
                               order_by="DiscussionMessage.created_at")

    DIFF_META = {
        "easy": ("Easy", "#16a34a"),
        "medium": ("Medium", "#d97706"),
        "hard": ("Hard", "#dc2626"),
    }

    @property
    def difficulty_label(self):
        return self.DIFF_META.get(self.difficulty, ("Medium", "#d97706"))[0]

    @property
    def difficulty_color(self):
        return self.DIFF_META.get(self.difficulty, ("Medium", "#d97706"))[1]

    def solved_by(self, user_id):
        return ProblemSolve.query.filter_by(user_id=user_id, problem_id=self.id).first() is not None

    def unlocked_by(self, user_id):
        return EditorialUnlock.query.filter_by(user_id=user_id, problem_id=self.id).first() is not None

    @property
    def is_custom(self):
        return self.created_by is not None


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, default="")
    pdf = db.Column(db.String(300))
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


class DiscussionMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, default="")
    image = db.Column(db.String(300))
    edited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


class ProblemSolve(db.Model):
    """Records that a user has solved a problem correctly (drives completion + points)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "problem_id", name="uq_user_problem_solve"),)


class EditorialUnlock(db.Model):
    """Records that a user has unlocked a problem's editorial (charged -10 once)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "problem_id", name="uq_user_problem_unlock"),)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    kind = db.Column(db.String(20), default="note")
    body = db.Column(db.Text, default="")
    attachment = db.Column(db.String(300))        # stored filename
    attachment_name = db.Column(db.String(300))   # original filename for display
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"))
    module_id = db.Column(db.Integer, db.ForeignKey("module.id"))
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"))
    edited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    problem = db.relationship("Problem")
    module = db.relationship("Module")
    chapter = db.relationship("Chapter")
    replies = db.relationship("PostReply", backref="post", cascade="all, delete-orphan",
                              order_by="PostReply.created_at")


class PostReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, default=5)
    category = db.Column(db.String(40), default="general")
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    replies = db.relationship("FeedbackReply", backref="feedback", cascade="all, delete-orphan",
                              order_by="FeedbackReply.created_at")


class FeedbackReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback_id = db.Column(db.Integer, db.ForeignKey("feedback.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    kind = db.Column(db.String(30), default="info")
    message = db.Column(db.String(400), nullable=False)
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NumberGameScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    level = db.Column(db.String(10), default="easy")
    duration = db.Column(db.Integer, default=60)   # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
