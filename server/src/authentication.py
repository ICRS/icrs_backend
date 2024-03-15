import base64
import tornado
import os

from dotenv import load_dotenv

load_dotenv()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_signed_cookie("icrs")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        print("HI")
        self.write("Hello World")
        return

users = {
    "icrs": os.getenv("SECRET"),
}

class LoginHandler(BaseHandler):
    # def get(self):
    #     self.write("Please login")
        # self.redirect("/login")
        # return
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*") # TODO: remove wildcard
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header('Access-Control-Allow-Methods', '*')

    def post(self):
        auth_header = self.request.headers.get('Authorization')
        print(auth_header, users)
        auth_type, auth_data = auth_header.split(' ', 1)
        if auth_type.lower() == 'basic':
            decoded_auth_data = str(base64.decodebytes(auth_data.encode("utf-8")), 'ascii')
            print(decoded_auth_data)
            username, password = decoded_auth_data.split(':', 1)
    #             # Check if username and password match
            print(username, password)
            print(users)
            if username in users and users.get(username) == password:
                print("ok")
                self.set_signed_cookie(username, username)
                # self.redirect("/")
                print("done")
                return 
            else:
                self.set_status(401)
                self.write("Unauthorized")
                return
