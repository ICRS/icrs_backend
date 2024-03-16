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

class AddUser(BaseHandler):
    '''adds a user to db with given ID and perms'''

    @tornado.web.authenticated
    def post(self):
        try:
            data = json.loads(self.request.body)
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

            self.write(db_execute_command("INSERT INTO Access (ID, VALID) VALUES (?,?)", (ID, "TRUE")))

        except Exception as e:
            self.finish("ERROR in post message:"+str(e))

class RegisterUsers(BaseHandler):
    '''sets users to valid if they have membership'''
    def get(self):
        try:
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT shortcode From public.access WHERE valid=\'FALSE\' OR valid=\'0\'")

                    update = [c[0] for c in cur.fetchall()]
                    update = union.is_member_list(update)
                    
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


class UserMachinePermissions(BaseHandler):
    '''sets the canPrint status for a given user'''
    @tornado.web.authenticated
    def post(self):
        try:
            data = json.loads(self.request.body)

            # TODO: FIX THIS
            canPrint = bool(data.get("canPrint"))
            canLaserCut = bool(data.get("canLaserCut"))    
            
            if "id" in data:
                id = data.get('id')
            
                if canPrint is not None:
                    db_execute_command("UPDATE public.access SET canprint=%s WHERE valid=\'TRUE\' AND id=%s", (str(canPrint).upper(), id))
                if canLaserCut is not None:
                    db_execute_command("UPDATE public.access SET canlasercut=%s WHERE valid=\'TRUE\' AND id=%s", (str(canLaserCut).upper(), id))

            if "shortcode" in data:
                shortcode = data.get("shortcode")
                if canPrint is not None:
                    db_execute_command("UPDATE public.access SET canprint=%s WHERE valid=\'TRUE\' AND shortcode=%s", (str(canPrint).upper(), shortcode))
                if canLaserCut is not None:
                    db_execute_command("UPDATE public.access SET canlasercut=%s WHERE valid=\'TRUE\' AND shortcode=%s", (str(canLaserCut).upper(), shortcode))
                
        except:
            self.finish("Error in post message")
            return

        self.finish("SUCCESS")
        return
 

class SetPrintWindow(BaseHandler):
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
            id = data.get('id').upper().strip().replace(" ","")
            id = id.zfill(8)
            #window = data.get('window')
            #if window is None:
            window = 60

            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM public.access WHERE id=%s AND canprint=\'TRUE\'", (id,))
                    print("executed")

                    if cur is not None and cur.fetchone()[0] > 0:
                        print("CHECK TIME")
                        global last_set_time, last_short_code
                        last_set_time = datetime.datetime.now() + datetime.timedelta(seconds=int(window))
                        
                        cur.execute("SELECT shortcode FROM public.access WHERE id=%s AND canprint=\'TRUE\'",(id,))
                        last_short_code = cur.fetchone()[0]
                        print(last_short_code)

                    else:
                        msg = "FAILURE"
        except:
            msg = "FAILURE"
        
        print(msg)
        self.write(msg)
        

class GetPrintWindow(BaseHandler):
    '''queries if the print window is open, returns true if open'''
    def get(self):
        try:            
            status = last_set_time > datetime.datetime.now()
            self.write(str(status))

        except:
            self.write("Error in get message")


class GetValidUsers(BaseHandler):
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

class GetUserPermsFromShortCode(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        shortcode = self.get_argument('shortcode', default=None)
        print("Shortcode", shortcode)
        if not shortcode:
            self.write("Shortcode not provided!")
            return
        
        try:
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM public.access WHERE shortcode=%s", (shortcode,))
                    result = cur.fetchone()
                    if not result:
                        result = {}
                    else:
                        result = {'shortcode':result[1],'print':result[2],'laser':result[3],'inducted':result[4]}
                    self.write(result)
        except Exception as e:
            self.write(e.message,e.args)
        

class GetUserPerms(BaseHandler):
    def get(self):
        data = json.loads(self.request.body)
        if data.get('secret') != secret:
            print("secret incorrect")
            self.finish("incorrect key")
            msg = "FAILURE"
            self.write(msg)
            return

        if (shortcode := data.get('shortcode')):
            shortcode = shortcode.strip().replace(" ", "")    
            perm_request = "SELECT * FROM public.access WHERE shortcode=%s"
            param = shortcode
        else:
            uid = data.get('id').strip().replace(" ","")
            perm_request = "SELECT * FROM public.access WHERE id=%s"
            param = uid
        try:
            with pg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute(perm_request, (param,))
                    result = cur.fetchone()
                    print(result)
                    if not result:
                        result = {}
                    else:
                        result = {'shortcode':result[1],'print':result[2],'laser':result[3],'inducted':result[4]}
                    self.write(result)
        except Exception as e:
            self.write(e.message,e.args)

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
        self.write(db_execute_command("INSERT INTO public.print_metrics (shortcode, print_duration, print_weight, printer_name) VALUES (%s,%s,%s,%s)", (last_short_code, print_time, print_weight, printer_name)))
        # print(data)

        return

class GetMetrics(BaseHandler):
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


class GetAllInducted(BaseHandler):    
    @tornado.web.authenticated
    def get(self):
        with pg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT shortcode FROM public.access WHERE valid=\'TRUE\'")
                inducted = cur.fetchall()
                inducted = [c[0] + "@ic.ac.uk" for c in inducted]
                self.write(json.dumps(inducted, default=str))
                return
