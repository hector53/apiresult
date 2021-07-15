from flask import  request, jsonify, abort, make_response, session
from app import app
from app import socketio
from app.schemas import *
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_socketio import join_room, leave_room, rooms
import time
import math
import string    
import random
import json
from dateutil import tz
clientes = []

mesFecha = ["Ene", "Feb","Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep",
        "Oct", "Nov", "Dic"  ];
def time_passed(fecha):
       
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
    INSERT INTO mn_eventos ( titulo, descripcion, codigo, id_user, modo, tipoUser, status, fecha) VALUES ( '{pregunta}',
    '', '{miCodigo}', '{cookieNotUser}', 0, 0, 1,  '{datetime.now()}'  ) 
    """ 
    id_evento = updateData(sql)
    sql = f"""
    INSERT INTO mn_tipo_encuesta ( tipo, titulo, id_user, id_evento, fecha) VALUES ( 1,
    '{pregunta}', '{cookieNotUser}', '{id_evento}',  '{datetime.now()}'  ) 
    """ 
    id_tipo_encuesta = updateData(sql)
    data = url_site+miCodigo
    
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

                sql = f"SELECT * FROM mn_users where id = '{id_user}' " 
                getUser = getDataOne(sql)

                
                response={
                        "name": getUser[1]+' '+getUser[2],
                        "email": getUser[3], 
                        "username": getUser[4], 
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
                    'fecha':   time_passed(str(row[8])),
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
                        "fecha": time_passed(str(evento[8]))
                        }

                        
                        return jsonify(response) 
        else:
                response =0
                return jsonify(response) 


@app.route('/api/_votar_user_not' , methods=["POST"])
def votar_encuesta():  
        body = request.get_json()
        print(body)
        id_opcion = body["id_opcion"]
        id_encuesta = body["id_encuesta"]
        cookieNotUser = body["cookieNotUser"]
        codigo = body["codigo"]
        modoLive = body["liveMode"]
        id_evento = body["id_evento"]
        login = body["login"]
        miUid = cookieNotUser
        if login:
                status =1
        else:
                sql = f"SELECT * FROM mn_users where cookieUser = '{miUid}' " 
                getUser = getDataOne(sql)
                if getUser:
                        return jsonify(result = 0) 
                else:
                        status = 1
        #buscar si esta encuesta es multiple respuesta o no
        sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and extra = 1   " 
        print(sql2)
        encu = getDataOne(sql2)
        if encu: 
                #busco si el usuario ya voto en esta opcion 
                sql2 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{miUid}' and id_opcion = '{id_opcion}'    " 
                opciones = getData(sql2)
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
                                if modoLive == 1:
                                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta})
                                socketio.emit('respuestaDelVoto', { "tipo": 1, "id_evento":id_evento, "msj": "votaste", "id_encuesta": id_encuesta})
                                return jsonify(result = status) 
                        else:
                                return jsonify(result = 3)
        else:
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
                                if modoLive == 1:
                                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta})
                                socketio.emit('respuestaDelVoto', { "tipo": 1, "id_evento":id_evento, "msj": "votaste", "id_encuesta": id_encuesta})
                                return jsonify(result = status) 
                        else:
                                return jsonify(result = 3) 

@app.route('/api/_cancelar_voto_not_registered' , methods=["GET"])
def cancelar_voto():
        id_encuesta = request.args.get('id_encuesta', '')
        id_evento = request.args.get('id_evento', '')
        codigo = request.args.get('codigo', '')
        miUid = request.args.get('u', '')
        modoLive = request.args.get('modoLive', '')
        print("modo live", modoLive)
        sql = f"""
        DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id_encuesta}' and id_user = '{miUid}'
                """ 
        actualizar = deleteData(sql)
        response = {
        'status': 1,
        }
        print("modo live cancelar voto", modoLive)
        if modoLive=='1':
                print("llegue a emitir el cancelar voto")
                socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta})
        socketio.emit('respuestaDelVoto', { "tipo": 1, "id_evento":id_evento, "msj": "cancelo voto", "id_encuesta": id_encuesta})
        return jsonify(response) 



#user registered

@app.route('/api/events_user_registered' , methods=['GET'])
@jwt_required()
def events_user_registered():
    id_user = get_jwt_identity()
    sqlV = f"SELECT COUNT(*) FROM `mn_votos_choice` WHERE id_user = '{id_user}' " 
    cantVotos = getData(sqlV)
    sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' order by id desc " 
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
                    'fecha':   time_passed(str(row[8])),
                    'cantVoto': cantVotoO[0][0]
                    })

            response = {
            'eventos': data,
            'cantVotos': cantVotos[0][0],
            'cantEventos': len(evento),
            'status': 1,
            }

    else:
            response = {
            'status': 0,
            }

    return jsonify(response)

#funcion codigo aleatorio 
def codigoAleatorio(s):
        ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = s))    
        return str(ran)
#


@app.route('/api/crear_evento' , methods=["POST"])
@jwt_required()
def crear_evento():  
        body = request.get_json()
        titulo = body["titulo"]
        descripcion = body["descripcion"]
        id_user = get_jwt_identity()
        codigo = codigoAleatorio(5)

        #buscar eventos del usuario el ultimo para saber el id
        sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' order by id desc " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
        else:
                id_evento = 0
        
        if titulo:
                numeroF = format((id_evento+1), "03d")
                titulo = f"{titulo}_{numeroF}"  
                sql = f"""
                INSERT INTO mn_eventos ( titulo, descripcion, codigo, id_user, modo, tipoUser,  status, fecha) 
                VALUES 
                ( '{titulo}', '{descripcion}', '{codigo}', '{id_user}', 0, 1, 0, '{datetime.now()}'  ) 
                """ 
                id_evento = updateData(sql)

                response = {
                        "status": id_evento, 
                        "codigo": codigo
                }
        else:
                response = {
                        "status": 0
                }


        return jsonify(response)





@app.route('/api/guardar_pregunta_tipo_1' , methods=["POST"])
@jwt_required()
def guardar_pregunta_tipo_1():  
        print("llegue aqui")
        body = request.get_json()
        id = body["id"]
        pregunta = body["pregunta"]
        id_user = get_jwt_identity()
        codigo = body["codigo"]
        #buscar id del evento por le codigo 
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}' " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento: 
                print("si existe el evento")
                id_evento = evento[0]
        else: 
                print("no existe el evento pailas lo voto")
                response = {
                        "status": 0
                }
                return jsonify(response)

        if id == 0:
                print("es nueva la creo")
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion, id_user, id_evento, fecha) 
                VALUES 
                ( 1, '{pregunta}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
                """ 
                id_tipo = updateData(sql)
                response = {
                        "status": id_tipo, 
                        "id": id_tipo
                }
        else:
                print("es vieja la actualizo")
                sql = f"""
                update mn_tipo_encuesta set titulo = '{pregunta}', fecha = '{datetime.now()}' where 
                id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id}'
                """ 
                id_tipo = updateData(sql)
                response = {
                        "status": 1, 
                        "id": id
                }
        
        return jsonify(response)



