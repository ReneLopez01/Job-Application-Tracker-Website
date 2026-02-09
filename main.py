from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# configure sql alchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
# creating db for app
db = SQLAlchemy(app)

# Create a database model for each user ,


class User(db.Model):
    # class's variables ( table columns will have id , user, password)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    applications = db.relationship("Application", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Application(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company = db.Column(db.String(30), nullable=False)
    jobTitle = db.Column(db.String(30), nullable=False)
    salary = db.Column(db.Float(precision=2), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    applicationStatus = db.Column(db.String(30), nullable=False)
    date = db.Column(db.Date, nullable=False)


# routes


@app.route("/")
def home():
    if "username" in session:
        # if username is logged in / registered redirect to dashboard
        return redirect(url_for('dashboard'))
    # else return index.html which is the login/register form
    return render_template("index.html")

# dashboard


@app.route("/dashboard")
def dashboard():
    if "username" in session:
        page = request.args.get('page', 1, type=int)

        user = User.query.filter_by(username=session["username"]).first()

        apps_pagination = Application.query.filter_by(
            user_id=user.id
        ).order_by(Application.id.desc()).paginate(page=page, per_page=250)

        return render_template("dashboard.html",
                               username=session['username'],
                               applications=apps_pagination)
    return redirect(url_for("home"))


@app.route("/add_application", methods=["POST"])
def add_application():
    # Get data from the form
    original_date = request.form.get("application-date")
    user = User.query.filter_by(username=session["username"]).first()
    new_app = Application(
        company=request.form.get("company"),
        jobTitle=request.form.get("jobTitle"),
        salary=float(request.form.get("salary", 0)),
        location=request.form.get("location"),
        applicationStatus=request.form.get("select-status"),
        date=datetime.strptime(original_date, "%Y-%m-%d").date(),
        user_id=user.id
    )
    db.session.add(new_app)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route("/delete_application/<int:app_id>", methods=["POST"])
def delete_application(app_id):
    app_to_delete = Application.query.get_or_404(app_id)
    db.session.delete(app_to_delete)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route("/login", methods=['POST'])
def login():
    # collect info from form
    if request.form["username"] == "":
        return render_template("index.html", error="Please enter a Username/Password")
    if request.form["password"] == "":
        return render_template("index.html", error="Please enter a Username/Password")
    else:
        username = request.form['username']
        password = request.form["password"]

    user = User.query.filter_by(username=username).first()
    # check if its in db
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        # other wise show home page
        return render_template("index.html", error="We Couldnt find your Account")

    # register


@app.route('/users')
def list_users():
    page = request.args.get('page', 1, type=int)

    users_pagination = User.query.order_by(
        User.id.desc()).paginate(page=page, per_page=250)

    return render_template('users.html', users=users_pagination)


@app.template_filter("mmddyyyy")  # jinja method
def format_mmddyyyy(value):
    if value is None:
        return ""
    return value.strftime("%m-%d-%Y")


@app.template_filter("dollar")  # jinja method
def format_Salary(value):
    if value == 0:
        return "Unpaid"

    try:
        return f"{value:,.0f}"
    except (TypeError, ValueError):
        return value


@app.route("/register", methods=['POST'])
def register():
    if request.form["username"] == "":
        return render_template("index.html", error="Please enter a Username/Password")
    if request.form["password"] == "":
        return render_template("index.html", error="Please enter a Username/Password")
    else:
        username = request.form['username']
        password = request.form["password"]

    user = User.query.filter_by(username=username).first()

    if user:
        return render_template("index.html", error="User already here")
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))


# logout
@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


if __name__ in "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
