#!/usr/bin/env python

import unittest
import requests
import time
import redis
import redis_session

class TestLimiters(unittest.TestCase):
    
    def setUp(self):
        r = redis.StrictRedis(db = 0)
        r.flushdb()
    
    def _test_limiter(self, url, times, expires):
        s = requests.Session()
        codes = [res.status_code for res in [s.get(url) for i in range(times+1)]]
        for code in codes:
            self.assertEqual(code,requests.codes.ok)
        self.assertEqual(s.get(url).status_code, requests.codes.forbidden)
        time.sleep(expires)
        self.assertEqual(s.get(url).status_code, requests.codes.ok)
    
    def test_url_query_limiter(self):
        self._test_limiter("http://127.0.0.1:8888/url_query_test?api_key=1", 3, 7)
        
    def test_ip_limiter(self):
        self._test_limiter("http://127.0.0.1:8888/ip_test", 5,3)
        
    def test_and_op(self):
        self._test_limiter("http://127.0.0.1:8888/and_test?api_key=1", 3, 3)
        
    def test_ip_blocking(self):
        url = "http://127.0.0.1:8888/ip_test"
        self.assertEqual(requests.get(url).status_code, requests.codes.ok)
        for i in range(3):
            self.assertEqual(requests.get(url).status_code, requests.codes.forbidden)
        
        time.sleep(redis_session.BLOCK_IP_EXPIRE_TIME)
        self.assertEqual(requests.get(url).status_code, requests.codes.ok)
        
        
if __name__ == '__main__':
    unittest.main()
        