@app.route('/api/guardar_pregunta_tipo_2' , methods=["POST"])
@jwt_required()
def guardar_pregunta_tipo_2():  
        print("llegue aqui")
        body = request.get_json()
        id = body["id"]
        pregunta = body["pregunta"]
        id_user = get_jwt_identity()
        codigo = body["codigo"]
        #buscar id del evento por le codigo 
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}' " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento: 
                print("si existe el evento")
                id_evento = evento[0]
        else: 
                print("no existe el evento pailas lo voto")
                response = {
                        "status": 0
                }
                return jsonify(response)

        if id == 0:
                print("es nueva la creo")
                #necesito saber la posicion de la ultima encuesta 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion, id_user, id_evento, fecha) 
                VALUES 
                ( 2, '{pregunta}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
                """ 
                id_tipo = updateData(sql)
                response = {
                        "status": id_tipo, 
                        "id": id_tipo
                }
        else:
                print("es vieja la actualizo")
                sql = f"""
                update mn_tipo_encuesta set titulo = '{pregunta}', fecha = '{datetime.now()}' where 
                id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id}'
                """ 
                id_tipo = updateData(sql)
                response = {
                        "status": 1, 
                        "id": id
                }
        
        return jsonify(response)

@app.route('/api/guardar_opciones_tipo_1' , methods=["POST"])
@jwt_required()
def guardar_opciones_tipo_1():  
        print("llegue aqui")
        body = request.get_json()
        id = body["id"]
        id_user = get_jwt_identity()
        codigo = body["codigo"]
        pregunta = body["pregunta"]
        opciones = body["opciones"]
        multiple = body["multiple"]
        #buscar id del evento por le codigo 
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}' " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento: 
                print("si existe el evento")
                id_evento = evento[0]
        else: 
                print("no existe el evento pailas lo voto")
                response = {
                        "status": 0
                }
                return jsonify(response)

        if id == 0:
                print("es nueva la creo")
                #consultar la posicion 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1

                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion, id_user, id_evento, extra, fecha) 
                VALUES 
                ( 1, '{pregunta}', '{posicion}', '{id_user}', '{id_evento}', '{multiple}', '{datetime.now()}'  ) 
                """ 
                id_tipo = updateData(sql)
                #ahora aqui si creo las opciones 
                for opcion in opciones:
                        opcionValue = opcion["opcion"]
                        sql = f"""
                        INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{opcionValue}',
                        '{id_tipo}' ) 
                        """ 
                        actualizar = updateData(sql)
                
                #cargar opciones 
                sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id_tipo}' " 
                #buscar por uid las encuestas q tenga en la db 
                opcionesDb = getData(sqlOp)
                opcionesData = []
                for op in opcionesDb:
                        opcionesData.append({
                        'id': op[0],
                        'opcion': op[1],
                        })
                
                response = {
                        "status": id_tipo, 
                        "id": id_tipo, 
                        "opciones": opcionesData
                }
        else:
                print("es vieja la actualizo")
                sql = f"""
                update mn_tipo_encuesta set titulo = '{pregunta}', extra = '{multiple}', fecha = '{datetime.now()}' where 
                id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id}'
                """ 
                id_tipo = updateData(sql)
                #comprar la opcion si no existe la creo, y si existe la actualizo
                for opcion in opciones:
                        opcionValue = opcion["opcion"]
                        idOpcion = opcion["id"]
                        if idOpcion==0:
                                print("creo la opcion")
                                sql = f"""
                                INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{opcionValue}',
                                '{id}' ) 
                                """  
                                crearOpcion = updateData(sql)
                        else:
                                print("actualizo la opcion")
                                sql = f"""
                                update mn_tipo_encuesta_choice set opcion = '{opcionValue}' where 
                                id = '{idOpcion}'
                                """ 
                                id_tipo = updateData(sql)

                
                #cargar opciones 
                sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id}' " 
                #buscar por uid las encuestas q tenga en la db 
                opcionesDb = getData(sqlOp)
                opcionesData = []
                for op in opcionesDb:
                        opcionesData.append({
                        'id': op[0],
                        'opcion': op[1],
                        })
                response = {
                        "status": 1, 
                        "id": id, 
                        "opciones": opcionesData
                }
        
        return jsonify(response)


@app.route('/api/get_encuestas_event' , methods=['GET'])
@jwt_required()
def get_encuestas_event():
        id_user = get_jwt_identity()
        codigo = request.args.get('codigo', '')
        sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' and codigo = '{codigo}'  " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento: 
                print("existe el evento")
                id_evento = evento[0]
                nameEvent = evento[1]
                eventStatus = evento[7]
                eventModo = evento[5]
                fecha = evento[8]
               
        else: 
                print("no existe el evento ")
                response = {
                        "status": 0
                }
                return jsonify(response)

        #ahora listo las encuestas con sus respectivas opciones 
        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc " 
        #buscar por uid las encuestas q tenga en la db 
        encuestas = getData(sql)
        if encuestas:
                print("si tiene")
                print(encuestas)
                encuestaTipo = []
                for en in encuestas:
                        idEcuesta = en[0]
                        tipo = en[1]
                        pregunta = en[2]
                        multiple = en[7]
                        premios = en[9]

                        if tipo == 1:
                                #ahora busco las opciones 
                                #cargar opciones 
                                sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{idEcuesta}' " 
                                #buscar por uid las encuestas q tenga en la db 
                                opcionesDb = getData(sqlOp)
                                print("voy por opciones", opcionesDb)
                                opcionesData = []
                                for op in opcionesDb:
                                        opcionesData.append({
                                        'id': op[0],
                                        'opcion': op[1],
                                        })

                                print("ya guarde las opciones")
                                print("es tipo 1")
                                encuestaTipo.append( {
                                 'tipo': tipo, 
                                'idEcuesta': idEcuesta,
                                'pregunta': pregunta, 
                                'opciones': opcionesData,
                                'opciones2': opcionesData, 
                                'multiple': multiple
                                })
                                print("ua guarte tipo 1", encuestaTipo)
                        if tipo == 2:
                                encuestaTipo.append( {
                                 'tipo': tipo, 
                                'idEcuesta': idEcuesta,
                                'pregunta': pregunta,
                                'multiple':multiple
                                })
                        if tipo == 3:
                                #buscar participantes
                                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {idEcuesta}  "
                                participantes = getData(sql2)
                                #ahora buscar si ya como usuario envie mi respeusta
                                integrantes = [] 
                                for row in participantes:
                                        integrantes.append({
                                        'id': row[0],
                                        'value': row[1],
                                        })
                                #buscar ganadores 
                                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {idEcuesta} and ganador > 0  "
                                ganadoresP = getData(sql2)
                                ganadores = [] 
                                for row in ganadoresP:
                                        ganadores.append({
                                        'id': row[0],
                                        'value': row[1],
                                        })    
                                encuestaTipo.append( {
                                 'tipo': tipo, 
                                'idEcuesta': idEcuesta,
                                'pregunta': pregunta,
                                'premios': premios,
                                'participantes': integrantes, 
                                'ganadores': ganadores, 
                                'id_evento': id_evento
                                })
                        if tipo == 4:
                                encuestaTipo.append( {
                                 'tipo': tipo, 
                                'idEcuesta': idEcuesta,
                                'pregunta': pregunta,
                                'id_evento': id_evento
                                })

                                  

                                
                response = {
                        "status": 1, 
                        "misencuestas": encuestaTipo, 
                        "eventName": nameEvent, 
                        "eventStatus": eventStatus, 
                        "eventModo": eventModo, 
                        "fecha": str(fecha.date())
                }

                return jsonify(response)
                        
        else:
                print("no tiene")
                response = {
                        "status": 0, 
                        "eventName": nameEvent, 
                        "eventStatus": eventStatus, 
                        "eventModo": eventModo, 
                         "fecha": str(fecha.date())
                }
                return jsonify(response)


