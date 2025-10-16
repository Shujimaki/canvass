import requests

class CanvasUser:
    def __init__(self, base_url, access_token):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def _get(self, path, params=None):
        url = f"{self.base_url}/api/v1{path}"
        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def get_profile(self):
        return self._get("/users/self/profile")

    def get_courses(self):
        data = self._get("/courses?enrollment_state=active")
        return [CanvasCourse(self, c) for c in data]


class CanvasCourse:
    def __init__(self, user, data):
        self.user = user
        self.id = data["id"]
        self.name = data["name"]
        self.term = data.get("term", {})
        self.enrollments = data.get("enrollments", [])

    def get_assignments(self):
        return [CanvasAssignment(self, a)
            for a in self.user._get(f"/courses/{self.id}/assignments")]


class CanvasAssignment:
    def __init__(self, course, data):
        self.course = course
        self.id = data["id"]
        self.name = data["name"]
        self.due_at = data.get("due_at")




