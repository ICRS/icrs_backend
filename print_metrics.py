import sqlite3
import datetime
import os
import tornado
import json
from tornado_swagger.model import register_swagger_model

try:
    env = os.environ["ENV"]
except:
    env = "dev"

DATABASE = "/home/pi/code/icrs_security/database.db" if env != "dev" else "database.db"

@register_swagger_model
class PrintStatistics(tornado.web.RequestHandler):
    """
    ----
    type: object
    description: Print Statistics representation
    properties:
    """    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        """
        ---
        tags:
        - Get
        summary: Get Print Statistic details
        description: Print Statistic details from a start date
        produces:
        - application/json
        parameters:
        -   name: start_time
            description: start time of query
            required: true
            type: string
            format: date
        responses:
            200:
              description: list of shortcodes, print durations and print weight
        """
        start_time = self.get_argument("start_time", default="1980-01-01")
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute("SELECT SHORTCODE, SUM(PRINT_DURATION), SUM(PRINT_WEIGHT) FROM PRINT_METRICS WHERE TIME_STARTED > ? GROUP BY SHORTCODE", (start_time,))
            self.write(json.dumps([{ "shortcode" : c[0], "print_duration": c[1], "print_weight": c[2]} for c in cur.fetchall()]))
        

