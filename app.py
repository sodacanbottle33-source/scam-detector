from flask import Flask, request, render_template, redirect
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Scan
from ai_engine import analyze_message

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"

db.init_app(app)

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- HOME (FIX FOR 404) ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=request.form["password"]
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("signup.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result = None

    if request.method == "POST":
        msg = request.form["message"]
        result = analyze_message(msg)

        scan = Scan(
            message=msg,
            score=result["score"],
            level=result["level"],
            user_id=current_user.id
        )

        db.session.add(scan)
        db.session.commit()

    scans = Scan.query.filter_by(user_id=current_user.id).all()

    return render_template("dashboard.html", result=result, scans=scans)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)