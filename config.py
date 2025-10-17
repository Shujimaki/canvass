import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "canvassisnotass")
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
 