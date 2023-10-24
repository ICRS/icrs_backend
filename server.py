import tornado
from access_server import addUser, updateUser, getRegistrationPortal, registerUsers, setUserCanPrint, setPrintWindow, getPrintWindow, getValidUsers, getUserPerms

def make_app():
    return tornado.web.Application([
        (r"/addUser", addUser,),
        (r"/updateUser", updateUser),
        (r"/setCanPrint", setPrintWindow),
        (r"/setPrintWindow", setPrintWindow),
        (r"/getPrintWindow", getPrintWindow),
        (r"/getRegistrationPortal", getRegistrationPortal),
        (r"/registerUsers", registerUsers),
        (r"/getValidUsers", getValidUsers),
        (r"/getUserPerms", getUserPerms),
    ])
