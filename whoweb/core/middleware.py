import json
import logging
from functools import partial

from django.http import HttpResponse, HttpResponseServerError
from promise import is_thenable
from sentry_sdk import capture_exception

from .loaders import Loaders

probe_logger = logging.getLogger("probes")
logger = logging.getLogger(__name__)


class HealthCheckMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if request.method == "GET":
            if request.path == "/readiness":
                return self.readiness(request)
            elif request.path == "/liveness":
                return self.liveness(request)
        return self.get_response(request)

    def liveness(self, request):
        """
        Returns that the server is alive.
        """
        return HttpResponse("OK")

    def readiness(self, request):
        # Connect to each database
        try:
            from django.db import connection

            connection.ensure_connection()
        except Exception as e:
            probe_logger.exception(e)
            return HttpResponseServerError("db: cannot connect to database.")

        # Call get_stats() to connect to each memcached instance and get it's stats.
        # This can effectively check if each is online.
        try:
            from django.core.cache import caches
            from django_redis.cache import RedisCache

            for cache in caches.all():
                if isinstance(cache, RedisCache):
                    cache.get(None)
        except Exception as e:
            probe_logger.exception(e)
            return HttpResponseServerError("cache: cannot connect to cache.")

        return HttpResponse("OK")


class LoaderMiddleware(object):
    def resolve(self, next, root, info, **args):
        if not hasattr(info.context, "loaders"):
            info.context.loaders = Loaders()
        return next(root, info, **args)


class DebugMiddleware(object):
    def on_error(self, error, info):
        return
        # self.log_request_body(info)

    def resolve(self, next, root, info, **args):
        return next(root, info, **args).catch(partial(self.on_error, info=info))

    @staticmethod
    def log_request_body(info):
        body = info.context._body.decode("utf-8")
        try:
            json_body = json.loads(body)
            logging.debug(
                " User: %s \n Action: %s \n Variables: %s \n Body: %s",
                info.context.user,
                json_body["operationName"],
                json_body["variables"],
                json_body["query"],
            )
        except:
            logging.debug(body)


class SentryMiddleware(object):
    """
    Properly capture errors during query execution and send them to Sentry.
    Then raise the error again and let Graphene handle it.
    """

    def on_error(self, error):
        capture_exception(error)
        raise error

    def resolve(self, next, root, info, **args):
        return next(root, info, **args).catch(self.on_error)