@app.route('/api/mover_arriba_posicion_encuesta' , methods=["POST"])
@jwt_required()
def mover_arriba_posicion_encuesta():  
        print("llegue aqui")
        body = request.get_json()
        idEncuestaVieja = body["idEncuestaVieja"]
        idEncuestaNueva = body["idEncuestaNueva"]
        posicionVieja = body["posicionVieja"]
        posicionNueva = body["posicionNueva"]

        id_user = get_jwt_identity()
        
        sql = f"""
        update mn_tipo_encuesta set posicion = '{posicionNueva}' where 
        id = '{idEncuestaVieja}' and id_user = '{id_user}'
        """ 
        id_tipo = updateData(sql)

        sql = f"""
        update mn_tipo_encuesta set posicion = '{posicionVieja}' where 
        id = '{idEncuestaNueva}' and id_user = '{id_user}'
        """ 
        id_tipo = updateData(sql)

        response = {
        "status": 1, 
        }
        
        return jsonify(response)

#get encuesta by codigo event

@app.route('/api/get_event_by_cod_front' , methods=["GET"])
def get_event_by_cod_front():
        codigo = request.args.get('codigo', '')
        print(codigo)
        codigo = codigo[0:5]
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}'  " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                #listar las encuestas para enviarlas de una vez 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' order by posicion asc  " 
                #buscar por uid las encuestas q tenga en la db 
                encuestas = getData(sql)
                encuestaTipo = []
                if encuestas:
                        
                        for en in encuestas:
                                encuestaTipo.append( {
                                'id': en[0], 
                                'tipo': en[1],
                                'titulo': en[2], 
                                'posicion': en[3],
                                })
                        response = {
                        "status": 1, 
                        "id_evento":  evento[0], 
                        "tipoUser": evento[6],
                        "statusEvent": evento[7],
                        "modo": evento[5],
                        "encuestas": encuestaTipo
                        }
                else: 
                        response = {
                        "status": 2, 
                        "id_evento":  evento[0], 
                        "tipoUser": evento[6],
                        "statusEvent": evento[7],
                        "modo": evento[5],
                        "encuestas": encuestaTipo
                        }
               
        else:
                response = {
                        "status": 0, 
                }

        return jsonify(response) 


@app.route('/api/get_encuesta_by_id' , methods=["GET"])
def get_encuesta_by_id():
        idEncuesta = request.args.get('id_encuesta', '')
        p = request.args.get('p', '')
        sql2 = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = {idEncuesta}  " 
        print(sql2)
        opciones = getData(sql2)
        data = []
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
                        miUid = p
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
                'status':1,
                'totalVotos': totalVotos,
                'opciones': data,
                'siVote': siVote, 
                'meta':descripcionMeta, 
                'miVoto': miVoto, 
                }
        else:
                response = {
                'status': 0
                }

       
        return jsonify(response) 
                


#publicar evento 


@app.route('/api/publicar_evento' , methods=["POST"])
@jwt_required()
def publicar_evento():  
        body = request.get_json()
        publicarDesactivar = body["publicarDesactivar"]
        print(publicarDesactivar)
        if publicarDesactivar == 1:
                status = 0
        else:
                status = 1

        id_user = get_jwt_identity()
        codigo = body["codigo"]
        sql = f"""
        update mn_eventos set status = '{status}' where 
        codigo = '{codigo}' and id_user = '{id_user}'
        """ 
        evento = updateData(sql)
        socketio.emit('cambiarStatusEvent', { "codigo": codigo, "status": status})
        response = {
                'status': 1
                }
        return jsonify(response) 


#activar modo live evento 
@app.route('/api/modo_live_evento' , methods=["POST"])
@jwt_required()
def modo_live_evento():  
        body = request.get_json()
        modoLive = body["modoLive"]
        id_user = get_jwt_identity()
        codigo = body["codigo"]
        sql = f"""
        update mn_eventos set modo = '{modoLive}' , status = '{modoLive}' where 
        codigo = '{codigo}' and id_user = '{id_user}'
        """ 
        evento = updateData(sql)
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        id_evento = evento[0]
        #update encuesta posicion 1 a play 1
        print("modo live", modoLive)
        if modoLive == 0: 
                print("modo live 0")
                sql = f"""
                update mn_tipo_encuesta set play = 0 where 
                id_evento = '{id_evento}' and id_user = '{id_user}' 
                """ 
                print(sql)
                tipoEncuesta = updateData(sql)
        else:
                print("poner activa la primera encuesta")
                sql = f"""
                update mn_tipo_encuesta set play = 0 where 
                id_evento = '{id_evento}' and id_user = '{id_user}' 
                """ 
                tipoEncuesta = updateData(sql)
                #buscar la encuesta uno ordenada por posicion 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and id_user = '{id_user}' order by posicion asc  " 
                primeraEncuesta = getDataOne(sql)
                if primeraEncuesta:
                        posiPri = primeraEncuesta[3]
                else:
                        posiPri = 0


                sql = f"""
                update mn_tipo_encuesta set play = {modoLive} where 
                id_evento = '{id_evento}' and id_user = '{id_user}' and posicion = '{posiPri}'
                """ 
                tipoEncuesta = updateData(sql)
        
        socketio.emit('activarModoPresentacion', { "codigo": codigo, "modo": modoLive})
        response = {
                'status': 1
                }
        return jsonify(response) 

#cambiar encuesta activa en modo live evento 
@app.route('/api/modo_live_evento_encuesta_activa' , methods=["POST"])
@jwt_required()
def modo_live_evento_encuesta_activa():  
        body = request.get_json()
        id_user = get_jwt_identity()
        codigo = body["codigo"]
        idEncuesta =  body["id"]
        
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        id_evento = evento[0]
        #updte evento tambien 
        sql = f"""
        update mn_eventos set status = 1, modo = 1 where 
        id = '{id_evento}' and id_user = '{id_user}' 
        """ 
        updateEvento = updateData(sql)
        #update encuesta posicion 1 a play 1
        sql = f"""
        update mn_tipo_encuesta set play = 0 where 
        id_evento = '{id_evento}' and id_user = '{id_user}' 
        """ 
        tipoEncuesta = updateData(sql)
        sql = f"""
        update mn_tipo_encuesta set play = 1 where 
        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{idEncuesta}'
        """ 
        tipoEncuesta = updateData(sql)
        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": idEncuesta})
        response = {
                'status': 1
                }
        return jsonify(response) 

#get encuesta activa modo live event
@app.route('/api/get_encuesta_event_live' ,  methods=["GET"])
def get_encuesta_event_live():  
        codigo = request.args.get('codigo', '')
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and modo = 1 " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and play = 1 " 
                en = getDataOne(sql)
                encuestaTipo = []
                play = 0
                if en:
                        encuestaTipo.append( {
                        'id': en[0], 
                        'tipo': en[1],
                        'titulo': en[2], 
                        'posicion': en[3],
                        'play': en[6]
                        })
                response = {
                "status": 1, 
                "id":  evento[0], 
                "titulo": evento[1],
                "statusEvent": evento[7],
                "modo": evento[5],
                "tipoEncuesta": encuestaTipo, 
                }
        else:
                 response = {
                "status": 0, 
                 }

        return jsonify(response)



