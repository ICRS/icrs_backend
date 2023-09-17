import tornado
from access_server import addUser, setUserCanPrint, setCanPrint


def make_app():
    return tornado.web.Application([
        (r"/addUser", addUser,),
        (r"/setUserCanPrint", setUserCanPrint),
        (r"/setCanPrint", setCanPrint),
    ])
