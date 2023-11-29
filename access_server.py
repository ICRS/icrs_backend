import sqlite3
import datetime
import os
from dotenv import load_dotenv
import tornado
import json
load_dotenv()
import union

secret = os.environ["SECRET"]
last_set_time = datetime.datetime.fromtimestamp(0)

try:
    env = os.environ["ENV"]
except:
    env = "dev"
DATABASE = "/home/pi/code/icrs_security/database.db" if env != "dev" else "database.db"

def create_table():
    """
    creates a database using the db.sql schema
    if dev environment is detected, the database is recreated every time
    """
    try:
        with open("db.sql",'r') as f:
            schema = f.read()
        if env=="dev":
            if os.path.isfile(DATABASE): os.remove(DATABASE)
        con = sqlite3.connect(DATABASE)
        c = con.cursor()
        c.execute(schema)
        con.commit()
    except Exception as e:
        print(e)

def db_execute_command(sql_query, parameters):
    try:
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute(sql_query, parameters)

            con.commit()
            msg = "Record successfully added"    
    except:
        con.rollback()
        msg = "error in insert operation"
    finally:
        con.close()
        return msg

class addUser(tornado.web.RequestHandler):
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
            #ISMEMBER = "TRUE"

            self.write( db_execute_command("INSERT INTO Access (ID, SHORTCODE, VALID) VALUES (?,?,?)", (ID, SHORTCODE, ISMEMBER)))
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
                db_execute_command("UPDATE Access SET CANPRINT=? WHERE VALID=\'TRUE\' AND ID=?", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE Access SET CANLASERCUT=? WHERE VALID=\'TRUE\' AND ID=?", (str(canLaserCut).upper(), ID))


        except:
            self.finish("ERROR in post message")

class registerUsers(tornado.web.RequestHandler):
    '''sets users to valid if they have membership'''
    def get(self):
        try:
            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()
                cur.execute("SELECT SHORTCODE From Access WHERE VALID=\'FALSE\' OR VALID=0")
                update = [(c[0],) for c in cur.fetchall()]
                update = union.isMemberList(update)
                set_valid_by_shortcode = "UPDATE Access SET VALID=\'TRUE\', CANPRINT=\'TRUE\' WHERE SHORTCODE=?"
                cur.executemany(set_valid_by_shortcode, update)
                con.commit()
                msg = "Successfully Registered Users"
        except Exception as e:
            print(e)
            con.rollback()
            msg = "FAILURE"
        finally:
            con.close()
            print(msg)
            self.write(msg)


class updateUser(tornado.web.RequestHandler):
    '''updates user perms'''
    def post(self):
        self.write("OK")

class setUserCanPrint(tornado.web.RequestHandler):
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
                db_execute_command("UPDATE Access SET CANPRINT=? WHERE VALID=\'TRUE\' AND ID=?", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE Access SET CANLASERCUT=? WHERE VALID=\'TRUE\' AND ID=?", (str(canLaserCut).upper(), ID))

        except:
            self.finish("Error in post message")
            return

        self.finish("SUCCESS")
        return
 

class setPrintWindow(tornado.web.RequestHandler):
    '''verifies if a user can print, if yes a print window of default 1 min is opened'''
    def post(self):
        con = None
        try:
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

            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()
                cur.execute("SELECT Count() From Access WHERE ID=? AND CANPRINT=\'TRUE\'", (ID,))

                if cur.fetchone()[0] > 0:
                    print("CHECK TIME")
                    global last_set_time
                    last_set_time = datetime.datetime.now() + datetime.timedelta(seconds=int(window))
                    msg = "SUCCESS"
                else:
                    msg = "FAILURE"
        except:
            if con is not None: con.rollback()
            msg = "FAILURE"
        
        if con is not None: con.close()
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
            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()
                cur.execute("SELECT SHORTCODE FROM Access A WHERE VALID=\'TRUE\' AND NOT EXISTS (SELECT \'X\' FROM SENT S WHERE A.SHORTCODE=S.SHORTCODE)")

                update = [c[0] for c in cur.fetchall()]
    
                mapping = union.getShortcodesToCIDAndName(update)
                
                cur.executemany("INSERT INTO SENT (SHORTCODE) VALUES (?)", [(c,) for c in update])
                return mapping
        except:
            con.rollback()
        finally:
            con.close()
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
            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()
                cur.execute("SELECT * From Access WHERE ID=?",(uid,))
                result = cur.fetchall()[0]
                result = {'shortcode':result[1],'print':result[2],'laser':result[3],'inducted':result[4]}
                self.write(result)
        except Exception as e:
            self.write(e.message,e.args)
        finally:
            con.close()

class printMetrics(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        if data.get('secret') != secret:
            # print("secret incorrect")
            self.finish("incorrect key")
            msg = "FAILURE"
            self.write(msg)
            return
        # TODO
        return

