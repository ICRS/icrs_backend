import tornado
from access_server import addUser, updateUser, getRegistrationPortal, registerUsers, setUserCanPrint, setPrintWindow, getPrintWindow, getValidUsers, getUserPerms, printMetrics
from print_metrics import PrintStatistics
from tornado_swagger.setup import setup_swagger

class Application(tornado.web.Application):
    _routes = [
        tornado.web.url(r"/addUser", addUser,),
        tornado.web.url(r"/updateUser", updateUser),
        tornado.web.url(r"/setCanPrint", setPrintWindow),
        tornado.web.url(r"/setPrintWindow", setPrintWindow),
        tornado.web.url(r"/getPrintWindow", getPrintWindow),
        tornado.web.url(r"/getRegistrationPortal", getRegistrationPortal),
        tornado.web.url(r"/registerUsers", registerUsers),
        tornado.web.url(r"/getValidUsers", getValidUsers),
        tornado.web.url(r"/getUserPerms", getUserPerms),
        tornado.web.url(r"/postPrintTime", printMetrics),
        tornado.web.url(r"/printStatistics", PrintStatistics),    
    ]

    def __init__(self):
        setup_swagger(self._routes)
        super(Application, self).__init__(self._routes)

def make_app():
    return Application()
