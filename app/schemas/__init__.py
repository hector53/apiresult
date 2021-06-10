import pymysql
from app.datos import *
#consultas mysql

def ultimoId():
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    ultimoId = con.insert_id()
    return ultimoId

def getData(consulta):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
            rows = cur.fetchall()
            return rows
            
    finally:
        con.close()


def getDataOne(consulta):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
            rows = cur.fetchone()
            return rows
            
    finally:
        con.close()

#update o insert

def updateData(consulta):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            guardar = cur.execute(consulta)
            con.commit()
            return cur.lastrowid
            
    finally:
        con.close()

#delete



def deleteData(consulta):
    con = pymysql.connect(host=host,   user=userDb,   password=userPass,    db=database)
    try:
        with con.cursor() as cur:
            guardar = cur.execute(consulta)
            con.commit()
            return guardar
            
    finally:
        con.close()