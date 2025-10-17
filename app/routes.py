from flask import Blueprint, render_template, jsonify
from .models import User

bp = Blueprint("main", __name__)

@app.route("/")
def home():
    return render_template("index.html")

@bp.route("/details", methods=["GET", "POST"])
def details():
    print (f"request method is {request.method}")
    if request.method == "POST":
        session["canvas_url"] = request.form.get("canvas_url").rstrip("/")
        session["access_token"] = request.form.get("access_token")
        save_credentials()
        

    else:
        print(f"session url = {session["canvas_url"]}")
        print(session["access_token"])
    
    user_courses.clear()
    user_tz = get_user_timezone()
    time = datetime.now(user_tz)
    print(time)
    profile = get_profile(params = None)
    # also get the courses
    load_all_courses(request.path)
    load_assignments(request.path)
    due_asses = get_due_assignments(14)
    return render_template("details.html", base=COURSE_ENDPOINT_FORMAT, profile=profile, courses=user_courses, due_asses=due_asses, time=time)

@bp.route("/profile", methods=["POST"])
def profile():
    profile = get_profile(params = None)
    return render_template("profile.html", profile=profile)

@bp.route("/courses", methods=["POST"])
def courses():
    user_courses.clear()
    load_all_courses(request.path)
    return render_template("courses.html", courses=user_courses, base=USER_ENDPOINT_FORMAT)

@bp.route("/assignments", methods=["POST"])
def assignments():
    return render_template("assignments.html")