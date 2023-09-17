import tornado
from access_server import create_table
from server import make_app


if __name__ == "__main__":
    create_table()
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()