#get encuesta by id en modo live modal
@app.route('/api/get_encuestas_by_id_live' ,  methods=["GET"])
@jwt_required()
def get_encuestas_by_id_live():  
        id = request.args.get('id', '')
        id_user = get_jwt_identity()
        sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id}' and id_user = '{id_user}' " 
        #buscar por uid las encuestas q tenga en la db 
        en = getDataOne(sql)
        encuestaTipo = []
        if en:
                encuestaTipo.append( {
                'id': en[0], 
                'tipo': en[1],
                'titulo': en[2], 
                'posicion': en[3],
                'play': en[6], 
                'multiple': en[7]
                })
                if en[1]==1:
                        #cargar opciones 
                        sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id}' " 
                        #buscar por uid las encuestas q tenga en la db 
                        opcionesDb = getData(sqlOp)
                        opcionesData = []
                        for op in opcionesDb:
                                id_opcion = op[0]
                                #buscar si hay votos en esta opcion
                                sqlVo = f"SELECT * FROM mn_votos_choice where id_opcion = '{id_opcion}' " 
                                #buscar por uid las encuestas q tenga en la db 
                                votos = getData(sqlVo)
                                sivotos = 0
                                if votos:
                                        sivotos = 1

                                opcionesData.append({
                                'id': op[0],
                                'opcion': op[1],
                                'votos': sivotos
                                })

                        response = {
                        "status": 1, 
                        "encuesta":  encuestaTipo, 
                        "opciones": opcionesData,
                        }
                if en[1]==2:
                        response = {
                        "status": 1, 
                        "encuesta":  encuestaTipo, 
                        }
                if en[1]==4:
                        sql = f"SELECT * FROM mn_date_day where id_encuesta = '{id}' " 
                        #buscar por uid las encuestas q tenga en la db 
                        getDias = getData(sql)
                        arrayDias = []
                        arrayDate = []
                        if getDias:
                                for dia in getDias:
                                        id_dia = dia[0]
                                        #aqui buscar las horas del dia
                                        sql = f"SELECT * FROM mn_date_horas where id_date_day = '{id_dia}' " 
                                        #buscar por uid las encuestas q tenga en la db 
                                        getHoras = getData(sql)
                                        arrayHoras = []
                                        for ho in getHoras:
                                                id_hora = ho[0]
                                                horaValue = ho[1]
                                                arrayHoras.append({
                                                'id': id_hora,
                                                'ini': str(horaValue),
                                                'fin': horaValue
                                                })

                                        arrayDias.append({
                                        'id': dia[0],
                                        'dia': str(dia[1]),
                                        'horas': arrayHoras
                                        })
                                        
                                        arrayDate.append(
                                         str(dia[1])
                                        )
                        response = {
                        "status": 1, 
                        "encuesta":  encuestaTipo, 
                        "dias": arrayDias, 
                        "date": arrayDate
                        }
                        
                        

                
                
        else:
                 response = {
                "status": 0, 
                 }

        return jsonify(response)

@app.route('/api/get_event_by_cod' , methods=["GET"])
@jwt_required()
def get_event_by_cod():
        print("get event ")
        id_user = get_jwt_identity()
        codigo = request.args.get('codigo', '')
        print(codigo)
        codigo = codigo[0:5]
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        #buscar por uid las encuestas q tenga en la db 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' order by posicion asc  " 
                #buscar por uid las encuestas q tenga en la db 
                encuestas = getData(sql)
                encuestaTipo = []
                play = 0
                if encuestas:
                        id_encuesta_primera = encuestas[0][0]
                        for en in encuestas:
                                if en[6] == 1:
                                        play = en[0]
                                encuestaTipo.append( {
                                'id': en[0], 
                                'tipo': en[1],
                                'titulo': en[2], 
                                'posicion': en[3],
                                'play': en[6]
                                })

                        response = {
                        "status": 1, 
                        "id":  evento[0], 
                        "titulo": evento[1],
                        "statusEvent": evento[7],
                        "modo": evento[5],
                        "tipoEncuesta": encuestaTipo, 
                        "encuestaActiva": play
                        }
                else:
                        response={
                        "status": 2
                        }
        else:
                response={
                        "status": 0
                }

        return jsonify(response) 



@app.route('/api/get_encuesta_by_id_result' , methods=["GET"])
def get_encuesta_by_id_result():
        idEncuesta = request.args.get('id_encuesta', '')
        sql2 = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = {idEncuesta}  " 
        opciones = getData(sql2)
        data = []
        if opciones:
                #buscar votos 
                sql3 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {idEncuesta}  " 
                votos = getData(sql3)
                totalVotos = len(votos)
                i = 0
                for row in opciones:
                        #sacar porcentaje 
                        id_opcion = row[0]
                        sql4 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {idEncuesta} and id_opcion = {id_opcion}  "
                        voto_opcion = getData(sql4)
                        if voto_opcion:
                                total_voto_opcion = len(voto_opcion)
                                porcentaje = (total_voto_opcion * 100) / totalVotos
                                color = i
                        else:
                                porcentaje = 0
                                total_voto_opcion = 0
                                color = 10
                        
                        data.append({
                        'id': row[0],
                        'valor': row[1],
                        'porcentaje':   "{:.2f}".format(float(porcentaje)),
                        'totalVoto': total_voto_opcion, 
                        'color': color
                        })

                        i=i+1

                response = {
                'status':1,
                'totalVotos': totalVotos,
                'opciones': data,
                }
        else:
                response = {
                'status': 0
                }

       
        return jsonify(response) 


#sockets
@socketio.on('conectar')
def handle_join_room_event(data):
        socketId =  rooms()
        print("id de usuario conectado", socketId)
        print("hola q tal estoy en el socket conectar")
        #aqui guardar en la db el cliente conectado
        sql = f"SELECT * FROM mn_clientes_conectados where id_user = '{data['username']}' and codigo_evento = '{data['room']}'  " 
        cliente = getDataOne(sql)
        if cliente: 
                print("ya esta conectado")
        else:
                #buscar si el dueño del evento para no sumarlo
                sql = f"SELECT * FROM mn_eventos where id_user = '{data['username']}' and codigo = '{data['room']}'  " 
                adminEvento = getDataOne(sql)
                if adminEvento: 
                        print("no guardar")
                else:
                        sql = f"""
                        INSERT INTO mn_clientes_conectados ( id_room, codigo_evento, id_user) VALUES ( '{socketId[0]}',
                        '{data['room']}', '{data['username']}' ) 
                        """ 
                        actualizar = updateData(sql)
                

        app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
        join_room(data['room'])
        #en este emit debo enviar las personas conectadas al evento
        sql = f"SELECT * FROM mn_clientes_conectados where  codigo_evento = '{data['room']}'  " 
        clientes = getData(sql)
        conectados = len(clientes)
        socketio.emit('join_room_announcement', {'username': data['username'], 'codigo': data['room'], 'conectados': conectados})
        print("emiti el socket")


@socketio.on('desconectar')
def desconectar_user_modo_live_event(data):
        print(data)
        sql = f"""
        delete from mn_clientes_conectados where codigo_evento = '{data['room']}' and id_user = '{data['username']}'
        """ 
        actualizar = updateData(sql)
        sql = f"SELECT * FROM mn_clientes_conectados where  codigo_evento = '{data['room']}'  " 
        clientes = getData(sql)
        conectados = len(clientes)
        socketio.emit('join_room_disconect', {'username': data['username'], 'codigo': data['room'], 'conectados': conectados})
        print('Client disconnected', request.sid)

#create poll simple modo live 

