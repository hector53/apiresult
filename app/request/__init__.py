from flask import  request, jsonify, abort, make_response, session
from app import app
from app import socketio
from app.schemas import *
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import qrcode
import time
import math


def time_passed(fecha):
        mesFecha = ["Ene", "Feb","Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep",
        "Oct", "Nov", "Dic"  ];
        timestamp = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
        timestamp = datetime.timestamp(timestamp)
        print("timestamp",timestamp)

        print("fecha normal", datetime.fromtimestamp(timestamp))
        fechaNormal = datetime.fromtimestamp(timestamp)
        year = fechaNormal.strftime("%Y")
        print("año ", year)
        print(int(time.time()))

        diff = int(time.time()) - int(timestamp)
        print(diff)
        if diff == 0: 
             return 'justo ahora'

        if diff > 604800:
                dia = fechaNormal.strftime("%d")
                mes = fechaNormal.strftime("%b")
                #mes = mes[1:2]
                return f"{dia} {mes}"

        if diff < 604800:
                intervals = ['days', 86400]
        if diff < 86400:
                intervals = ['h', 3600]
        if diff < 3600:
                intervals = ['min', 60]
        if diff < 60:
                intervals = ['seg', 1]

        value = math.floor(diff/intervals[1])
        return f"{value} {intervals[0]}"


@app.route('/api/login' , methods=['POST'])
def login():
    body = request.get_json()
    print(body)
    email = body["email"]
    password = body["password"]

    sql = f"SELECT * FROM mn_users where email = '{email}' and pass = '{password}'  " 
    getUser = getDataOne(sql)
    if getUser: 
        access_token = create_access_token(identity=getUser[0])
        person1 = {
        "id": getUser[0],
        "name": getUser[1]+' '+getUser[2],
        "email": getUser[3], 
        "username": getUser[4], 
        "token": access_token
        }
        return jsonify(person1)
    else:
        abort(make_response(jsonify(message="data user incorrect"), 401))

@app.route('/api/_get_test' , methods=['POST'])
def guardar_capture():
    body = request.get_json()
    person1 = {
      "name": "Bob", 
      "id": body["id"], 
    }
    return jsonify(person1)

@app.route('/api/set' , methods=['GET'])
def setsesion():
    session['misesion'] = 'value'
    return 'ok'


@app.route('/api/getSession' , methods=['GET'])
@jwt_required()
def getSession():
    current_user_id = get_jwt_identity()
    return jsonify({"id": current_user_id}), 200

    

@app.route('/api/create_poll_not_user' , methods=['POST'])
def create_poll_not_user():
    body = request.get_json()
    print(body)
    pregunta = body["pregunta"]
    opciones = body["opciones"]
    miCodigo = body["miCodigo"]
    cookieNotUser = body["cookieNotUser"]
    ipWeb = body["ipWeb"]
    #consultar si el usuario existe sino guardarlo 
    sql = f"SELECT * FROM mn_users_cookie where cookie = '{cookieNotUser}' " 
    getUser = getDataOne(sql)
    if getUser:
        print("ya existe")
    else:
        #guardarlo
        sql = f"""
        INSERT INTO mn_users_cookie ( name, ip, cookie, fecha) VALUES ( 'guest',
        '{ipWeb}', '{cookieNotUser}', '{datetime.now()}'  ) 
        """ 
        id_user = updateData(sql)




    sql = f"""
    INSERT INTO mn_eventos ( titulo, descripcion, codigo, id_user, status, fecha) VALUES ( '{pregunta}',
    '', '{miCodigo}', '{cookieNotUser}', 1,  '{datetime.now()}'  ) 
    """ 
    id_evento = updateData(sql)
    sql = f"""
    INSERT INTO mn_tipo_encuesta ( tipo, titulo, id_user, id_evento, fecha) VALUES ( 1,
    '{pregunta}', '{cookieNotUser}', '{id_evento}',  '{datetime.now()}'  ) 
    """ 
    id_tipo_encuesta = updateData(sql)
    data = url_site+miCodigo
    QRCodefile = "app/static/img/qr/QR_"+miCodigo+".png"
    QRimage = qrcode.make(data)
    QRimage.save(QRCodefile)
    for opcion in opciones:
        sql = f"""
        INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{opcion}',
        '{id_tipo_encuesta}' ) 
        """ 
        actualizar = updateData(sql)
    
    response = {
        'codigo': miCodigo,
        'status': 1
        }
    return jsonify(response)



  
