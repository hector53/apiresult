from flask import  request, jsonify, abort, make_response, session
from app import app
from app import socketio
from app.schemas import *
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_socketio import join_room, leave_room
import qrcode
import time
import math
import string    
import random


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
        id_opcion = body["id_opcion"]
        id_encuesta = body["id_encuesta"]
        cookieNotUser = body["cookieNotUser"]
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
                        socketio.emit('respuestaDelVoto', { "tipo": 1, "id_evento":id_evento, "msj": "votaste", "id_encuesta": id_encuesta})
                        return jsonify(result = status) 
                else:
                        return jsonify(result = 3) 

@app.route('/api/_cancelar_voto_not_registered' , methods=["GET"])
def cancelar_voto():
        id_encuesta = request.args.get('id_encuesta', '')
        id_evento = request.args.get('id_evento', '')
        miUid = request.args.get('u', '')
        sql = f"""
        DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id_encuesta}' and id_user = '{miUid}'
                """ 
        actualizar = deleteData(sql)
        response = {
        'status': actualizar,
        }
        socketio.emit('respuestaDelVoto', {"tipo": 2, "msj": "cancelo el voto", "id_evento":id_evento, "id_encuesta": int(id_encuesta)})
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
        
        if titulo:
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
                enPosicion = getData(sql)
                posicion = len(enPosicion) + 1
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
                enPosicion = getData(sql)
                posicion = len(enPosicion) + 1
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
                enPosicion = getData(sql)
                posicion = len(enPosicion) + 1

                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion, id_user, id_evento, fecha) 
                VALUES 
                ( 1, '{pregunta}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
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
                update mn_tipo_encuesta set titulo = '{pregunta}', fecha = '{datetime.now()}' where 
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
                                'opciones2': opcionesData
                                })
                                print("ua guarte tipo 1", encuestaTipo)
                        if tipo == 2:
                                encuestaTipo.append( {
                                 'tipo': tipo, 
                                'idEcuesta': idEcuesta,
                                'pregunta': pregunta,
                                })

                                
                response = {
                        "status": 1, 
                        "misencuestas": encuestaTipo, 
                        "eventName": nameEvent, 
                        "eventStatus": eventStatus, 
                        "eventModo": eventModo
                }

                return jsonify(response)
                        
        else:
                print("no tiene")
                response = {
                        "status": 0, 
                        "eventName": nameEvent, 
                        "eventStatus": eventStatus, 
                        "eventModo": eventModo
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
        sql = f"""
        update mn_tipo_encuesta set play = {modoLive} where 
        id_evento = '{id_evento}' and id_user = '{id_user}' and posicion = 1
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
                'play': en[6]
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

                        if play == 0:
                                print("poner activa la primera encuesta")
                                sql = f"""
                                update mn_tipo_encuesta set play = 1 where 
                                id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_encuesta_primera}'
                                """ 
                                tipoEncuesta = updateData(sql)
                                play = id_encuesta_primera
                                #socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta_primera})
       
                
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
        print("hola q tal estoy en el socket conectar")
        app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
        join_room(data['room'])
        socketio.emit('join_room_announcement', data, room=data['room'])
        print("emiti el socket")

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
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  " 
        evento = getDataOne(sql)
        if evento:
                id_evento = evento[0]
                #necesito saber la posicion de la ultima encuesta 
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getData(sql)
                posicion = len(enPosicion) + 1
                sql = f"""
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento, fecha) VALUES ( 1,
                '{pregunta}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
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
        id = body["id"]
        opcionesNueva = body["opcionesNueva"]
        id_user = get_jwt_identity()
        sql = f"""
        update mn_tipo_encuesta set titulo = '{pregunta}' where 
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
                        DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id}' and id_user = '{id_user}'
                        """ 
                        actualizar = deleteData(sql)
                if tipo == 2:
                        sql = f"""
                        DELETE FROM `mn_nube_palabras` WHERE  id_tipo_encuesta = '{id}'
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
                                socketio.emit('cambioDeEncuesta', { "tipo": 1, "msj": "cambia encuesta", "codigo":codigo, "id_encuesta": id_encuesta_primera})
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
                sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc " 
                #buscar por uid las encuestas q tenga en la db 
                enPosicion = getData(sql)
                posicion = len(enPosicion) + 1
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

@app.route('/api/add_palabra_live_front' , methods=['POST'])
def add_palabra_live_front():
        body = request.get_json()
        palabra = body["palabra"]
        id_evento = body["id_evento"]
        id_encuesta = body["id_encuesta"]
        id_user = body["p"]

        sql = f"""
        INSERT INTO mn_nube_palabras ( palabra, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{palabra}',
        '{id_user}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
        """ 
        id_nube_palabras = updateData(sql)

        socketio.emit('respuestaDelVoto', { "tipo": 2, "id_evento":id_evento, "msj": "Nueva palabra", "id_encuesta": id_encuesta})

        response = {
        'status': id_nube_palabras
        }

        return jsonify(response)