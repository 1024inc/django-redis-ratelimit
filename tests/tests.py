from django.conf.urls import url
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.views import View
from unittest.mock import MagicMock, patch

from redis_ratelimit import ratelimit
from redis_ratelimit.exceptions import RateLimited
from redis_ratelimit.utils import parse_rate
from redis_ratelimit.decorators import (
    ignore_redis_errors,
    is_rate_limited,
    redis_connection,
)
from redis.exceptions import TimeoutError

factory = RequestFactory()


def make_request(view):
    class DynamicUrlPattern:
        urlpatterns = [url(r'', view)]

    with override_settings(ROOT_URLCONF=DynamicUrlPattern):
        req = factory.get('/')
        view(req)


class RateParsingTests(TestCase):
    def test_rate_parsing(self):
        tests = (
            ('100/s', (100, 1)),
            ('100/10s', (100, 10)),
            ('100/m', (100, 60)),
            ('400/10m', (400, 10 * 60)),
            ('600/h', (600, 60 * 60)),
            ('800/d', (800, 24 * 60 * 60)),
        )

        for input, output in tests:
            assert output == parse_rate(input)


class DecoratorTests(TestCase):
    def test_no_rate(self):
        @ratelimit()
        def view(request):
            return True

        req = factory.get('/')
        assert view(req)


class RedisTests(TestCase):
    def setUp(self):
        self.redis = redis_connection()

    def test_existing_key_gets_expiry(self):
        key = 'REDIS_RATELIMIT/127.0.0.1/tests.tests.view/500/60'
        self.redis.delete(key)
        self.redis.set(key, 20)

        @ratelimit(rate='500/m')
        def view(request):
            return True

        make_request(view)

        self.assertEqual(self.redis.ttl(key), 60)

    def test_new_key_gets_expiry(self):
        key = 'REDIS_RATELIMIT/127.0.0.1/tests.tests.view/500/60'
        self.redis.delete(key)

        @ratelimit(rate='500/m')
        def view(request):
            return True

        make_request(view)

        self.assertEqual(self.redis.ttl(key), 60)


class RateLimitTests(TestCase):
    def test_method_decorator(self):
        @ratelimit(rate='5/s')
        def view(request):
            return True

        for _ in range(5):
            make_request(view)

        with self.assertRaises(RateLimited):
            make_request(view)

    def test_cbv_decorator(self):
        class Cbv(View):
            @ratelimit(rate='5/s')
            def get(self, request):
                return True

        class DynamicUrlPattern:
            urlpatterns = [url(r'', Cbv.as_view())]

        with override_settings(ROOT_URLCONF=DynamicUrlPattern):
            for _ in range(5):
                req = factory.get('/')
                Cbv.as_view()(req)

            with self.assertRaises(RateLimited):
                req = factory.get('/')
                Cbv.as_view()(req)


class IgnoreRedisErrorsTest(TestCase):
    def test_invokes_function(self):
        @ignore_redis_errors
        def fake_rate_limited():
            return True

        assert fake_rate_limited()

    def test_error(self):
        @ignore_redis_errors
        def fake_rate_limited():
            raise TimeoutError

        assert fake_rate_limited() == False
