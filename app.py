"""M³ — ML Math Maxx  (community math-for-ML platform)."""
import os
import uuid
from datetime import datetime, date

from flask import (Flask, render_template, request, redirect, url_for, flash,
                   jsonify, abort)
from flask_login import (LoginManager, login_user, logout_user, login_required,
                         current_user)
from werkzeug.utils import secure_filename

from models import (db, User, Module, Chapter, Problem, Submission,
                    DiscussionMessage, ProblemSolve, EditorialUnlock, Post, PostReply,
                    Feedback, FeedbackReply, Notification, NumberGameScore, MEDALS,
                    POINTS_DAILY_LOGIN, POINTS_CORRECT_SOLVE, POINTS_EDITORIAL_UNLOCK)
from number_game import number_game_question
from notifications import notify, notify_all_except
import seed_content

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_PDF = {".pdf"}
ALLOWED_IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_ATTACH = ALLOWED_IMG | ALLOWED_PDF | {".doc", ".docx", ".ppt", ".pptx",
                                              ".xls", ".xlsx", ".txt", ".csv", ".zip"}
PER_CHAPTER_PREVIEW = 12
CHAPTER_PAGE_SIZE = 30

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
db_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'mathmaxx.db')}")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


# ---------------------------------------------------------------- helpers
def _save_file(file_storage, allowed_ext):
    if not file_storage or not file_storage.filename:
        return None, None
    original = secure_filename(file_storage.filename)
    ext = os.path.splitext(original)[1].lower()
    if ext not in allowed_ext:
        return None, None
    name = uuid.uuid4().hex + ext
    file_storage.save(os.path.join(UPLOAD_DIR, name))
    return name, original


def _answers_match(user_ans, expected):
    """None if not auto-checkable; else True/False."""
    if not expected:
        return None
    u = (user_ans or "").strip().lower().replace(" ", "")
    e = str(expected).strip().lower().replace(" ", "")
    if not u:
        return False
    try:
        return abs(float(u) - float(e)) < 1e-6
    except ValueError:
        return u == e


def _award_points(user, delta):
    """Apply a point change and fire a medal notification on threshold crossing."""
    before = user.streak_points
    user.add_points(delta)
    db.session.commit()
    after = user.streak_points
    for threshold, name, icon in sorted(MEDALS):
        if before < threshold <= after:
            notify(user.id, f"{icon} You earned the {name} medal ({threshold} points)!",
                   link=url_for("profile"), kind="medal",
                   email_subject=f"You earned the {name} medal on M³")
            flash(f"{icon} {name} medal unlocked!", "success")


def _award_daily_login(user):
    today = date.today()
    if user.last_login_award != today:
        user.last_login_award = today
        _award_points(user, POINTS_DAILY_LOGIN)


@app.context_processor
def inject_globals():
    unread, recent_notes = 0, []
    if current_user.is_authenticated:
        unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        recent_notes = (Notification.query.filter_by(user_id=current_user.id)
                        .order_by(Notification.created_at.desc()).limit(8).all())
    return {"app_name": "M³", "app_full": "ML Math Maxx",
            "unread_count": unread, "recent_notes": recent_notes, "now": datetime.utcnow()}


