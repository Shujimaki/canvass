from flask import Blueprint, render_template, jsonify, request, g, make_response
from datetime import datetime
from zoneinfo import ZoneInfo
from .models import User, Profile, Course
from .auth import TokenManager

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

            profile = user._get_profile()
            courses = user._get_courses()
            
            for course in courses:
                course.assignments = course._get_assignments()
            # assignments are fetched when creating token
            # assignments = {course.name: course._get_assignments() for course in courses}

            token = TokenManager.create_token(user, profile, courses)

            resp = make_response(render_template(
                "details.html",
                profile=profile,
                courses=courses,
                time=datetime.now(ZoneInfo(profile.time_zone))
            ))
            resp.set_cookie('auth_token', token,
                        max_age=60*60*24*30,
                        httponly=True, secure=True)
            return resp

        except Exception as e:
            print(f"Error: {e}")
            return render_template("index.html")
    
    token = request.cookies.get('auth_token')
    if not token:
        print(f"No Token!")
        return render_template("index.html")

    data = TokenManager.get_user_data(token)
    if not data:
        print("No Data!")
        return render_template("index.html")
    
    return render_template(
        "details.html",
        profile=data["profile"],
        courses=data["courses"],
        time=datetime.now(ZoneInfo(data['profile']['time_zone']))
    )

    # TODO: fix get_due_assignments
    # due_asses = get_due_assignments(14)

# TODO: persist user across sessions and routes
@bp.route("/profile", methods=["POST"])
def profile():
    token = request.cookies.get('auth_token')
    if not token:
        print("No token!")
        return render_template("index.html")

    data = TokenManager.get_user_data(token)

    if not data:
        return render_template("index.html")
    
    return render_template("profile.html", profile=data['profile'])

@bp.route("/courses", methods=["POST"])
def courses():
    token = request.cookies.get('auth_token')
    if not token:
        print("No token!")
        return render_template("index.html")

    data = TokenManager.get_user_data(token)

    if not data:
        return render_template("index.html")
    
    return render_template("courses.html", courses=data['courses'])

@bp.route("/assignments", methods=["POST"])
def assignments():
    token = request.cookies.get('auth_token')
    if not token:
        print("No token!")
        return render_template("index.html")

    data = TokenManager.get_user_data(token)

    if not data:
        return render_template("index.html")

    assignments_by_course = {
        course['name']: course['assignments']
        for course in data['courses']
    }
    
    return render_template(
        "assignments.html", 
        assignments=assignments_by_course
        )



@bp.route("/set_timezone", methods = ["POST"])
def set_timezone():
    data = request.get_json()
    tz = data.get("timezone")

    if not tz:
        return jsonify({"success": False, "error": "No timezone provided"}), 400
    
    session["timezone"] = tz

    return jsonify({"success": True, "timezone": tz}), 200