@app.route('/api/me' , methods=['GET'])
def getUser():
    body = request.get_json()
    person1 = {
         "id": 1,
        "name": "Jon Snow",
        "email": "jon.snow@asoiaf.com"
    }
    return jsonify(person1)

@app.route('/api/logout' , methods=['POST'])
def salir():
        session.pop('loggedin', None)
        session.pop('id_user', None)
        session.pop('username', None)
        session.pop('user', None)
        return jsonify(status=1)



@app.route('/api/register' , methods=["POST"])
def registrar_user():
        body = request.get_json()
        print(body)
        firstName = body["firstName"]
        lastName = body["lastName"]
        email = body["email"]
        userName = body["userName"]
        passW = body["pass"]
        userCookie = body["userCookie"]

        if firstName and lastName and email and userName and passW:
                #todos estos campos estan llenos
                sql = f"""
                INSERT INTO mn_users ( firstName, lastName, email, userName, pass, cookieUser, date) 
                VALUES 
                ( '{firstName}', '{lastName}', '{email}', '{userName}', '{passW}', '{userCookie}', '{datetime.now()}'  ) 
                """ 
                id_user = updateData(sql)
                #ahora reemplazar este id por el id de las cookies en las encuestas
                sql2 = f"""
                update mn_eventos set id_user = '{id_user}' where id_user = '{userCookie}'  
                """ 
                updateEncuesta = updateData(sql2)

                sql2 = f"""
                update mn_tipo_encuesta set id_user = '{id_user}' where id_user = '{userCookie}'  
                """ 
                updateEncuesta = updateData(sql2)
                #ahora reemplazAR EL USUARIO en los votos 
                sql3 = f"""
                update mn_votos_choice set id_user = '{id_user}' where id_user = '{userCookie}'  
                """ 
                updateVotos = updateData(sql3)

                access_token = create_access_token(identity=id_user)

                
                response={
                        "status": id_user, 
                        "token": access_token
                }
        else:
                response={
                        "status": 0
                }
        return jsonify(response) 


#user not registered 

@app.route('/api/events_not_registered' , methods=['GET'])
def events_not_registered():
    cookieNotUser = request.args.get('cookieNotUser', '')
    sqlV = f"SELECT COUNT(*) FROM `mn_votos_choice` WHERE id_user = '{cookieNotUser}' " 
    cantVotos = getData(sqlV)
    sql = f"SELECT * FROM mn_eventos where id_user = '{cookieNotUser}' order by id desc " 
    #buscar por uid las encuestas q tenga en la db 
    evento = getData(sql)
    data = []
    if evento:
            for row in evento:
                    idEvento=row[0]
                    #buscar cantidad de votos 
                    sqlVO = f"SELECT COUNT(*) FROM `mn_votos_choice` WHERE  id_evento = '{idEvento}' " 
                    cantVotoO = getData(sqlVO)
                    
                    data.append({
                    'id': row[0],
                    'titulo': row[1],
                    'codigo': row[3],
                    'fecha':   time_passed(str(row[6])),
                    'cantVoto': cantVotoO[0][0]
                    })

            response = {
            'encuestas': data,
            'cantVotos': cantVotos[0][0],
            'cantEncuestas': len(evento),
            'status': 1,
            }

    else:
            response = {
            'status': 0,
            }

    return jsonify(response)

