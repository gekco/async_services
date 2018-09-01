
import redis

from config.redis_settings import MASTER_PREFIX, REDIS_HOST, REDIS_PORT, REDIS_DB,REDIS_PASSWORD


class RedisConnection(object):

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, prefix="", strict_redis=False, password = REDIS_PASSWORD):
        self.prefix = MASTER_PREFIX + prefix
        self.connection = redis.Redis(host=host, port=port, db=db,password=password)
        if strict_redis:
            self.sconnection = redis.StrictRedis(host=host, port=port, db=db,password=password)

    def set(self, key, value, prefix=""):
        prefix = self.prefix + prefix
        self.connection.set('{0}{1}'.format(prefix, key), value)

    def rpush(self, key, value, prefix=""):
        prefix = self.prefix + prefix
        self.connection.rpush('{0}{1}'.format(prefix, key), value)

    def get(self, key, prefix=""):
        prefix = self.prefix + prefix
        return self.connection.get('{0}{1}'.format(prefix, key))

    def lrange(self, key, n, prefix=""):
        prefix = self.prefix + prefix
        return self.connection.lrange('{0}{1}'.format(prefix, key), -n, -1)

    def lrange2(self, key, a, b , prefix=""):
        prefix = self.prefix + prefix
        return self.connection.lrange('{0}{1}'.format(prefix, key), a, b)

    def list_keys(self, prefix):
        prefix = self.prefix + prefix
        return [ i.decode('utf-8').replace(prefix, "")for i in self.sconnection.keys(pattern=prefix+"*")]

    def lpop(self, key, prefix = ""):
        prefix = self.prefix + prefix
        return self.connection.lpop('{0}{1}'.format(prefix, key))

    def delete(self, key, prefix = ""):
        prefix = self.prefix + prefix
        return self.connection.delete('{0}{1}'.format(prefix, key) )

    def ltrim(self, key, start, stop ,prefix =""):
        prefix = self.prefix + prefix
        return self.connection.ltrim('{0}{1}'.format(prefix, key), start, stop)


