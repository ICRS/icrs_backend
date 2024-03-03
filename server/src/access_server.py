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
        conn.rollback()
        msg = "error in insert operation"
    finally:
        conn.close()
        return msg

class AddUser(tornado.web.RequestHandler):
    '''adds a user to db with given ID and perms'''
    def post(self):
        try:
            data = json.loads(self.request.body)

            if data.get('secret') != secret:
                self.set_status(403)
                self.finish("Not Authorised!")
                return "incorrect key"
            
            ID = data.get('id').upper()
            SHORTCODE = data.get('shortcode').lower()
            ISMEMBER = "TRUE" if union.isMember(SHORTCODE) is True else "FALSE"
           
            self.write(db_execute_command("INSERT INTO public.access (ID, SHORTCODE, VALID) VALUES (%s,%s,%s)", (ID, SHORTCODE, ISMEMBER)))
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
                db_execute_command("UPDATE public.access SET CANPRINT=%s WHERE VALID=\'TRUE\' AND ID=%s", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE public.access SET CANLASERCUT=%s WHERE VALID=\'TRUE\' AND ID=%s", (str(canLaserCut).upper(), ID))


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
                    cur.execute("SELECT SHORTCODE From public.access WHERE VALID=\'FALSE\' OR VALID=0")
                    
                    set_valid_by_shortcode = "UPDATE public.access SET VALID=\'TRUE\', CANPRINT=\'TRUE\' WHERE SHORTCODE=%s"
                    cur.executemany(set_valid_by_shortcode, [(c,) for c in update])
                    
                    conn.commit()
        
                    msg = "Successfully Registered Users"
        except Exception as e:
            print(e)
            conn.rollback()
            msg = "FAILURE"
        finally:
            conn.close()
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
            canPrint = bool(data.get("canPrint"))
            canLaserCut = bool(data.get("canLaserCut"))
            
            if data.get('secret') != secret:
                self.finish("incorrect key")
                return
            
            ID = data.get('id')
            #print(data)
            if canPrint is not None:
                db_execute_command("UPDATE public.access SET CANPRINT=%s WHERE VALID=\'TRUE\' AND ID=%s", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE public.access SET CANLASERCUT=%s WHERE VALID=\'TRUE\' AND ID=%s", (str(canLaserCut).upper(), ID))

        except:
            self.finish("Error in post message")
            return

        self.finish("SUCCESS")
        return
 

class setPrintWindow(tornado.web.RequestHandler):
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
            ID = data.get('id').upper().replace(" ","")
            #window = data.get('window')
            #if window is None:
            window = 60

            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Count() From public.access WHERE ID=%s AND CANPRINT=\'TRUE\'", (ID,))
                    print(cur)

                    if cur is not None and cur.fetchone()[0] > 0:
                        print("CHECK TIME")
                        global last_set_time, last_short_code
                        last_set_time = datetime.datetime.now() + datetime.timedelta(seconds=int(window))
                        last_short_code = cur.execute("SELECT SHORTCODE FROM public.access WHERE ID=%s AND CANPRINT=\'TRUE\'",(ID,)).fetchall()[0][0]

                    else:
                        msg = "FAILURE"
        except:
            msg = "FAILURE"
        
        print(msg)
        self.write(msg)
        

class getPrintWindow(tornado.web.RequestHandler):
    '''queries if the print window is open, returns true if open'''
    def get(self):
        try:            
            status = last_set_time > datetime.datetime.now()
            self.write(str(status))

        except:
            self.write("Error in post message")


class getRegistrationPortal(tornado.web.RequestHandler):
    def get(self):
        self.render("template.html")


class getValidUsers(tornado.web.RequestHandler):
    def getValidNameCIDs(self):
        try:
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT SHORTCODE FROM public.access A WHERE VALID=\'TRUE\' AND NOT EXISTS (SELECT \'X\' FROM SENT S WHERE A.SHORTCODE=S.SHORTCODE)")

                    update = [c[0] for c in cur.fetchall()]
        
                    mapping = union.getShortcodesToCIDAndName(update)
                    
                    cur.executemany("INSERT INTO SENT (SHORTCODE) VALUES (%s)", [(c,) for c in update])
                    return mapping
        except:
            conn.rollback()
        finally:
            conn.close()
            
    def get(self):
        try:
            self.write(str(self.getValidNameCIDs()))
        
        except:
            self.write("ERROR")

class getUserPerms(tornado.web.RequestHandler):
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
                    cur.execute("SELECT * From public.access WHERE ID=%s",(uid,))
                    result = cur.fetchall()[0]
                    result = {'shortcode':result[1],'print':result[2],'laser':result[3],'inducted':result[4]}
                    self.write(result)
        except Exception as e:
            self.write(e.message,e.args)
        finally:
            conn.close()

class printMetrics(tornado.web.RequestHandler):
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
        self.write(db_execute_command("INSERT INTO PRINT_METRICS (SHORTCODE, PRINT_DURATION, PRINT_WEIGHT, PRINTER_NAME) VALUES (%s,%s,%s,%s)", (last_short_code, print_time, print_weight, printer_name)))
        # print(data)

        return

class getMetrics(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        shortcode = data['shortcode'].lower()
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * From PRINT_METRICS WHERE SHORTCODE=%s", (shortcode,))
                prints = cur.fetchall()
                out = {"prints":prints}
                self.write(out)
                return
