import base64
import tornado
import os

from dotenv import load_dotenv

load_dotenv()

users = {
    "icrs": os.getenv("SECRET"),
}

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_signed_cookie("icrs")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        print("HI")
        self.write("Hello World")
        return

class LoginHandler(BaseHandler):
    def post(self):
        auth_header = self.request.headers.get('Authorization')
        print(auth_header, users)
        auth_type, auth_data = auth_header.split(' ', 1)
        if auth_type.lower() == 'basic':
            decoded_auth_data = str(base64.decodebytes(auth_data.encode("utf-8")), 'ascii')
            username, password = decoded_auth_data.split(':', 1)

            if username in users and users.get(username) == password:
                self.set_signed_cookie(username, username)
            else:
                self.set_status(401)
                self.write("Unauthorized")
        else:
            self.set_status(403)