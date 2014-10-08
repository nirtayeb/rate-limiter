import redis
import os
import uuid

BLOCK_IP_EXPIRE_TIME = 60
FIRST_TIME_EXPIRE_BEFORE_GETTING_SID = 60
SESSION_ID_EXPIRE_TIME = 100


g_redis = redis.StrictRedis(db = 0)
        
def generate_sid():
    return str(uuid.uuid4())

def is_ip_blocked(ip):
    return g_redis.get("blocked:%s" % ip) != None

def block_ip(ip):
    g_redis.set("blocked:%s" % ip, ip, ex=BLOCK_IP_EXPIRE_TIME)

def add_first_time(ip):
    return g_redis.set("first:%s" % ip, ip, ex=FIRST_TIME_EXPIRE_BEFORE_GETTING_SID)

def is_first_time(ip):
    return g_redis.get("first:%s" % ip) == None

def is_sid_expired(sid):
    return g_redis.get("sid:%s" % sid) == None

def extend_sid_expiration(sid):
    g_redis.set("sid:%s", sid, ex=SESSION_ID_EXPIRE_TIME)


def session_required(func):
    def func_wrapper(self, *args, **kargs):
        # Check if user already generated session id and not already blocked
        # so he couldn't DDos our redis 
        ip = self.request.remote_ip
        if "sid" not in self.request.cookies:
            if not is_first_time(ip) or is_ip_blocked(ip):
                block_ip(ip)
                self.set_status(403)
                self.write("Please enable cookies and try again in later")
                return
            else:
                self.set_cookie("sid", generate_sid())
                add_first_time(ip)

        # Check if sid is not expired or exists in our db and not fake
        sid = self.get_cookie("sid")
        if not is_sid_expired(sid):
            self.set_status(403)
            self.write("Your session is expired")
            return
        
        extend_sid_expiration(sid)
        return func(self, *args, **kargs)
    return func_wrapper