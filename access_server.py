import sqlite3
import datetime
import os
from dotenv import load_dotenv
import tornado
import json
load_dotenv()


secret = os.environ["SECRET"]
DATABASE = "database.db"
last_set_time = datetime.datetime.fromtimestamp(0)

try:
    env = os.environ["ENV"]
except:
    env = "dev"

def create_table():
    """
    creates a database using the db.sql schema
    if dev environment is detected, the database is recreated every time
    """
    try:
        with open("db.sql",'r') as f:
            schema = f.read()
        if env=="dev":
            os.remove(DATABASE)
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
            canPrint = bool(data.get("canPrint"))
            canLaserCut = bool(data.get("canLaserCut"))

            if data.get('secret') != secret:
                self.set_status(403)
                self.finish("Not Authorised!")
                return "incorrect key"
            
            ID = data.get('id')
            if canPrint is not None:
                db_execute_command("UPDATE Access SET CANPRINT=? WHERE VALID=\'TRUE\' AND ID=?", (str(canPrint).upper(), ID))
            if canLaserCut is not None:
                db_execute_command("UPDATE Access SET CANLASERCUT=? WHERE VALID=\'TRUE\' AND ID=?", (str(canLaserCut).upper(), ID))

            self.write(db_execute_command("INSERT INTO Access (ID, VALID) VALUES (?,?)", (ID, "TRUE")))

        except:
            self.finish("ERROR in post message")

class updateUser(tornado.web.RequestHandler):
    '''updates user perms'''
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
        try:
            data = json.loads(self.request.body)
            print(data)
            if data.get('secret') != secret:
                self.finish("incorrect key")
                return
            
            ID = data.get('id')
            window = data.get('window')
            if window is None:
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
            con.rollback()
            msg = "FAILURE"
        finally:
            con.close()
            print(msg)
            self.write(msg)
        


# @app.route('/getCanPrint', methods = ['GET'])
# def get_can_print():

#     return {"canPrint": last_set_time > datetime.datetime.now()}
class getPrintWindow(tornado.web.RequestHandler):
    '''queries if the print window is open, returns true if open'''
    def post(self):
        try:
            data = json.loads(self.request.body)
            print(data)
            if data.get('secret') != secret:
                self.finish("incorrect key")
                return
            
            status = last_set_time > datetime.datetime.now()
            self.write(str(status))

        except:
            self.write("Error in post message")