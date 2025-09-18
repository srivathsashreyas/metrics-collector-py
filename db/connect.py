import redis
import os


def get_redis_conn():
    host = "localhost" if "REDIS_HOST" not in os.environ else os.environ["REDIS_HOST"]
    port = "6379" if "REDIS_PORT" not in os.environ else os.environ["REDIS_PORT"]
    r = redis.Redis(host=host, port=port, decode_responses=True)
    return r
