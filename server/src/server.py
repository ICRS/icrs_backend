import tornado
from src.access_server import (
    AddUser,
    SetUserCanPrint,
    getMetrics,
    UpdateUser,
    getRegistrationPortal,
    RegisterUsers,
    setPrintWindow,
    getPrintWindow,
    getValidUsers,
    getUserPerms,
    printMetrics,
)
from src.print_metrics import PrintStatistics
from tornado_swagger.setup import setup_swagger


class Application(tornado.web.Application):
    _routes = [
        tornado.web.url(r"/addUser",AddUser),
        tornado.web.url(r"/updateUser", UpdateUser),
        tornado.web.url(r"/setCanPrint", SetUserCanPrint),
        tornado.web.url(r"/setPrintWindow", setPrintWindow),
        tornado.web.url(r"/getPrintWindow", getPrintWindow),
        tornado.web.url(r"/getRegistrationPortal", getRegistrationPortal),
        tornado.web.url(r"/registerUsers", RegisterUsers),
        tornado.web.url(r"/getValidUsers", getValidUsers),
        tornado.web.url(r"/getUserPerms", getUserPerms),
        tornado.web.url(r"/postPrintTime", printMetrics),
        tornado.web.url(r"/printStatistics", PrintStatistics),    
        tornado.web.url(r"/getMetrics", getMetrics),
    ]

    def __init__(self):
        setup_swagger(self._routes)
        super(Application, self).__init__(self._routes)


def make_app():
    return Application()