@app.route('/api/create_poll_simple_live' , methods=['POST'])
@jwt_required()
def create_poll_simple_live():
        body = request.get_json()
        print(body)
        pregunta = body["pregunta"]
        opciones = body["opciones"]
        codigo = body["codigo"]
        activar = body["activar"]
        id_user = get_jwt_identity()
        multiple = body["multiple"]
        print("multiple", multiple)
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                #necesito saber la posicion de la ultima encuesta 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento, extra, fecha) VALUES ( 1,
                '{pregunta}', '{posicion}', '{id_user}', '{id_evento}', '{multiple}', '{datetime.now()}'  ) 
                """ 
                id_tipo_encuesta = updateData(sql)

                for opcion in opciones:
                        sql = f"""
                        INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{opcion}',
                        '{id_tipo_encuesta}' ) 
                        """ 
                        actualizar = updateData(sql)
                if activar == 1:
                        sql = f"""
                        update mn_eventos set modo = 1, status = 1 where 
                        id = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        eventoUpdate = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 0 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        tipoEncuesta = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 1 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
                        """ 
                        tipoEncuesta = updateData(sql)
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})
                response = {
                'status': 1
                }
        else: 
                response = {
                'status': 0
                }

        return jsonify(response)

#edit poll simple live

@app.route('/api/edit_poll_simple_live' , methods=['POST'])
@jwt_required()
def edit_poll_simple_live():
        body = request.get_json()
        print(body)
        pregunta = body["pregunta"]
        opciones = body["opciones"]
        modo = body["modo"]
        codigo = body["codigo"]
        multiple = body["multiple"]
        id = body["id"]
        opcionesNueva = body["opcionesNueva"]
        id_user = get_jwt_identity()
        sql = f"""
        update mn_tipo_encuesta set titulo = '{pregunta}', extra = '{multiple}' where 
        id = '{id}' and id_user = '{id_user}' 
        """ 
        tipoEncuesta = updateData(sql)
        for op in opciones:
                        opcionTexto = op["opcion"]
                        opcionId = op["id"]
                        sql = f"""
                        update mn_tipo_encuesta_choice set opcion = '{opcionTexto}' where id = '{opcionId}' and id_tipo_encuesta = '{id}' 
                                """ 
                        actualizar = updateData(sql)
        #ahora insertar las nuevas
        for op2 in opcionesNueva:
                sql = f"""
                INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{op2}',
                '{id}' ) 
                """ 
                actualizar = updateData(sql)
        
        if modo == 1:
                socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id})

        response = {
                'status': 1,
                }

        return jsonify(response)

#edit poll nuibe de palabras live

@app.route('/api/edit_nube_palabras_live' , methods=['POST'])
@jwt_required()
def edit_nube_palabras_live():
        body = request.get_json()
        print(body)
        pregunta = body["pregunta"]
        codigo = body["codigo"]
        modo = body["modo"]
        id = body["id"]
        id_user = get_jwt_identity()
        sql = f"""
        update mn_tipo_encuesta set titulo = '{pregunta}' where 
        id = '{id}' and id_user = '{id_user}' 
        """ 
        tipoEncuesta = updateData(sql)
        if modo == 1:
                socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id})

        response = {
                'status': 1,
                }

        return jsonify(response)

@app.route('/api/delete_poll_simple_live' , methods=["POST"])
@jwt_required()
def delete_poll_simple_live():
        body = request.get_json()
        id = body["id"]
        id_opcion = body["id_opcion"]
        id_user = get_jwt_identity()
        print("id de la encuesta",id)
        print("id de la opcion",id_opcion)
        sql = f"""
        DELETE FROM `mn_tipo_encuesta_choice` WHERE  id_tipo_encuesta = '{id}' and id = '{id_opcion}' 
                """ 
        actualizar = deleteData(sql)

        sql = f"""
        DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id}' and id_opcion = '{id_opcion}'
                """ 
        actualizar = deleteData(sql)
        
        response = {
        'status': actualizar,
        }
        return jsonify(response) 



@app.route('/api/delete_poll_simple_live_by_id' , methods=["POST"])
@jwt_required()
def delete_poll_simple_live_by_id():
        body = request.get_json()
        id = body["id"]
        codigo = body["codigo"]
        id_user = get_jwt_identity()
        sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id}' and id_user = '{id_user}'  " 
        buscarTipo = getDataOne(sql)
        tipo = 0
        if buscarTipo:
                tipo = buscarTipo[1]
                sql = f"""
                DELETE FROM `mn_tipo_encuesta` WHERE  id = '{id}' and id_user = '{id_user}'
                """ 
                actualizar = deleteData(sql)
                if tipo == 1:
                        sql = f"""
                        DELETE FROM `mn_tipo_encuesta_choice` WHERE  id_tipo_encuesta = '{id}'
                        """ 
                        actualizar = deleteData(sql)

                        sql = f"""
                        DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id}' 
                        """ 
                        actualizar = deleteData(sql)
                if tipo == 2:
                        sql = f"""
                        DELETE FROM `mn_nube_palabras` WHERE  id_tipo_encuesta = '{id}'
                        """ 
                        actualizar = deleteData(sql)
                if tipo == 3:
                        sql = f"""
                        DELETE FROM `mn_sorteos_participantes` WHERE  id_encuesta = '{id}'
                        """ 
                        actualizar = deleteData(sql)
                if tipo == 4:
                        sql = f"""
                        DELETE FROM `mn_date_day` WHERE  id_encuesta = '{id}'
                        """ 
                        actualizar = deleteData(sql)
                        
                        sql = f"""
                        DELETE FROM `mn_date_horas` WHERE  id_encuesta = '{id}'
                        """ 
                        actualizar = deleteData(sql)

                        sql = f"""
                        DELETE FROM `mn_date_horas_votos` WHERE  id_tipo_encuesta = '{id}'
                        """ 
                        actualizar = deleteData(sql)
                
                #buscar si quedan encuestas y poner activa la primera 
                sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
                evento = getDataOne(sql)
                if evento:
                        id_evento = evento[0]
                        #buscar encuestas del evento 
                        sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and id_user = '{id_user}' order by posicion asc " 
                        misencuestas = getDataOne(sql)
                        print(misencuestas)
                        if misencuestas:
                                id_encuesta_primera = misencuestas[0]
                                #update 
                                sql = f"""
                                update  mn_tipo_encuesta set play = 1 where id = '{id_encuesta_primera}'  
                                """ 
                                actualizar = deleteData(sql)
                                socketio.emit('cambioDeEncuesta', { "tipo": 3, "msj": "elimine una encuesta", "codigo":codigo, "id_encuesta": id_encuesta_primera})
                        else:
                                socketio.emit('cambioDeEncuesta', { "tipo": 5, "msj": "sin encuestas", "codigo":codigo})
       
                response = {
                'status': actualizar,
                }
        else:
                response = {
                'status': 'error',
                }
                
        return jsonify(response) 

#nube de palabras 
@app.route('/api/create_poll_nube_palabras_live' , methods=['POST'])
@jwt_required()
def create_poll_nube_palabras_live():
        body = request.get_json()
        print(body)
        pregunta = body["pregunta"]
        codigo = body["codigo"]
        activar = body["activar"]
        id_user = get_jwt_identity()
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                #necesito saber la posicion de la ultima encuesta 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1

                
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento, fecha) VALUES ( 2,
                '{pregunta}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
                """ 
                id_tipo_encuesta = updateData(sql)

                if activar == 1:
                        sql = f"""
                        update mn_eventos set modo = 1, status = 1 where 
                        id = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        eventoUpdate = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 0 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        tipoEncuesta = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 1 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
                        """ 
                        tipoEncuesta = updateData(sql)
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})
                response = {
                'status': 1
                }
        else: 
                response = {
                'status': 0
                }

        return jsonify(response)

#create sorteo live 

