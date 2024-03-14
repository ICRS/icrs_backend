import tornado
from src.authentication import LoginHandler, MainHandler
from src.access_server import (
    AddUser,
    GetAllInducted,
    SetUserCanPrint,
    GetMetrics,
    UpdateUser,
    RegisterUsers,
    SetPrintWindow,
    GetPrintWindow,
    GetValidUsers,
    GetUserPerms,
    PrintMetrics,
    GetUserPermsFromShortCode,
)
from src.print_metrics import PrintStatistics
from tornado_swagger.setup import setup_swagger

import base64
import uuid


class Application(tornado.web.Application):
    _routes = [
        tornado.web.url(r"/addUser", AddUser),
        tornado.web.url(r"/updateUser", UpdateUser),
        tornado.web.url(r"/setCanPrint", SetUserCanPrint),
        tornado.web.url(r"/setPrintWindow", SetPrintWindow),
        tornado.web.url(r"/getPrintWindow", GetPrintWindow),
        tornado.web.url(r"/registerUsers", RegisterUsers),
        tornado.web.url(r"/getValidUsers", GetValidUsers),
        tornado.web.url(r"/getUserPerms", GetUserPerms),
        tornado.web.url(r"/postPrintTime", PrintMetrics),
        tornado.web.url(r"/printStatistics", PrintStatistics),
        tornado.web.url(r"/getMetrics", GetMetrics),
        tornado.web.url(r"/getAllInducted", GetAllInducted),
        tornado.web.url(r"/user/perms", GetUserPermsFromShortCode),
        tornado.web.url(r"/login", LoginHandler),
        tornado.web.url(r"/", MainHandler),
    ]

    def __init__(self):
        setup_swagger(self._routes)
        cookie_secret = str(base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes))
        settings = {
            "cookie_secret": cookie_secret,
            "login_url": "/login",
            # "xsrf_cookies": True,
        }
        super(Application, self).__init__(self._routes, **settings)


def make_app():
    return Application()
