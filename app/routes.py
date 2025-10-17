from flask import Blueprint, render_template, jsonify
from .models import User

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return render_template("index.html")

@bp.route("/details", methods=["GET", "POST"])
def details():
    print (f"request method is {request.method}")
    if request.method == "POST":
        try:
            canvas_url = request.form.get("canvas_url")
            access_token = request.form.get("access_token")
            user = User(canvas_url, access_token)
        except Exception:
            return render_template("index.html")
    
    else:
        print("User found!")
    
    profile = user._get_profile()
    courses = user._get_courses()
    assignments = {course.name: [course._get_assignments()] for course in courses}
    time = datetime.now(ZoneInfo(profile.time_zone))

    # TODO: fix get_due_assignments
    due_asses = get_due_assignments(14)
    return render_template("details.html", base=COURSE_ENDPOINT_FORMAT, profile=profile, courses=user_courses, due_asses=due_asses, time=time)

# TODO: persist user across sessions and routes
@bp.route("/profile", methods=["POST"])
def profile():
    profile = user._get_profile()
    return render_template("profile.html", profile=profile)

@bp.route("/courses", methods=["POST"])
def courses():
    courses = user._get_courses()
    return render_template("courses.html", courses=courses, base=USER_ENDPOINT_FORMAT)

@bp.route("/assignments", methods=["POST"])
def assignments():
    assignments = user._
    return render_template("assignments.html")


@app.route("/set_timezone", methods = ["POST"])
def set_timezone():
    data = request.get_json()
    tz = data.get("timezone")

    if not tz:
        return jsonify({"success": False, "error": "No timezone provided"}), 400
    
    session["timezone"] = tz

    return jsonify({"success": True, "timezone": tz}), 200