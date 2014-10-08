import tornado.ioloop
import tornado.web
import ratelimit
from redis_session import session_required

api_key_limiter = ratelimit.RateLimitType(name = "apikey",
                                times = 3,
                                expire = 7,
                                get_data_func = lambda h: h.get_argument("api_key"))


ip_limiter = ratelimit.RateLimitType(name = "ip",
                           times = 5,
                           expire = 3,
                           get_data_func = lambda h: h.request.remote_ip)

api_and_ip = ratelimit.AndRateLimitType(api_key_limiter, ip_limiter)

class APIKeyHandler(tornado.web.RequestHandler):  
    @session_required
    @ratelimit.limit_by(api_key_limiter)
    def get(self, **kargs):
        pass
        

class IPHandler(tornado.web.RequestHandler):
    @session_required
    @ratelimit.limit_by(ip_limiter)
    def get(self, **kargs):
        pass

class IPAndKeyHandler(tornado.web.RequestHandler):
    @session_required
    @ratelimit.limit_by(api_and_ip)
    def get(self, **kargs):
        pass
        

application = tornado.web.Application([
    (r"/url_query_test$", APIKeyHandler),
    (r"/ip_test$", IPHandler),
    (r"/and_test$", IPAndKeyHandler),
], autoreload=True)


if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()