# ---------------------------------------------------------------- auth
@app.route("/")
def index():
    return redirect(url_for("dashboard") if current_user.is_authenticated else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        f = request.form
        first = (f.get("first_name") or "").strip()
        last = (f.get("last_name") or "").strip()
        email = (f.get("email") or "").strip().lower()
        pw = f.get("password") or ""
        confirm = f.get("confirm_password") or ""
        form = {"first_name": first, "last_name": last, "email": email}
        if not (first and last and email and pw):
            flash("Please fill in all fields.", "error"); return render_template("register.html", form=form)
        if len(pw) < 6:
            flash("Password must be at least 6 characters.", "error"); return render_template("register.html", form=form)
        if pw != confirm:
            flash("Passwords do not match.", "error"); return render_template("register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error"); return render_template("register.html", form=form)
        u = User(first_name=first, last_name=last, email=email)
        u.set_password(pw)
        db.session.add(u); db.session.commit()
        login_user(u)
        _award_daily_login(u)
        flash("Welcome to M³! Your account is ready.", "success")
        return redirect(url_for("dashboard"))
    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(pw):
            login_user(u)
            _award_daily_login(u)
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    modules = Module.query.order_by(Module.order, Module.id).all()
    parts = {}
    for m in modules:
        parts.setdefault(m.part, []).append(m)
    posts = Post.query.order_by(Post.created_at.desc()).limit(40).all()
    return render_template("dashboard.html", parts=parts, posts=posts)


# ---------------------------------------------------------------- modules
@app.route("/module/new", methods=["GET", "POST"])
@login_required
def module_new():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Module needs a title.", "error"); return redirect(url_for("module_new"))
        key = secure_filename(title.lower().replace(" ", "-"))[:70] or uuid.uuid4().hex[:8]
        if Module.query.filter_by(key=key).first():
            key = key + "-" + uuid.uuid4().hex[:4]
        m = Module(key=key, title=title, icon=(request.form.get("icon") or "📗")[:8],
                   part=(request.form.get("part") or "Custom").strip(),
                   description=(request.form.get("description") or "").strip(),
                   order=1000, created_by=current_user.id)
        db.session.add(m); db.session.commit()
        db.session.add(Post(user_id=current_user.id, kind="module",
                            body=f"added a new module: {title}", module_id=m.id))
        db.session.commit()
        notify_all_except(current_user.id, f"{current_user.full_name} added a new module: {title}",
                          link=url_for("module_view", key=m.key), kind="module",
                          email_subject="New module on M³")
        flash("Module created.", "success")
        return redirect(url_for("module_view", key=m.key))
    return render_template("module_form.html")


@app.route("/module/<key>")
@login_required
def module_view(key):
    m = Module.query.filter_by(key=key).first_or_404()
    diff = request.args.get("difficulty", "all")
    solved = {r.problem_id for r in ProblemSolve.query.filter_by(user_id=current_user.id).all()}
    chapters = []
    for ch in m.chapters:
        q = Problem.query.filter_by(chapter_id=ch.id)
        if diff in ("easy", "medium", "hard"):
            q = q.filter_by(difficulty=diff)
        total = q.count()
        probs = q.order_by(Problem.id).limit(PER_CHAPTER_PREVIEW).all()
        solved_here = sum(1 for p in Problem.query.filter_by(chapter_id=ch.id).all()
                          if p.id in solved)
        chapters.append({"chapter": ch, "problems": probs, "total": total,
                         "solved_here": solved_here,
                         "count_all": Problem.query.filter_by(chapter_id=ch.id).count()})
    return render_template("module.html", m=m, chapters=chapters, diff=diff, solved=solved)


@app.route("/module/<key>/delete", methods=["POST"])
@login_required
def module_delete(key):
    m = Module.query.filter_by(key=key).first_or_404()
    if not m.is_custom:
        flash("Built-in curriculum modules can't be deleted.", "error")
        return redirect(url_for("module_view", key=key))
    problem_ids = [pid for (pid,) in db.session.query(Problem.id).filter_by(module_id=m.id).all()]
    chapter_ids = [cid for (cid,) in db.session.query(Chapter.id).filter_by(module_id=m.id).all()]
    if problem_ids:
        Submission.query.filter(Submission.problem_id.in_(problem_ids)).delete(synchronize_session=False)
        DiscussionMessage.query.filter(DiscussionMessage.problem_id.in_(problem_ids)).delete(synchronize_session=False)
        ProblemSolve.query.filter(ProblemSolve.problem_id.in_(problem_ids)).delete(synchronize_session=False)
        EditorialUnlock.query.filter(EditorialUnlock.problem_id.in_(problem_ids)).delete(synchronize_session=False)
    # remove posts referencing this module / its chapters / its problems
    conds = [Post.module_id == m.id]
    if chapter_ids:
        conds.append(Post.chapter_id.in_(chapter_ids))
    if problem_ids:
        conds.append(Post.problem_id.in_(problem_ids))
    Post.query.filter(db.or_(*conds)).delete(synchronize_session=False)
    Problem.query.filter_by(module_id=m.id).delete(synchronize_session=False)
    Chapter.query.filter_by(module_id=m.id).delete(synchronize_session=False)
    db.session.delete(m)
    db.session.commit()
    flash(f"Module “{m.title}” and all its content were deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/module/<key>/edit", methods=["GET", "POST"])
@login_required
def module_edit(key):
    m = Module.query.filter_by(key=key).first_or_404()
    if not m.is_custom:
        flash("Built-in curriculum modules can't be edited.", "error")
        return redirect(url_for("module_view", key=key))
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Module needs a title.", "error")
            return redirect(url_for("module_edit", key=key))
        m.title = title
        m.icon = (request.form.get("icon") or m.icon)[:8]
        m.part = (request.form.get("part") or m.part).strip()
        m.description = (request.form.get("description") or "").strip()
        db.session.commit()
        flash("Module updated.", "success")
        return redirect(url_for("module_view", key=m.key))
    return render_template("module_form.html", m=m)


@app.route("/module/<key>/chapter/new", methods=["POST"])
@login_required
def chapter_new(key):
    m = Module.query.filter_by(key=key).first_or_404()
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Chapter needs a title.", "error"); return redirect(url_for("module_view", key=key))
    order = max([c.order for c in m.chapters], default=0) + 1
    ch = Chapter(module_id=m.id, title=title, content=(request.form.get("content") or "").strip(),
                 order=order, created_by=current_user.id)
    db.session.add(ch); db.session.commit()
    db.session.add(Post(user_id=current_user.id, kind="chapter",
                        body=f"added a chapter “{title}” to {m.title}", module_id=m.id, chapter_id=ch.id))
    db.session.commit()
    flash("Chapter added.", "success")
    return redirect(url_for("module_view", key=key))


@app.route("/chapter/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def chapter_edit(cid):
    ch = Chapter.query.get_or_404(cid)
    if not ch.is_custom:
        flash("Built-in chapters can't be edited.", "error")
        return redirect(url_for("module_view", key=ch.module.key))
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Chapter needs a title.", "error")
            return redirect(url_for("chapter_edit", cid=cid))
        ch.title = title
        ch.content = (request.form.get("content") or "").strip()
        db.session.commit()
        flash("Chapter updated.", "success")
        return redirect(url_for("module_view", key=ch.module.key))
    return render_template("chapter_form.html", ch=ch)


@app.route("/chapter/<int:cid>/delete", methods=["POST"])
@login_required
def chapter_delete(cid):
    ch = Chapter.query.get_or_404(cid)
    if not ch.is_custom:
        flash("Built-in chapters can't be deleted.", "error")
        return redirect(url_for("module_view", key=ch.module.key))
    module_key = ch.module.key
    problem_ids = [pid for (pid,) in db.session.query(Problem.id).filter_by(chapter_id=ch.id).all()]
    if problem_ids:
        Submission.query.filter(Submission.problem_id.in_(problem_ids)).delete(synchronize_session=False)
        DiscussionMessage.query.filter(DiscussionMessage.problem_id.in_(problem_ids)).delete(synchronize_session=False)
        ProblemSolve.query.filter(ProblemSolve.problem_id.in_(problem_ids)).delete(synchronize_session=False)
        EditorialUnlock.query.filter(EditorialUnlock.problem_id.in_(problem_ids)).delete(synchronize_session=False)
    conds = [Post.chapter_id == ch.id]
    if problem_ids:
        conds.append(Post.problem_id.in_(problem_ids))
    Post.query.filter(db.or_(*conds)).delete(synchronize_session=False)
    Problem.query.filter_by(chapter_id=ch.id).delete(synchronize_session=False)
    db.session.delete(ch)
    db.session.commit()
    flash(f"Chapter “{ch.title}” and its problems were deleted.", "success")
    return redirect(url_for("module_view", key=module_key))


@app.route("/chapter/<int:cid>")
@login_required
def chapter_view(cid):
    ch = Chapter.query.get_or_404(cid)
    diff = request.args.get("difficulty", "all")
    page = max(1, int(request.args.get("page", 1) or 1))
    q = Problem.query.filter_by(chapter_id=cid)
    if diff in ("easy", "medium", "hard"):
        q = q.filter_by(difficulty=diff)
    total = q.count()
    probs = (q.order_by(Problem.id).offset((page - 1) * CHAPTER_PAGE_SIZE)
             .limit(CHAPTER_PAGE_SIZE).all())
    solved = {r.problem_id for r in ProblemSolve.query.filter_by(user_id=current_user.id).all()}
    pages = (total + CHAPTER_PAGE_SIZE - 1) // CHAPTER_PAGE_SIZE
    return render_template("chapter.html", ch=ch, probs=probs, diff=diff, page=page,
                           pages=pages, total=total, solved=solved)


@app.route("/chapter/<int:cid>/problem/new", methods=["GET", "POST"])
@login_required
def problem_new(cid):
    ch = Chapter.query.get_or_404(cid)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        statement = (request.form.get("statement") or "").strip()
        difficulty = request.form.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"
        if not (title and statement):
            flash("A problem needs a title and a statement.", "error")
            return redirect(url_for("problem_new", cid=cid))
        p = Problem(chapter_id=ch.id, module_id=ch.module_id, title=title, statement=statement,
                    difficulty=difficulty, answer=(request.form.get("answer") or "").strip() or None,
                    official_editorial=(request.form.get("editorial") or "").strip(),
                    created_by=current_user.id)
        db.session.add(p); db.session.commit()
        db.session.add(Post(user_id=current_user.id, kind="problem",
                            body=f"posted a {difficulty} problem “{title}” in {ch.module.title}",
                            problem_id=p.id, module_id=ch.module_id, chapter_id=ch.id))
        db.session.commit()
        notify_all_except(current_user.id, f"{current_user.full_name} posted a new problem: {title}",
                          link=url_for("problem_view", pid=p.id), kind="problem",
                          email_subject="New problem posted on M³")
        flash("Problem posted.", "success")
        return redirect(url_for("problem_view", pid=p.id))
    return render_template("problem_form.html", ch=ch)


@app.route("/problem/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def problem_edit(pid):
    p = Problem.query.get_or_404(pid)
    if not p.is_custom:
        flash("Built-in problems can't be edited.", "error")
        return redirect(url_for("problem_view", pid=pid))
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        statement = (request.form.get("statement") or "").strip()
        difficulty = request.form.get("difficulty", p.difficulty)
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = p.difficulty
        if not (title and statement):
            flash("A problem needs a title and a statement.", "error")
            return redirect(url_for("problem_edit", pid=pid))
        p.title = title
        p.statement = statement
        p.difficulty = difficulty
        p.answer = (request.form.get("answer") or "").strip() or None
        p.official_editorial = (request.form.get("editorial") or "").strip()
        db.session.commit()
        flash("Problem updated.", "success")
        return redirect(url_for("problem_view", pid=pid))
    return render_template("problem_form.html", p=p, ch=p.chapter)


@app.route("/problem/<int:pid>/delete", methods=["POST"])
@login_required
def problem_delete(pid):
    p = Problem.query.get_or_404(pid)
    if not p.is_custom:
        flash("Built-in problems can't be deleted.", "error")
        return redirect(url_for("problem_view", pid=pid))
    chapter_id = p.chapter_id
    ProblemSolve.query.filter_by(problem_id=p.id).delete(synchronize_session=False)
    EditorialUnlock.query.filter_by(problem_id=p.id).delete(synchronize_session=False)
    Post.query.filter_by(problem_id=p.id).delete(synchronize_session=False)
    db.session.delete(p)  # cascades submissions, discussion messages via relationship
    db.session.commit()
    flash(f"Problem “{p.title}” was deleted.", "success")
    return redirect(url_for("chapter_view", cid=chapter_id))


# ---------------------------------------------------------------- problems
@app.route("/problem/<int:pid>")
@login_required
def problem_view(pid):
    p = Problem.query.get_or_404(pid)
    unlocked = p.unlocked_by(current_user.id)
    solved = p.solved_by(current_user.id)
    return render_template("problem.html", p=p, unlocked=unlocked, solved=solved)


@app.route("/problem/<int:pid>/submit", methods=["POST"])
@login_required
def problem_submit(pid):
    p = Problem.query.get_or_404(pid)
    body = (request.form.get("body") or "").strip()
    pdf, _ = _save_file(request.files.get("pdf"), ALLOWED_PDF)
    if not body and not pdf:
        flash("Write your solution or attach a PDF.", "error")
        return redirect(url_for("problem_view", pid=pid))

    verdict = _answers_match(body, p.answer)  # None / True / False
    s = Submission(problem_id=pid, user_id=current_user.id, body=body, pdf=pdf,
                   is_correct=bool(verdict))
    db.session.add(s); db.session.commit()

    if verdict is True:
        if not p.solved_by(current_user.id):
            db.session.add(ProblemSolve(user_id=current_user.id, problem_id=pid))
            db.session.commit()
            _award_points(current_user, POINTS_CORRECT_SOLVE)
            flash(f"✅ Correct! Solution verified — +{POINTS_CORRECT_SOLVE} points. Marked complete.", "success")
        else:
            flash("✅ Correct again! (already counted)", "success")
    elif verdict is False:
        flash("❌ Not correct yet — this problem stays incomplete. Try again.", "error")
    else:
        flash("Solution posted. (This problem has no auto-check; a reviewer can confirm it.)", "info")

    if p.created_by and p.created_by != current_user.id:
        notify(p.created_by, f"{current_user.full_name} submitted a solution to “{p.title}”",
               link=url_for("problem_view", pid=pid), kind="editorial",
               email_subject="New solution on your problem")
    return redirect(url_for("problem_view", pid=pid) + "#editorial")


@app.route("/submission/<int:sid>/delete", methods=["POST"])
@login_required
def submission_delete(sid):
    s = Submission.query.get_or_404(sid)
    if s.user_id != current_user.id:
        abort(403)
    pid = s.problem_id
    if s.pdf:
        try:
            os.remove(os.path.join(UPLOAD_DIR, s.pdf))
        except OSError:
            pass
    db.session.delete(s); db.session.commit()
    flash("Your answer was deleted.", "info")
    return redirect(url_for("problem_view", pid=pid) + "#editorial")


@app.route("/problem/<int:pid>/editorial/unlock", methods=["POST"])
@login_required
def editorial_unlock(pid):
    p = Problem.query.get_or_404(pid)
    if not p.unlocked_by(current_user.id):
        db.session.add(EditorialUnlock(user_id=current_user.id, problem_id=pid))
        db.session.commit()
        _award_points(current_user, POINTS_EDITORIAL_UNLOCK)
        flash(f"Editorial unlocked — {abs(POINTS_EDITORIAL_UNLOCK)} points deducted.", "info")
    return redirect(url_for("problem_view", pid=pid) + "#editorial")


@app.route("/problem/<int:pid>/discuss", methods=["POST"])
@login_required
def problem_discuss(pid):
    p = Problem.query.get_or_404(pid)
    body = (request.form.get("body") or "").strip()
    image, _ = _save_file(request.files.get("image"), ALLOWED_IMG)
    if not body and not image:
        flash("Type a message or attach an image.", "error")
        return redirect(url_for("problem_view", pid=pid) + "#discussion")
    db.session.add(DiscussionMessage(problem_id=pid, user_id=current_user.id, body=body, image=image))
    db.session.commit()
    participants = {p.created_by} if p.created_by else set()
    participants |= {mm.user_id for mm in p.messages}
    for uid in participants:
        if uid and uid != current_user.id:
            notify(uid, f"{current_user.full_name} replied in the discussion on “{p.title}”",
                   link=url_for("problem_view", pid=pid) + "#discussion", kind="discussion",
                   email_subject="New discussion reply on M³")
    return redirect(url_for("problem_view", pid=pid) + "#discussion")


@app.route("/discussion/<int:mid>/edit", methods=["POST"])
@login_required
def discussion_edit(mid):
    msg = DiscussionMessage.query.get_or_404(mid)
    if msg.user_id != current_user.id:
        abort(403)
    body = (request.form.get("body") or "").strip()
    if not body and not msg.image:
        flash("Message can't be empty.", "error")
        return redirect(url_for("problem_view", pid=msg.problem_id) + "#discussion")
    msg.body = body
    msg.edited = True
    db.session.commit()
    return redirect(url_for("problem_view", pid=msg.problem_id) + "#discussion")


@app.route("/discussion/<int:mid>/delete", methods=["POST"])
@login_required
def discussion_delete(mid):
    msg = DiscussionMessage.query.get_or_404(mid)
    if msg.user_id != current_user.id:
        abort(403)
    pid = msg.problem_id
    if msg.image:
        try:
            os.remove(os.path.join(UPLOAD_DIR, msg.image))
        except OSError:
            pass
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("problem_view", pid=pid) + "#discussion")


# ---------------------------------------------------------------- posts / feed
@app.route("/post/new", methods=["POST"])
@login_required
def post_new():
    body = (request.form.get("body") or "").strip()
    stored, original = _save_file(request.files.get("attachment"), ALLOWED_ATTACH)
    if not body and not stored:
        flash("Write something or attach a file to post.", "error")
        return redirect(url_for("dashboard"))
    db.session.add(Post(user_id=current_user.id, kind="note", body=body,
                        attachment=stored, attachment_name=original))
    db.session.commit()
    if stored:
        notify_all_except(current_user.id, f"{current_user.full_name} shared a file on the feed",
                          link=url_for("dashboard"), kind="post")
    return redirect(url_for("dashboard"))


@app.route("/post/<int:post_id>/edit", methods=["POST"])
@login_required
def post_edit(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    new_body = (request.form.get("body") or "").strip()
    post.body = new_body
    post.edited = True
    db.session.commit()
    flash("Post updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    if post.attachment:
        try:
            os.remove(os.path.join(UPLOAD_DIR, post.attachment))
        except OSError:
            pass
    db.session.delete(post); db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("dashboard"))


@app.route("/post/<int:post_id>/reply", methods=["POST"])
@login_required
def post_reply(post_id):
    post = Post.query.get_or_404(post_id)
    body = (request.form.get("body") or "").strip()
    if body:
        db.session.add(PostReply(post_id=post_id, user_id=current_user.id, body=body))
        db.session.commit()
        if post.user_id != current_user.id:
            notify(post.user_id, f"{current_user.full_name} replied to your post",
                   link=url_for("dashboard"), kind="post",
                   email_subject="New reply to your post on M³")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------- profile
@app.route("/profile")
@login_required
def profile():
    my_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).limit(10).all()
    return render_template("profile.html", user=current_user, my_posts=my_posts, medals=sorted(MEDALS))


@app.route("/profile/edit", methods=["POST"])
@login_required
def profile_edit():
    current_user.first_name = (request.form.get("first_name") or current_user.first_name).strip()
    current_user.last_name = (request.form.get("last_name") or current_user.last_name).strip()
    new_email = (request.form.get("email") or "").strip().lower()
    if new_email and new_email != current_user.email:
        if User.query.filter(User.email == new_email, User.id != current_user.id).first():
            flash("That email is already in use.", "error"); return redirect(url_for("profile"))
        current_user.email = new_email
    photo, _ = _save_file(request.files.get("photo"), ALLOWED_IMG)
    if photo:
        current_user.photo = photo
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("profile"))


# ---------------------------------------------------------------- notifications
@app.route("/notifications")
@login_required
def notifications():
    notes = (Notification.query.filter_by(user_id=current_user.id)
             .order_by(Notification.created_at.desc()).limit(100).all())
    return render_template("notifications.html", notes=notes)


@app.route("/notifications/read")
@login_required
def notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(request.referrer or url_for("notifications"))


# ---------------------------------------------------------------- number game
@app.route("/number-game")
@login_required
def number_game():
    return render_template("number_game.html")


@app.route("/api/number-game/question")
@login_required
def api_number_game_question():
    return jsonify(number_game_question(request.args.get("level", "easy")))


def _best_scores(level, duration):
    glob = (db.session.query(db.func.max(NumberGameScore.score))
            .filter_by(level=level, duration=duration).scalar()) or 0
    personal = (db.session.query(db.func.max(NumberGameScore.score))
                .filter_by(level=level, duration=duration, user_id=current_user.id).scalar()) or 0
    return int(glob), int(personal)


@app.route("/api/number-game/best")
@login_required
def api_number_game_best():
    level = request.args.get("level", "easy")
    duration = int(request.args.get("duration", 60) or 60)
    g, p = _best_scores(level, duration)
    return jsonify({"global": g, "personal": p})


@app.route("/api/number-game/score", methods=["POST"])
@login_required
def api_number_game_score():
    data = request.get_json(silent=True) or {}
    score = int(data.get("score", 0))
    level = data.get("level", "easy")
    duration = int(data.get("duration", 60) or 60)
    db.session.add(NumberGameScore(user_id=current_user.id, score=score,
                                   level=level, duration=duration))
    db.session.commit()
    g, p = _best_scores(level, duration)
    return jsonify({"ok": True, "global": g, "personal": p})


# ---------------------------------------------------------------- feedback
@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        body = (request.form.get("body") or "").strip()
        if not body:
            flash("Please write your feedback.", "error"); return redirect(url_for("feedback"))
        db.session.add(Feedback(user_id=current_user.id,
                                rating=int(request.form.get("rating", 5) or 5),
                                category=request.form.get("category", "general"), body=body))
        db.session.commit()
        flash("Thanks for the feedback!", "success")
        return redirect(url_for("feedback"))
    items = Feedback.query.order_by(Feedback.created_at.desc()).limit(50).all()
    return render_template("feedback.html", items=items)


@app.route("/feedback/<int:fid>/edit", methods=["POST"])
@login_required
def feedback_edit(fid):
    fb = Feedback.query.get_or_404(fid)
    if fb.user_id != current_user.id:
        abort(403)
    body = (request.form.get("body") or "").strip()
    if not body:
        flash("Feedback can't be empty.", "error")
        return redirect(url_for("feedback"))
    fb.body = body
    fb.rating = int(request.form.get("rating", fb.rating) or fb.rating)
    fb.category = request.form.get("category", fb.category)
    db.session.commit()
    flash("Feedback updated.", "success")
    return redirect(url_for("feedback"))


@app.route("/feedback/<int:fid>/delete", methods=["POST"])
@login_required
def feedback_delete(fid):
    fb = Feedback.query.get_or_404(fid)
    if fb.user_id != current_user.id:
        abort(403)
    db.session.delete(fb)
    db.session.commit()
    flash("Feedback deleted.", "info")
    return redirect(url_for("feedback"))


@app.route("/feedback/<int:fid>/reply", methods=["POST"])
@login_required
def feedback_reply(fid):
    fb = Feedback.query.get_or_404(fid)
    body = (request.form.get("body") or "").strip()
    if body:
        db.session.add(FeedbackReply(feedback_id=fid, user_id=current_user.id, body=body))
        db.session.commit()
        if fb.user_id != current_user.id:
            notify(fb.user_id, f"{current_user.full_name} replied to your feedback",
                   link=url_for("feedback"), kind="feedback",
                   email_subject="New reply to your feedback on M³")
    return redirect(url_for("feedback"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


with app.app_context():
    db.create_all()
    seed_content.seed(app)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
