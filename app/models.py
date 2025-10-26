import requests
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.extensions import cache

# add caching
# transfer functions from app.py
# transfer templates to app/
# test

class User:
    def __init__(self, base_url, access_token):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def _get(self, path, params=None):
        url = f"{self.base_url}/api/v1{path}"
        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def _token_hash(self):
        # stable, non-reversible key material for cache keys
        return hashlib.sha256(self.access_token.encode("utf-8")).hexdigest()[:16]

    def _cache_key(self, *parts):
        return "models:" + ":".join(parts)

    def _get_profile(self, timeout=60*60):
        key = self._cache_key("profile", self.base_url, self._token_hash())
        cached = cache.get(key)
        if cached is not None:
            return Profile(self, cached)

        data = self._get("/users/self/profile")
        cache.set(key, data, timeout=timeout)
        return Profile(self, data)

    def _get_courses(self, timeout=60*60):
        key = self._cache_key("courses", self.base_url, self._token_hash())
        cached = cache.get(key)
        if cached is not None:
            return [Course(self, c) for c in cached]

        data = self._get("/courses?enrollment_state=active")
        cache.set(key, data, timeout=timeout)
        return [Course(self, c) for c in data]

    def get_due_assignments(self, max_days=7, timeout=60*10):
        key = self._cache_key("due_assignments", self.base_url, self._token_hash(), str(max_days))
        cached = cache.get(key)
        if cached is not None:
            return {
                datetime.fromisoformat(date_str).date(): course_assignments
                for date_str, course_assignments in cached.items()
            }
        

        profile = self._get_profile()
        user_tz = ZoneInfo(profile.time_zone)
        now = datetime.now(user_tz)

        due_assignments = {}
        for i in range(max_days + 1):
            due_date = (now + timedelta(days=i)).date()
            due_assignments[due_date] = {}
    
        courses = self._get_courses()
        for course in courses:
            assignments = course._get_assignments()

            for ass in assignments:
                if not ass.due_at:
                    continue

                due_date = datetime.fromisoformat(ass.due_at.replace('Z', '+00:00')).astimezone(user_tz).date()

                if now.date() <= due_date <= (now + timedelta(days=max_days)).date():
                    if course.name not in due_assignments[due_date]:
                        due_assignments[due_date][course.name] = []
                    
                    assignment_data = {
                        'id': ass.id,
                        'name': ass.name,
                        'due_at': ass.due_at
                    }

                    due_assignments[due_date][course.name].append(assignment_data)
        
        cache_data = {
            date.isoformat(): course_assignments
            for date, course_assignments in due_assignments.items()
        }
        cache.set(key, cache_data, timeout=timeout)

        return due_assignments

class Profile:
    def __init__(self, user, data):
        self.user = user
        self.name = data["name"]
        self.avatar = data["avatar_url"]
        self.email = data["primary_email"]
        self.time_zone = data["time_zone"]


class Course:
    def __init__(self, user, data):
        self.user = user
        self.id = data["id"]
        self.name = data["name"]
        self.term = data.get("term", {})
        self.enrollments = data.get("enrollments", [])
        self.assignments = data.get("assignments", [])

    def _get_assignments(self, timeout=60*15, params=None):
        # include params in the cache key so different query params don't collide
        params_key = str(params) if params else ""
        key = self.user._cache_key("assignments", self.user.base_url, str(self.id), self.user._token_hash(), params_key)
        cached = cache.get(key)
        if cached is not None:
            return [Assignment(self, a) for a in cached]
 
        # include params handling if needed (affects cache key)
        path = f"/courses/{self.id}/assignments"

        # Canvas API is paginated. Use the User._get method with page/per_page params
        # and iterate until no more results.
        all_data = []
        page = 1
        per_page = 100
        while True:
            page_params = dict(params) if params else {}
            page_params.update({"page": page, "per_page": per_page})
            page_data = self.user._get(path, params=page_params)
            if not page_data:
                break

            all_data.extend(page_data)

            # if fewer than per_page results returned, we've reached the last page
            if len(page_data) < per_page:
                break

            page += 1

        cache.set(key, all_data, timeout=timeout)
        return [Assignment(self, a) for a in all_data]

class Assignment:
    def __init__(self, course, data):
        self.course = course
        self.id = data["id"]
        self.name = data["name"]
        self.due_at = data.get("due_at")




