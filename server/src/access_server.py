import math
import psycopg2 as pg

import datetime
import os
from dotenv import load_dotenv
import tornado
import tornado.web

import json

from src.authentication import BaseHandler
from src.database import DB_CONFIG

load_dotenv()

secret = os.environ["SECRET"]
last_set_time = datetime.datetime.fromtimestamp(0)
last_short_code = ''

try:
    env = os.environ["ENV"]
except Exception:
    env = "dev"


def db_execute_command(sql_query, parameters):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, parameters)

                conn.commit()
                msg = "Record successfully added"
    except Exception:
        msg = "error in insert operation"
    finally:
        return msg


class SetPrintWindow(BaseHandler):
    '''verifies if a user can print,
    if yes a print window of default 1 min is opened'''

    def post(self):
        try:
            msg = "SUCCESS"

            data = json.loads(self.request.body)
            print(data, secret)
            if data.get('secret') != secret:
                print("secret incorrect")
                self.finish("incorrect key")
                msg = "FAILURE"
                return
            print("ok")
            id = data.get('id').upper().strip().split(" ")
            id = "".join([bit_val.zfill(2) for bit_val in id])
            id = id.zfill(8)
            # window = data.get('window')
            # if window is None:
            window = 60

            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM public.access WHERE id=%s AND canprint=\'TRUE\'", (id,))  # noqa: E501
                    print("executed")

                    if cur is not None and cur.fetchone()[0] > 0:
                        print("CHECK TIME")
                        global last_set_time, last_short_code
                        last_set_time = datetime.datetime.now() + datetime.timedelta(seconds=int(window))  # noqa: E501

                        cur.execute(
                            "SELECT shortcode FROM public.access WHERE id=%s AND canprint=\'TRUE\'", (id,))  # noqa: E501
                        last_short_code = cur.fetchone()[0]
                        print(last_short_code)

                    else:
                        msg = "FAILURE"
        except Exception:
            msg = "FAILURE"

        print(msg)
        self.write(msg)


class GetPrintWindow(BaseHandler):
    '''queries if the print window is open, returns true if open'''

    def get(self):
        try:
            status = last_set_time > datetime.datetime.now()
            self.write(str(status))

        except Exception:
            self.write("Error in get message")


class PrintMetrics(BaseHandler):
    '''Saves metrics for a singe print job'''

    def parse_to_int(self, s: str) -> int:
        '''Expects the time to be in in seconds (float)'''
        return math.ceil(float(s))

    def post(self):
        data = json.loads(self.request.body)
        # print(data)

        print_time = self.parse_to_int(data.get('time').strip())
        print_weight = self.parse_to_int(data.get('weight').strip())
        printer_name = data.get('name').strip()

        print(print_time, print_weight, printer_name, last_short_code)
        self.write(db_execute_command("INSERT INTO public.print_metrics (shortcode, print_duration, print_weight, printer_name) VALUES (%s,%s,%s,%s)",  # noqa: E501
                   (last_short_code, print_time, print_weight, printer_name)))
        # print(data)

        return