@app.route('/api/create_sorteo_live' , methods=['POST'])
@jwt_required()
def create_sorteo_live():
        body = request.get_json()
        print(body)
        titulo = body["titulo"]
        participantes = body["participantes"]
        participantesArray = json.loads(participantes)
        #cantidad de participantes 
        premios = body["premios"]
        codigo = body["codigo"]
        activar = body["activar"]
        id_user = get_jwt_identity()

        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                #necesito saber la posicion de la ultima encuesta 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento, premios, fecha) VALUES ( 3,
                '{titulo}', '{posicion}', '{id_user}', '{id_evento}', '{premios}',  '{datetime.now()}'  ) 
                """ 
                id_tipo_encuesta = updateData(sql)
                #agregar participantes
                for lis in participantesArray:
                        sql = f"""
                        INSERT INTO mn_sorteos_participantes ( value, id_encuesta) VALUES ( '{lis}',
                        '{id_tipo_encuesta}' ) 
                        """ 
                        id_participante = updateData(sql)

                if activar == 1:
                        sql = f"""
                        update mn_eventos set modo = 1, status = 1 where 
                        id = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        eventoUpdate = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 0 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        tipoEncuesta = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 1 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
                        """ 
                        tipoEncuesta = updateData(sql)
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})
                
                #buscar participantes
                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_tipo_encuesta}  "
                participantes = getData(sql2)
                #ahora buscar si ya como usuario envie mi respeusta
                integrantes = [] 
                for row in participantes:
                        integrantes.append({
                        'id': row[0],
                        'value': row[1],
                        })

                response = {
                'status': 1, 
                'id': id_tipo_encuesta, 
                'participantes': integrantes
                }
        else: 
                response = {
                'status': 0
                }

        return jsonify(response)

#edit sorteo modal live

@app.route('/api/edit_sorteo_live_modal' , methods=['POST'])
@jwt_required()
def edit_sorteo_live_modal():
        body = request.get_json()
        print(body)
        titulo = body["titulo"]
        participantes = body["participantes"]
        participantesArray = json.loads(participantes)
        print("participantes", participantesArray)
        #cantidad de participantes 
        premios = body["premios"]
        codigo = body["codigo"]
        activar = body["activar"]
        id_encuesta = body["id_encuesta"]
        id_user = get_jwt_identity()

        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                


                sql = f"""
                update  mn_tipo_encuesta set titulo = '{titulo}',
                premios = '{premios}' where id =  '{id_encuesta}' and id_user = '{id_user}'
                and id_evento = '{id_evento}'
                """ 
                id_tipo_encuesta = updateData(sql)

                #ahora borro los participantes viejos y añado los nuevos
                sql = f"""
                DELETE FROM `mn_sorteos_participantes` WHERE  id_encuesta = '{id_encuesta}'
                """ 
                actualizar = deleteData(sql)

                #agregar participantes
                for lis in participantesArray:
                        sql = f"""
                        INSERT INTO mn_sorteos_participantes ( value, id_encuesta) VALUES ( '{lis}',
                        '{id_encuesta}' ) 
                        """ 
                        id_participante = updateData(sql)

                if activar == 1:
                        sql = f"""
                        update mn_eventos set modo = 1, status = 1 where 
                        id = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        eventoUpdate = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 0 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        tipoEncuesta = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 1 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
                        """ 
                        tipoEncuesta = updateData(sql)
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})
                
                sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and id = '{id_encuesta}' and play = 1  " 
                tipoE = getDataOne(sql)
                if tipoE:
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})

                response = {
                'status': 1, 
                }
        else: 
                response = {
                'status': 0
                }

        return jsonify(response)

#create dia y hora live q


@app.route('/api/create_diayhora_live' , methods=['POST'])
@jwt_required()
def create_diayhora_live():
        body = request.get_json()
        titulo = body["titulo"]
        dias = body["dias"]
        diasArray = json.loads(dias)
        horas = body["horas"]
        horasArray = json.loads(horas)
        print(horasArray)
        #cantidad de participantes 
        codigo = body["codigo"]
        activar = body["activar"]
        id_user = get_jwt_identity()
        # METHOD 1: Hardcode zones:
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Caracas')
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                #necesito saber la posicion de la ultima encuesta 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getDataOne(sql)
                if enPosicion:
                        posicion = enPosicion[3]+1
                else:
                        posicion = 0+1
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento,  fecha) VALUES ( 4,
                '{titulo}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
                """ 
                id_tipo_encuesta = updateData(sql)
                #agregar participantes
                for d in horasArray:
                        fechaDia = d['id']
                        sql = f"""
                        INSERT INTO mn_date_day ( fecha, id_encuesta) VALUES ( '{fechaDia}',
                        '{id_tipo_encuesta}' ) 
                        """ 
                        id_dia = updateData(sql)
                        for h in d['horas']:
                                horaini = h['ini']      
                                horaini = datetime.strptime(horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
                                #utc = datetime.strptime(str(horaini), '%Y-%m-%d %H:%M:%S')
                                utc = horaini.replace(tzinfo=from_zone)
                                central = utc.astimezone(to_zone)
                                print(central)
                                horaini = str(central)

                                sql = f"""
                                INSERT INTO mn_date_horas ( hora, id_date_day, id_encuesta) VALUES ( '{horaini[:19]}',
                                '{id_dia}', '{id_tipo_encuesta}' ) 
                                """ 
                                id_hora = updateData(sql)

                if activar == 1:
                        sql = f"""
                        update mn_eventos set modo = 1, status = 1 where 
                        id = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        eventoUpdate = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 0 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        tipoEncuesta = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 1 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
                        """ 
                        tipoEncuesta = updateData(sql)
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})
                
                response = {
                'status': 1, 
                'id': id_tipo_encuesta, 
                }
        else: 
                response = {
                'status': 0
                }

        return jsonify(response)


