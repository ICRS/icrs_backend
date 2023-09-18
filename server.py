import tornado
from access_server import addUser, setUserCanPrint, setPrintWindow, getPrintWindow


def make_app():
    return tornado.web.Application([
        (r"/addUser", addUser,),
        (r"/setUserCanPrint", setUserCanPrint),
        (r"/setCanPrint", setPrintWindow),
        (r"/setPrintWindow", setPrintWindow),
        (r"/getPrintWindow", getPrintWindow),
    ])
