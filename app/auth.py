import uuid
import json
from datetime import datetime
from .extensions import redis_client

class TokenManager:
    @staticmethod
    def create_token(user, profile, courses, assignments) -> str:
        token = uuid.uuid4().hex

        user_data = {
            'canvas_url': user.base_url,
            'access_token': user.access_token,
            'profile': {
                'name': profile.name,
                'avatar': profile.avatar,
                'email': profile.email,
                'time_zone': profile.time_zone 
            }
            'courses': [{
                'id': course.id,
                'name': course.name,
                'term': course.term,
                'enrollments': course.enrollments,
                'assignments': assignments[course.name]
            } for course in courses],
            'created_at': datetime.now().isoformat()
        }

        redist_client.setex(
            f'user_token:{token}',
            60 * 60 * 24,
            json.dumps(user_data)
        )

        return token

    @staticmethod
    def get_user_data(token: str) -> dict:
        if not token:
            return None

        data = redis_client.get(f"user_token{token}")
        if not data:
            return None
        
        return json.loads(data)