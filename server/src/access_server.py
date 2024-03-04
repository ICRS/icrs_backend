import psycopg2 as pg

import datetime
import os
from dotenv import load_dotenv
import tornado
import json

from src.database import DB_CONFIG

load_dotenv()
import math

secret = os.environ["SECRET"]
last_set_time = datetime.datetime.fromtimestamp(0)
last_short_code = ''

try:
    env = os.environ["ENV"]
except:
    env = "dev"

if env == "dev":
    import src.union_mock as union
else:
    import src.union as union

def db_execute_command(sql_query, parameters):
    try:
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, parameters)

                conn.commit()
                msg = "Record successfully added"    
    except:
        msg = "error in insert operation"
    finally:
        return msg

class AddUser(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*") # TODO: remove wildcard
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST')

    '''adds a user to db with given ID and perms'''
    def post(self):
        try:
            data = json.loads(self.request.body)

            if data.get('secret') != secret:
                self.set_status(403)
                self.finish("Not Authorised!")
                return "incorrect key"
            
            ID = data.get('id').upper().strip().replace(" ","")
            SHORTCODE = data.get('shortcode').lower()
            ISMEMBER = "TRUE" if union.isMember(SHORTCODE) is True else "FALSE"
           
            self.write(db_execute_command("INSERT INTO public.access (id, shortcode, valid) VALUES (%s,%s,%s)", (ID, SHORTCODE, ISMEMBER)))
            self.write("Is Member: " + ISMEMBER)

            canPrint = None
            canLaserCut = None
            try:
                canPrint = bool(data.get("canPrint"))
            except:
                pass
            try:
                canLaserCut = bool(data.get("canLaserCut"))
            except:
                pass

            if canPrint is not None:
                db_execute_command("UPDATE public.access SET canprint=%s WHERE valid=\'TRUE\' AND id=%s", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE public.access SET canlasercut=%s WHERE valid=\'TRUE\' AND id=%s", (str(canLaserCut).upper(), ID))


        except Exception as e:
            self.finish("ERROR in post message:"+str(e))

class RegisterUsers(tornado.web.RequestHandler):
    '''sets users to valid if they have membership'''
    def get(self):
        try:
            update = [c[0] for c in cur.fetchall()]
            update = union.is_member_list(update)
        
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT shortcode From public.access WHERE valid=\'FALSE\' OR valid=0")
                    
                    set_valid_by_shortcode = "UPDATE public.access SET valid=\'TRUE\', canprint=\'TRUE\' WHERE shortcode=%s"
                    cur.executemany(set_valid_by_shortcode, [(c,) for c in update])
                    
                    conn.commit()
        
                    msg = "Successfully Registered Users"
        except Exception as e:
            print(e)
            msg = "FAILURE"
        finally:
            print(msg)
            self.write(msg)


class UpdateUser(tornado.web.RequestHandler):
    '''updates user perms'''
    # TODO: remove this endpoint
    def post(self):
        self.write("OK")

class SetUserCanPrint(tornado.web.RequestHandler):
    '''sets the canPrint status for a given user'''
    def post(self):
        try:
            data = json.loads(self.request.body)

            # TODO: FIX THIS
            canPrint = bool(data.get("canPrint"))
            canLaserCut = bool(data.get("canLaserCut"))
            
            if data.get('secret') != secret:
                self.finish("incorrect key")
                return
            
            ID = data.get('id')
            #print(data)
            if canPrint is not None:
                db_execute_command("UPDATE public.access SET canprint=%s WHERE valid=\'TRUE\' AND id=%s", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE public.access SET canlasercut=%s WHERE valid=\'TRUE\' AND id=%s", (str(canLaserCut).upper(), ID))

        except:
            self.finish("Error in post message")
            return

        self.finish("SUCCESS")
        return
 

class SetPrintWindow(tornado.web.RequestHandler):
    '''verifies if a user can print, if yes a print window of default 1 min is opened'''
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
            ID = data.get('id').upper().strip().replace(" ","")
            #window = data.get('window')
            #if window is None:
            window = 60

            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM public.access WHERE id=%s AND canprint=\'TRUE\'", (ID,))
                    print("executed")

                    if cur is not None and cur.fetchone()[0] > 0:
                        print("CHECK TIME")
                        global last_set_time, last_short_code
                        last_set_time = datetime.datetime.now() + datetime.timedelta(seconds=int(window))
                        
                        cur.execute("SELECT shortcode FROM public.access WHERE id=%s AND canprint=\'TRUE\'",(ID,))
                        last_short_code = cur.fetchone()[0]
                        print(last_short_code)

                    else:
                        msg = "FAILURE"
        except:
            msg = "FAILURE"
        
        print(msg)
        self.write(msg)
        

class GetPrintWindow(tornado.web.RequestHandler):
    '''queries if the print window is open, returns true if open'''
    def get(self):
        try:            
            status = last_set_time > datetime.datetime.now()
            self.write(str(status))

        except:
            self.write("Error in post message")


class GetValidUsers(tornado.web.RequestHandler):
    def getValidNameCIDs(self):
        try:
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT shortcode FROM public.access A WHERE valid=\'TRUE\' AND NOT EXISTS (SELECT \'X\' FROM public.sent S WHERE A.shortcode=S.shortcode)")

                    update = [c[0] for c in cur.fetchall()]
        
                    mapping = union.getShortcodesToCIDAndName(update)
                    
                    cur.executemany("INSERT INTO public.sent (shortcode) VALUES (%s)", [(c,) for c in update])
                    return mapping
        except:
            print("Error somewhere in here")
            
    def get(self):
        try:
            self.write(str(self.getValidNameCIDs()))
        
        except:
            self.write("ERROR")

class GetUserPerms(tornado.web.RequestHandler):
    def get(self):
        return self.post()

    def post(self):
        data = json.loads(self.request.body)
        uid = data.get('id').strip().replace(" ","")
        if data.get('secret') != secret:
                print("secret incorrect")
                self.finish("incorrect key")
                msg = "FAILURE"
                self.write(msg)
                return
        
        try:
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM public.access WHERE id=%s",(uid,))
                    result = cur.fetchall()
                    if not result:
                        result = {}
                    else:
                        result = result[0]
                        result = {'shortcode':result[1],'print':result[2],'laser':result[3],'inducted':result[4]}
                    self.write(result)
        except Exception as e:
            self.write(e.message,e.args)

class PrintMetrics(tornado.web.RequestHandler):
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
        self.write(db_execute_command("INSERT INTO public.print_metrics (shortcode, print_duration, print_weight, printer_name) VALUES (%s,%s,%s,%s)", (last_short_code, print_time, print_weight, printer_name)))
        # print(data)

        return

class GetMetrics(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        shortcode = data['shortcode'].lower()
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM public.print_metrics WHERE shortcode=%s", (shortcode,))
                prints = cur.fetchall()
                # out = {"prints":prints}
                self.write(json.dumps(prints, default=str))
                return
