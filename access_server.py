from flask import Flask, request
import sqlite3
import datetime
import os

app = Flask(__name__)

secret = os.environ["secret"]
DATABASE = "database.db"

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


@app.route('/addUser', methods = ['POST'])
def add_user():
    if request.method == "POST":
        try:
            data = request.json
            secret = data.get("secret")
            
            if data.get('secret') != secret:
                return "incorrect key"
            
            ID = data.get('id')

            return db_execute_command("INSERT INTO Access (ID, VALID) VALUES (?,?)", (ID, "TRUE"))

        except:
            return "ERROR in post message"

    return

@app.route('/setUserCanPrint', methods = ['POST'])
def set_user_can_print():
    if request.method == "POST":
        try:
            data = request.json
            secret = data.get("secret")
            
            if data.get('secret') != secret:
                return "incorrect key"
            
            ID = data.get('id')
            CAN_PRINT = data.get('value')
            
            db_execute_command("UPDATE Access SET CANPRINT=? WHERE VALID=TRUE AND ID=?", (CAN_PRINT, ID))

        except:
            return "ERROR in post message"

    return


last_set_time = datetime.datetime.fromtimestamp(0)


@app.route('/setCanPrint', methods = ['POST'])
def set_can_print():
    if request.method == "POST":
        try:
            data = request.json
            secret = data.get("secret")
            
            if data.get('secret') != secret:
                return "incorrect key"
            
            ID = data.get('id')
            
            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()
                cur.execute("SELECT Count() From Access WHERE ID=? AND CANPRINT=\'TRUE\'", ID)

                if cur.fetchone()[0] > 0:
                    global last_set_time
                    last_set_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
        except:
            con.rollback()
        finally:
            con.close()
    return


@app.route('/getCanPrint', methods = ['GET'])
def get_can_print():

    return {"canPrint": last_set_time > datetime.datetime.now()}

app.run(host='0.0.0.0',port=5000)
