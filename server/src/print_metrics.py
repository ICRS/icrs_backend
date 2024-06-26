import tornado
import json
from tornado_swagger.model import register_swagger_model
import psycopg2 as pg

from src.database import DB_CONFIG


@register_swagger_model
class PrintStatistics(tornado.web.RequestHandler):
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
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT SHORTCODE, SUM(PRINT_DURATION), SUM(PRINT_WEIGHT) FROM PRINT_METRICS WHERE TIME_STARTED > %s GROUP BY SHORTCODE", (start_time,))  # noqa: E501
                self.write(json.dumps(
                    [{
                        "shortcode": c[0],
                        "print_duration": c[1],
                        "print_weight": c[2]} for c in cur.fetchall()]))