#editar encueta dia y hora
@app.route('/api/edit_diayhora_live' , methods=['POST'])
@jwt_required()
def edit_diayhora_live():
        body = request.get_json()
        titulo = body["titulo"]
        dias = body["dias"]
        diasArray = json.loads(dias)
        horas = body["horas"]
        horasArray = json.loads(horas)
        print(horasArray)
        #cantidad de participantes 
        codigo = body["codigo"]
        activar = body["activar"]
        id_tipo_encuesta = body["id_encuesta"]


        id_user = get_jwt_identity()
        # METHOD 1: Hardcode zones:
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Caracas')
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                idsDiaNoBorrar = []
                idsHoraNoBorrar = []
                for d in horasArray:
                        idDb = d['idDb']
                        fechaDia = d['id']
                        if idDb == 0:
                                #inserto
                                sql = f"""
                                INSERT INTO mn_date_day ( fecha, id_encuesta) VALUES ( '{fechaDia}',
                                '{id_tipo_encuesta}' ) 
                                """ 
                                id_dia = updateData(sql)
                                idsDiaNoBorrar.append(id_dia)
                                for h in d['horas']:
                                        horaini = h['ini']      
                                        horaini = datetime.strptime(horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
                                        #utc = datetime.strptime(str(horaini), '%Y-%m-%d %H:%M:%S')
                                        utc = horaini.replace(tzinfo=from_zone)
                                        central = utc.astimezone(to_zone)
                                        print(central)
                                        horaini = str(central)

                                        sql = f"""
                                        INSERT INTO mn_date_horas ( hora, id_date_day, id_encuesta) VALUES ( '{horaini[:19]}',
                                        '{id_dia}', '{id_tipo_encuesta}' ) 
                                        """ 
                                        id_hora = updateData(sql)
                                        idsHoraNoBorrar.append(id_hora)
                        else:
                                #editar 
                                print("editar horas")
                                idsDiaNoBorrar.append(idDb)
                                for h in d['horas']:
                                        idHoraDb = h['id'] 
                                        if idHoraDb == 0: 
                                                #inserto 
                                                horaini = h['ini']      
                                                horaini = datetime.strptime(horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
                                                #utc = datetime.strptime(str(horaini), '%Y-%m-%d %H:%M:%S')
                                                utc = horaini.replace(tzinfo=from_zone)
                                                central = utc.astimezone(to_zone)
                                                print(central)
                                                horaini = str(central)

                                                sql = f"""
                                                INSERT INTO mn_date_horas ( hora, id_date_day, id_encuesta) VALUES ( '{horaini[:19]}',
                                                '{idDb}', '{id_tipo_encuesta}' ) 
                                                """ 
                                                id_hora = updateData(sql)
                                                idsHoraNoBorrar.append(id_hora)
                                        else:
                                                print("editar hora")
                                                #edito
                                                horaini = h['ini']      
                                                horaini = datetime.strptime(horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
                                                #utc = datetime.strptime(str(horaini), '%Y-%m-%d %H:%M:%S')
                                                utc = horaini.replace(tzinfo=from_zone)
                                                central = utc.astimezone(to_zone)
                                                print(central)
                                                horaini = str(central)

                                                sql = f"""
                                                update mn_date_horas set hora = '{horaini[:19]}' where id = '{idHoraDb}' 
                                                """ 
                                                id_hora = updateData(sql)
                                                idsHoraNoBorrar.append(idHoraDb)

                #borrar los ids q no esten incluidos en el array de dias y horas 
                #arrayT = [2,3,4,5,6]
                notBorrar = ''
                f=1

                for t in idsDiaNoBorrar:
                        if f==len(idsDiaNoBorrar):
                                notBorrar = notBorrar + str(t)
                        else:
                                notBorrar = notBorrar + str(t) + ','
                        f=f+1
                
                sql = f"""
                delete from mn_date_day where id not in ({notBorrar}) and id_encuesta = '{id_tipo_encuesta}'
                """ 
                print(sql)
                borrarSobrantes = updateData(sql)

                notBorrar = ''
                f=1

                for t in idsHoraNoBorrar:
                        if f==len(idsHoraNoBorrar):
                                notBorrar = notBorrar + str(t)
                        else:
                                notBorrar = notBorrar + str(t) + ','
                        f=f+1
                
                sql = f"""
                delete from mn_date_horas where id not in ({notBorrar}) and id_encuesta = '{id_tipo_encuesta}'
                """ 
                print(sql)
                borrarSobrantes = updateData(sql)

                sql = f"""
                delete from mn_date_horas_votos where id_date_hora not in ({notBorrar}) and id_tipo_encuesta = '{id_tipo_encuesta}'
                """ 
                print(sql)
                borrarSobrantes = updateData(sql)
                                        

                if activar == 1:
                        sql = f"""
                        update mn_eventos set modo = 1, status = 1 where 
                        id = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        eventoUpdate = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 0 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' 
                        """ 
                        tipoEncuesta = updateData(sql)
                        sql = f"""
                        update mn_tipo_encuesta set play = 1 where 
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
                        """ 
                        tipoEncuesta = updateData(sql)
                        socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_tipo_encuesta})
                
                response = {
                'status': 1, 
                'id': id_tipo_encuesta, 
                }
        else: 
                response = {
                'status': 0
                }

        return jsonify(response)

@app.route('/api/get_respuestas_by_user_nube_palabras' , methods=["GET"])
def get_respuestas_by_user_nube_palabras():
        id_evento = request.args.get('id_evento', '')
        id_encuesta = request.args.get('id_encuesta', '')
        id_user = request.args.get('p', '')
        sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}'  " 
        tipoEncuesta = getData(sql2)
        if tipoEncuesta:
                print("buscar nube de palabras si tiene respuestas")
                sql3 = f"SELECT palabra, COUNT(palabra) as cantidad FROM mn_nube_palabras where id_tipo_encuesta = '{id_encuesta}' and id_evento = '{id_evento}' GROUP BY palabra   " 
                nubePalabras = getData(sql3)
                #ahora buscar si ya como usuario envie mi respeusta 
                sql4 = f"SELECT * FROM mn_nube_palabras where id_tipo_encuesta = {id_encuesta} and id_evento = '{id_evento}' and id_user = '{id_user}'  " 
                nubePalabrasRespuesta = getData(sql4)
                siRespondi = 0
                if nubePalabrasRespuesta: 
                        siRespondi = 1
                
                response = {
                'status':1,
                'palabras': nubePalabras,
                'siRespondi': siRespondi,
                }
        else:
                response = {
                'status': 0
                }

       
        return jsonify(response) 

#get sorteo activo modo live 
@app.route('/api/get_datos_sorteo_by_id_encuesta' , methods=["GET"])
def get_datos_sorteo_by_id_encuesta():
        id_evento = request.args.get('id_evento', '')
        id_encuesta = request.args.get('id_encuesta', '')
        id_user = request.args.get('p', '')
        sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}'  " 
        tipoEncuesta = getDataOne(sql2)
        if tipoEncuesta:
                print(tipoEncuesta)
                #buscar participantes
                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_encuesta}  "
                participantes = getData(sql2)
                #ahora buscar si ya como usuario envie mi respeusta
                integrantes = [] 
                for row in participantes:
                         integrantes.append({
                        'id': row[0],
                        'value': row[1],
                        })
                
                #buscar ganadores 
                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_encuesta} and ganador > 0  "
                ganadoresP = getData(sql2)
                ganadores = [] 
                for row in ganadoresP:
                         ganadores.append({
                        'id': row[0],
                        'value': row[1],
                        })

                response = {
                'status':1,
                'participantes': integrantes,
                'premios': tipoEncuesta[9], 
                'ganadores': ganadores
                }
        else:
                response = {
                'status': 0
                }

       
        return jsonify(response) 


#get diayhora activo modo live 
@app.route('/api/get_datos_diayhora_by_id_encuesta' , methods=["GET"])
def get_datos_diayhora_by_id_encuesta():
        id_evento = request.args.get('id_evento', '')
        id_encuesta = request.args.get('id_encuesta', '')
        id_user = request.args.get('p', '')
        sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}'  " 
        tipoEncuesta = getDataOne(sql2)
        if tipoEncuesta:
                print(tipoEncuesta)
                #buscar participantes
                sql2 = f"SELECT * FROM mn_date_day where id_encuesta = {id_encuesta}  "
                dias = getData(sql2)
                #ahora buscar si ya como usuario envie mi respeusta
                diasyhoras = [] 
                #buscar horas ganadoras para tenerlas aquí :D 
                sql2 = f"SELECT id_date_hora, count(id_date_hora) as votos FROM `mn_date_horas_votos` where id_tipo_encuesta = '{id_encuesta}' GROUP by id_date_hora order by votos desc limit 0,2  "
                votosGanadores = getData(sql2)
                uno = 0
                votoGanador = 0
                id_mayorVoto = 0
                siHayMayorVoto = 0
                for unG in votosGanadores:
                        if uno == 0: 
                                votoGanador = unG[1]
                                id_mayorVoto = unG[0]
                        else:
                                if votoGanador > unG[1]:
                                        siHayMayorVoto = 1
                        uno = uno+1


                for row in dias:
                        id_dia = row[0]
                        sql2 = f"SELECT * FROM mn_date_horas where id_date_day = {id_dia} order by hora asc  "
                        horas = getData(sql2)
                        horasDia = []
                        for h in horas:
                                id_hora = h[0]
                                mihora = h[1]
                                minutos = mihora.minute
                                if minutos < 10:
                                        minutos = "0" + str(minutos)
                                #buscar los votos de esta hora y si ha votado en esta hora 
                                sql2 = f"SELECT * FROM mn_date_horas_votos where id_date_hora = {id_hora}  "
                                votosHoras = getData(sql2)
                                cantVotosHoras = len(votosHoras)
                                #buscar si el usuario voto en esta hora 
                                sql2 = f"SELECT * FROM mn_date_horas_votos where id_date_hora = {id_hora} and id_user = '{id_user}'  "
                                siVoteHora = getData(sql2)
                                if siVoteHora:
                                        sivoteH = 1
                                else:
                                        sivoteH = 0

                                #ver si es ganador o no 
                                votoGanador = 0
                                if siHayMayorVoto==1:
                                        if h[0] == id_mayorVoto:
                                                votoGanador = 1
                                else:
                                        for win in votosGanadores:
                                                if h[0] == win[0]:
                                                        votoGanador = 1
                                

                                horasDia.append({
                                'id': h[0],
                                'fecha': h[1],
                                'hora': mihora.hour, 
                                'minutos': minutos, 
                                'cantVotos': cantVotosHoras, 
                                'siVote': sivoteH, 
                                'votoGanador': votoGanador

                                })
                        my_date = datetime.strptime(str(row[1]), "%Y-%m-%d")
                        mes = my_date.month
                        dia = my_date.day
                        if dia < 10:
                                dia = "0" + str(dia)
                        
                        
                        

                        diasyhoras.append({
                                'id': id_dia,
                                'fecha': row[1],
                                'horas': horasDia, 
                                'mes': mesFecha[(mes-1)],
                                'dia': dia, 
                               
                                })
                
                #buscar cantidad de votos totales de la encuesta
                sql2 = f"SELECT * FROM mn_date_horas_votos where id_tipo_encuesta = {id_encuesta}  "
                votosTotales = getData(sql2)
                #buscar cantidad de usuarios q han votado 
                sql2 = f"SELECT count(DISTINCT id_user) as usuarios FROM `mn_date_horas_votos` where id_tipo_encuesta = '{id_encuesta}'  "
                usuariosTotales = getDataOne(sql2)
                response = {
                'status':1,
                'dias': diasyhoras,
                'votosTotales': len(votosTotales), 
                'usuariosTotales': usuariosTotales[0]
                }
        else:
                response = {
                'status': 0
                }

       
        return jsonify(response) 

