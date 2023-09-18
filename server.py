import tornado
from access_server import addUser, updateUser, setPrintWindow, getPrintWindow


def make_app():
    return tornado.web.Application([
        (r"/addUser", addUser,),
        (r"/updateUser", updateUser),
        (r"/setCanPrint", setPrintWindow),
        (r"/setPrintWindow", setPrintWindow),
        (r"/getPrintWindow", getPrintWindow),
    ])
