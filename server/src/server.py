import tornado
from src.authentication import LoginHandler
from src.access_server import (
    SetPrintWindow,
    GetPrintWindow,
    PrintMetrics
)
from tornado_swagger.setup import setup_swagger

import base64
import uuid


class Application(tornado.web.Application):
    _routes = [
        tornado.web.url(r"/setPrintWindow", SetPrintWindow),
        tornado.web.url(r"/getPrintWindow", GetPrintWindow),
        tornado.web.url(r"/postPrintTime", PrintMetrics),
        tornado.web.url(r"/login", LoginHandler),
    ]

    def __init__(self):
        setup_swagger(self._routes)
        cookie_secret = str(base64.b64encode(
            uuid.uuid4().bytes + uuid.uuid4().bytes))
        settings = {
            "cookie_secret": cookie_secret,
            "login_url": "/login",
            # "xsrf_cookies": True,
        }
        super(Application, self).__init__(self._routes, **settings)


def make_app():
    return Application()