#get sorteo by id encuesta 
#get sorteo activo modo live 
@app.route('/api/get__sorteo_by_id_encuesta_modal' , methods=["GET"])
def get__sorteo_by_id_encuesta_modal():
        id_encuesta = request.args.get('id_encuesta', '')
        id_user = request.args.get('p', '')
        sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_user = '{id_user}'  " 
        tipoEncuesta = getDataOne(sql2)
        if tipoEncuesta:
                print(tipoEncuesta)
                #buscar participantes
                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_encuesta}  "
                participantes = getData(sql2)
                #ahora buscar si ya como usuario envie mi respeusta
                integrantes = ''
                
                for row in participantes:
                        integrantes = integrantes + row[1] + '\n'
                
                response = {
                'status':1,
                'titulo':tipoEncuesta[2],
                'participantes': integrantes,
                'premios': tipoEncuesta[9], 
                }
        else:
                response = {
                'status': 0
                }

       
        return jsonify(response) 

@app.route('/api/add_palabra_live_front' , methods=['POST'])
def add_palabra_live_front():
        body = request.get_json()
        palabra = body["palabra"]
        id_evento = body["id_evento"]
        id_encuesta = body["id_encuesta"]
        codigo = body["codigo"]
        id_user = body["p"]
        modoLive = body["liveMode"]

        sql = f"""
        INSERT INTO mn_nube_palabras ( palabra, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{palabra}',
        '{id_user}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
        """ 
        id_nube_palabras = updateData(sql)
        if modoLive==1:
                socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta})
        socketio.emit('respuestaDelVoto', { "tipo": 2, "id_evento":id_evento, "msj": "Nueva palabra", "id_encuesta": id_encuesta})

        response = {
        'status': id_nube_palabras
        }

        return jsonify(response)

#votar encuesta dia y hora 
@app.route('/api/votar_encuesta_dia_y_hora_front' , methods=['POST'])
def votar_encuesta_dia_y_hora_front():
        body = request.get_json()
        hora = body["hora"]
        codigo = body["codigo"]
        id_evento = body["id_evento"]
        id_encuesta = body["id_encuesta"]
        id_user = body["p"]
        modoLive = body["liveMode"]
        #crear funciones para validar q el id del evento existe y q el usuario existe

        sql = f"SELECT * FROM mn_date_horas_votos where id_date_hora = '{hora}' and id_user = '{id_user}'  " 
        votoHora = getDataOne(sql)
        if votoHora:
                #ya votó
                sql = f"""
                DELETE FROM mn_date_horas_votos where id_date_hora = '{hora}' and id_user = '{id_user}'
                and id_tipo_encuesta = '{id_encuesta}' and id_evento = '{id_evento}'
                """ 
                id_voto_hora = updateData(sql)
                response = {
                        'status': 0
                }
        else:
                #votar 
                sql = f"""
                INSERT INTO mn_date_horas_votos ( id_date_hora, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{hora}',
                '{id_user}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
                """ 
                id_voto_hora = updateData(sql)
                response = {
                        'status': 1, 
                        'id_voto': id_voto_hora
                }
        
        if modoLive==1:
                socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta})
        socketio.emit('respuestaDelVoto', { "tipo": 4, "id_evento":id_evento, "msj": "Nueva voto en hora", "id_encuesta": id_encuesta})


        return jsonify(response)

@app.route('/api/_sortear1' , methods=["GET"])
def sortear1():
        participantes = request.args.get('participantes', '')
        premios = request.args.get('premios', '')
        y = json.loads(participantes)
        #cantidad de participantes 
        cantParticipantes = len(y)
        #lista de ganadores 
        ganadores = []
        while len(ganadores) < int(premios):
                #generamos numero aleatorio
                n = random.randint(1, cantParticipantes)
                if n not in ganadores:
                        #si no existe lo agrego 
                        ganadores.append(y[(n-1)])

        
        response = {
        'status': 1,
        'participantes': y, 
        'ganadores': ganadores
        }
        return jsonify(response) 



@app.route('/api/sortear_sorteo_live' , methods=['POST'])
def sortear_sorteo_live():
        body = request.get_json()
        participantes = body["participantes"]
        participantes = json.loads(participantes)
        cantParticipantes = len(participantes)
        premios = body["premios"]
        codigo = body["codigo"]
        id_encuesta = body["id_encuesta"]
        ganadores = []
        while len(ganadores) < int(premios):
                #generamos numero aleatorio
                n = random.randint(1, cantParticipantes)
                if n not in ganadores:
                        #si no existe lo agrego 
                        ganadores.append(participantes[(n-1)])
                        #update table participantes al ganador
                        print("ganador", participantes[(n-1)]['id'])
                        sql = f"""
                        update mn_sorteos_participantes set ganador = 1 where 
                        id = '{participantes[(n-1)]['id']}' 
                        """ 
                        guardarGanador = updateData(sql)

        socketio.emit('generarGanadorSorteo', { "ganadores": ganadores, "msj": "generando ganadores", "codigo":codigo, "id_encuesta": id_encuesta})
      

        response = {
        'status': 1,
        'participantes': participantes, 
        'ganadores': ganadores
        }

        return jsonify(response)

@app.route('/api/get_event_by_codigo_buscador' , methods=["GET"])
def get_event_by_codigo_buscador():
        codigo = request.args.get('codigo', '')
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}'  " 
        evento = getDataOne(sql)
        if evento:
                response = {
                'status': 1,
                }
        else:
                response = {
                'status': 0,
                }

        return jsonify(response) 


#get conectados al rooms

@app.route('/api/get_users_conectados' , methods=["GET"])
def get_users_conectados():
        codigo = request.args.get('codigo', '')
        
        print(request.sid)

        response = {
        'status': 1,
        }

        return jsonify(response) 