@app.route('/api/_get_encuesta_not_registered' , methods=["GET"])
def get_encuesta_not_registered():
        codigo = request.args.get('codigo', '')
        print(codigo)
        cookieNotUser = request.args.get('u', '')
        codigo = codigo[0:5]
        
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}'  " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        idEvento = evento[0]

        sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{idEvento}' and tipo = 1  " 
        #buscar por uid las encuestas q tenga en la db 
        encuesta = getDataOne(sql)
        
        data = []
        if encuesta:
                idEncuesta = encuesta[0]
                sql2 = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = {idEncuesta}  " 
                print(sql2)
                opciones = getData(sql2)
               
                if opciones:
                        #buscar votos 
                        sql3 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {idEncuesta}  " 
                        print(sql3)
                        votos = getData(sql3)
                        totalVotos = len(votos)
                        descripcionMeta = ''
                        i = 0
                        for row in opciones:
                                #sacar porcentaje 
                                id_opcion = row[0]
                                sql4 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {idEncuesta} and id_opcion = {id_opcion}  "
                                print(sql4) 
                                voto_opcion = getData(sql4)
                                if voto_opcion:
                                        total_voto_opcion = len(voto_opcion)
                                        porcentaje = (total_voto_opcion * 100) / totalVotos
                                        color = i
                                else:
                                        porcentaje = 0
                                        total_voto_opcion = 0
                                        color = 10
                                if i==0:
                                        descripcionMeta = descripcionMeta + str((i+1))+')'+row[1]
                                else:
                                        descripcionMeta = descripcionMeta + ', '+str((i+1))+')'+row[1]
                                
                                data.append({
                                'id': row[0],
                                'valor': row[1],
                                'porcentaje':   "{:.2f}".format(float(porcentaje)),
                                'totalVoto': total_voto_opcion, 
                                'color': color
                                })

                                #buscar por uid si vote en la encuesta
                                miUid = cookieNotUser
                                sql3 = f"SELECT * FROM mn_votos_choice where id_user = '{miUid}' and id_tipo_encuesta = '{idEncuesta}'  " 
                                print(sql3)
                                voto = getDataOne(sql3)
                                
                                if voto:
                                        siVote = 1
                                        miVoto= voto[1]
                                else:
                                        siVote = 0
                                        miVoto= 0
                                
                                i=i+1

                        response = {
                        'totalVotos': totalVotos,
                        'opciones': data,
                        'encuesta': encuesta,
                        'siVote': siVote, 
                        'meta':descripcionMeta, 
                        'miVoto': miVoto, 
                        "qr": url_site+'static/img/qr/QR_'+codigo+'.png', 
                        "id_evento": idEvento, 
                        "fecha": time_passed(str(encuesta[5]))
                        }

                        
                        return jsonify(response) 
        else:
                response =0
                return jsonify(response) 


@app.route('/api/_votar_user_not' , methods=["POST"])
def votar_encuesta():  
        body = request.get_json()
        id_opcion = body["id_opcion"]
        id_encuesta = body["id_encuesta"]
        cookieNotUser = body["cookieNotUser"]
        id_evento = body["id_evento"]
        miUid = cookieNotUser
        sql = f"SELECT * FROM mn_users where cookieUser = '{miUid}' " 
        getUser = getDataOne(sql)
        if getUser:
                return jsonify(result = 0) 
        else:
                status = 1

        #buscar si el usuario ya voto en esta encuesta 
        sql2 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{miUid}'    " 
        print(sql2)
        opciones = getData(sql2)
        print(opciones)
        if opciones:
                return jsonify(result = 2) 
        else:
                print("no voto")
                #guardar la votacion nueva 
                sql = f"""
                INSERT INTO mn_votos_choice ( id_opcion, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{id_opcion}',
                '{miUid}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
                """ 
                actualizar = updateData(sql)
                if actualizar:
                        #socketio.emit('respuestaDelVoto', 'votaste')
                        return jsonify(result = status) 
                else:
                        return jsonify(result = 3) 

@app.route('/api/_cancelar_voto_not_registered' , methods=["GET"])
def cancelar_voto():
        id_encuesta = request.args.get('id_encuesta', '')
        miUid = request.args.get('u', '')
        sql = f"""
        DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id_encuesta}' and id_user = '{miUid}'
                """ 
        actualizar = deleteData(sql)
        response = {
        'status': actualizar,
        }
        socketio.emit('respuestaDelVoto', 'votaste')
        return jsonify(response) 