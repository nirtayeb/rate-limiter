#!/usr/bin/env python
import redis

g_redis = redis.StrictRedis(db = 0)

class RateLimitType:
    def __init__(self, name, times, expire, get_data_func=lambda h: None):
        self.name = name
        self.times = times
        self.expire_at = expire
        self.get_data_func = get_data_func

    def server_name(self, request):
            return "l_%s:%s" % (self.name, self.get_data_func(request))

    def check(self, request):
        times = g_redis.get(self.server_name(request))
        print "rule",self.times, "db", times
        return times != None and int(times) > self.times
    
    def change(self, request):
        name = self.server_name(request)
        current = g_redis.get(name)
        if current is not None:
            g_redis.incr(name)
        else:
            g_redis.set(name, 1, self.expire_at)


class AndRateLimitType(RateLimitType):
    def __init__(self, first, other):
        name = "%s & %s" % (first.name, other.name)
        times = min(first.times, other.times)
        expire_at = min(first.expire_at, other.expire_at)
        RateLimitType.__init__(self, name, times, expire_at)
        self.first = first
        self.other = other
        
    def server_name(self, request):
        return "(%s)&(%s)" % (self.first.server_name(request), self.other.server_name(request))
        
class OrRateLimitType(RateLimitType):
    def __init__(self, first, other):
        name = "%s | %s" % (first.name, other.name)
        times = max(first.times, other.times)
        expire_at = max(first.expire_at, other.expire_at)
        RateLimitType.__init__(self, name, times, expire_at)
        self.first = first
        self.other = other
        
    def server_name(self, request):
        return "(%s)|(%s)" % (self.first.server_name(request), self.other.server_name(request))

def limit_exceed(handler):
    handler.set_status(403)
    handler.write("Limits exceed")

def limit_by(limiter):
    def rate_limiter_decorator(func):
        def func_wrapper(self, *args, **kargs):
            if not limiter.check(self):
                limiter.change(self)
                return func(self, *args, **kargs)
            limit_exceed(handler)
        return func_wrapper
    return rate_limiter_decorator