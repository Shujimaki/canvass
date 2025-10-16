import requests
import os
from datetime import datetime, timezone, timedelta
from flask import Flask, has_request_context, jsonify, render_template, request, session
from flask_caching import Cache
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = "300"
app.secret_key = os.getenv("SECRET_KEY", "canvass is not ass")
cache = Cache(app)



USER_CANVAS_BASE = os.getenv("CANVAS_BASE")
USER_CANVAS_ACCESS_TOKEN = os.getenv("CANVAS_ACCESS_TOKEN")
COURSE_ENDPOINT_FORMAT = f"{USER_CANVAS_BASE}/api/v1"
USER_ENDPOINT_FORMAT = f"{USER_CANVAS_BASE}/api/v1/users/self"

user_courses = []

def make_canvas_cache_key(*args, **kwargs):
    if has_request_context():
        base = f"{request.path}"
        print(f"BASE = {base}")
        if "canvas_url" in session:
            base += f"_{session['canvas_url']}"
        if "access_token" in session:
            base += f"_{hash(session['access_token'])}"
        return base
    return "no_request_context"

def save_credentials():
    global COURSE_ENDPOINT_FORMAT, USER_ENDPOINT_FORMAT, USER_CANVAS_ACCESS_TOKEN
    COURSE_ENDPOINT_FORMAT = f"{session["canvas_url"]}/api/v1"
    USER_ENDPOINT_FORMAT = f"{session["canvas_url"]}/api/v1/users/self"
    USER_CANVAS_ACCESS_TOKEN = session["access_token"]

# TODO: Cache get functions

# TODO: store all courses details
@cache.cached(timeout=60*60*1, key_prefix=make_canvas_cache_key)
def get_paginated_courses(params=None):
    return canvas_api_paginated_get(USER_ENDPOINT_FORMAT, "/courses", params=params)

@cache.cached(timeout=60*60*6, key_prefix=make_canvas_cache_key)
def get_profile(params=None):
    return canvas_api_get(USER_ENDPOINT_FORMAT, "/profile")

# TODO: store all assignments details
@cache.cached(timeout=60*15, key_prefix=make_canvas_cache_key)
def get_paginated_assignments(course_id, params = None):
    return canvas_api_paginated_get(COURSE_ENDPOINT_FORMAT, f"/courses/{course_id}/assignments", params=params)


def load_all_courses(request_path = None):
    request.path = "/courses"
    params = {
        "include[]": ["term", "sections", "enrollments"],
        "enrollment_state": "active",
        "per_page": 100
    }

    user_tz = get_user_timezone()
    now = datetime.now(user_tz)
    print(now)


    data = get_paginated_courses(params)
    print(f"data = {data}")
    for c in data:
        print(f"C = {c}")
        term = c.get("term", {})
        enrollments = c.get("enrollments", [])

        start_at = term.get("start_at")
        end_at = term.get("end_at")

        if start_at and end_at:
            start_at = datetime.fromisoformat(start_at.replace("Z","+00:00")).astimezone(user_tz)
            end_at = datetime.fromisoformat(end_at.replace("Z","+00:00")).astimezone(user_tz)

            if start_at <= now <= end_at:
                user_courses.append({"id": c.get("id"), "name": c.get("name")})
    
    if request_path:
        request.path = request_path
    
    print(f"usercourses = {user_courses}")

def load_assignments(request_path = None):
    params = {
        "include[]": ["submission"]
    }
    
    for course in user_courses:
        request.path = f"{course['id']}/assignments"
        print(f"asscourse = {course}")
        course["assignments"] = []

        data = get_paginated_assignments(course_id = course['id'], params = params)
        for c in data:
            print(f"assign: {c.get("name")}")
            course["assignments"].append({"name": c.get("name"), "due_at": c.get("due_at")})
            
    if request_path:
        request.path = request_path
            
def get_due_assignments(max_days=7):
# TODO: display due assignments with specified number of days
    user_tz = get_user_timezone()
    now = datetime.now(user_tz)
    due_asses = {}

    for i in range(0, max_days + 1):
        due_date = now.date() + timedelta(days=i)
        print(f"Due for {due_date}")
        due_asses[due_date] = {}

        for course in user_courses:
            due_asses[due_date][course["name"]] = []

            for ass in course["assignments"]:
                due_at_string = ass["due_at"]

                if due_at_string is None:
                    continue

                due_at = datetime.fromisoformat(ass["due_at"].replace("Z","+00:00")).astimezone(user_tz)

                if due_at.date() == due_date:
                    print(ass["name"])
                    due_asses[due_date][course["name"]].append(ass["name"])
    return due_asses


"""
    TODO: 
        Sort Per-day assignments per course (subject)
        Do caching (full data of courses and assignments) --> done via SimpleCache
        Do rate limiting (Flask-Limiter) --> next
"""

def get_user_timezone():
    tz_name = session.get("timezone", "Asia/Manila")
    return ZoneInfo(tz_name)


def canvas_api_get(base_format, path, params=None):
    url = f"{base_format}{path}"
    headers = {
        "Authorization": f"Bearer {USER_CANVAS_ACCESS_TOKEN}"
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def canvas_api_paginated_get(base_format, path, params=None):
    url = f"{base_format}{path}"
    headers = {
        "Authorization": f"Bearer {USER_CANVAS_ACCESS_TOKEN}"
    }
    all_data = []

    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        all_data.extend(r.json())

        if "next" in r.links:
            url = r.links["next"]["url"]
        else:
            url = None
        params = None
    
    return all_data

@app.template_filter("format_date")
def format_date(value, fmt="%B %d, %Y"):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime(fmt)
    except Exception:
        return value


@app.route("/set_timezone", methods = ["POST"])
def set_timezone():
    data = request.get_json()
    tz = data.get("timezone")

    if not tz:
        return jsonify({"success": False, "error": "No timezone provided"}), 400
    
    session["timezone"] = tz

    return jsonify({"success": True, "timezone": tz}), 200

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/details", methods=["GET", "POST"])
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
    session
    user_tz = get_user_timezone()
    time = datetime.now(user_tz)
    print(time)
    profile = get_profile(params = None)
    # also get the courses
    load_all_courses(request.path)
    load_assignments(request.path)
    due_asses = get_due_assignments(14)
    return render_template("details.html", base=COURSE_ENDPOINT_FORMAT, profile=profile, courses=user_courses, due_asses=due_asses, time=time)

@app.route("/profile", methods=["POST"])
def profile():
    profile = get_profile(params = None)
    return render_template("profile.html", profile=profile)

@app.route("/courses", methods=["POST"])
def courses():
    user_courses.clear()
    load_all_courses(request.path)
    return render_template("courses.html", courses=user_courses, base=USER_ENDPOINT_FORMAT)

@app.route("/assignments", methods=["POST"])
def assignments():
    return render_template("assignments.html")



if __name__ == "__main__":
    app.run(debug = True)