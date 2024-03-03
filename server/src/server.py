import tornado
from src.access_server import (
    AddUser,
    SetUserCanPrint,
    GetMetrics,
    UpdateUser,
    GetRegistrationPortal,
    RegisterUsers,
    SetPrintWindow,
    GetPrintWindow,
    GetValidUsers,
    GetUserPerms,
    PrintMetrics,
)
from src.print_metrics import PrintStatistics
from tornado_swagger.setup import setup_swagger


class Application(tornado.web.Application):
    _routes = [
        tornado.web.url(r"/addUser",AddUser),
        tornado.web.url(r"/updateUser", UpdateUser),
        tornado.web.url(r"/setCanPrint", SetUserCanPrint),
        tornado.web.url(r"/setPrintWindow", SetPrintWindow),
        tornado.web.url(r"/getPrintWindow", GetPrintWindow),
        tornado.web.url(r"/getRegistrationPortal", GetRegistrationPortal),
        tornado.web.url(r"/registerUsers", RegisterUsers),
        tornado.web.url(r"/getValidUsers", GetValidUsers),
        tornado.web.url(r"/getUserPerms", GetUserPerms),
        tornado.web.url(r"/postPrintTime", PrintMetrics),
        tornado.web.url(r"/printStatistics", PrintStatistics),
        tornado.web.url(r"/getMetrics", GetMetrics),
    ]

    def __init__(self):
        setup_swagger(self._routes)
        super(Application, self).__init__(self._routes)


def make_app():
    return Application()
