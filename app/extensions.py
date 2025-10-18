from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

cache = Cache()
limiter = Limiter(key_func=get_remote_address)
redis_client = redis.Redis(host="localhost", port=6379, db=0)