import requests
import hashlib
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
        key = self.user._cache_key("assignments", self.user.base_url, str(self.id), self.user._token_hash())
        cached = cache.get(key)
        if cached is not None:
            return [Assignment(self, a) for a in cached]

        # include params handling if needed (affects cache key)
        path = f"/courses/{self.id}/assignments"
        data = self.user._get(path, params=params)
        cache.set(key, data, timeout=timeout)
        return [Assignment(self, a) for a in data]


class Assignment:
    def __init__(self, course, data):
        self.course = course
        self.id = data["id"]
        self.name = data["name"]
        self.due_at = data.get("due_at")




