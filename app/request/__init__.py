from flask import request, jsonify, abort, make_response, session
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

from app.request.encuestas.multipleChoice import *
from app.request.encuestas.nubeDePalabras import *
from app.request.encuestas.sorteos import *
from app.request.encuestas.diaYHora import *
from app.request.encuestas.qya import *

clientes = []
mesFecha = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep",
            "Oct", "Nov", "Dic"]



@app.route('/api/login', methods=['POST'])
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

@app.route('/api/_get_test', methods=['POST'])
def guardar_capture():
    body = request.get_json()
    person1 = {
        "name": "Bob",
        "id": body["id"],
    }
    return jsonify(person1)

@app.route('/api/set', methods=['GET'])
def setsesion():
    session['misesion'] = 'value'
    return 'ok'

@app.route('/api/getSession', methods=['GET'])
@jwt_required()
def getSession():
    current_user_id = get_jwt_identity()
    #buscar si el usuario tiene ip 
    sql = f"SELECT * FROM mn_users where id = '{current_user_id}' "
    buscarUser = getDataOne(sql)
    if buscarUser: 
        ip = buscarUser[7]
    else:
        ip = ''
    return jsonify({"id": current_user_id, "ip": ip}), 200



@app.route('/api/update_ip_user_registered', methods=['POST'])
def update_ip_user_registered():
    body = request.get_json()
    id_user = body["id_user"]
    pais = body["pais"]
    ipUser = body["ipUser"]

    sql = f"""
    update mn_users set ip = '{ipUser}', pais = '{pais}' where 
    id = '{id_user}' 
                        """
    print(sql)
    updateIpUser = updateData(sql)

    response = {
        'status': 1,
    }

    return jsonify(response)

@app.route('/api/me', methods=['GET'])
def getUser():
    body = request.get_json()
    person1 = {
        "id": 1,
        "name": "Jon Snow",
        "email": "jon.snow@asoiaf.com"
    }
    return jsonify(person1)


@app.route('/api/logout', methods=['POST'])
def salir():
    session.pop('loggedin', None)
    session.pop('id_user', None)
    session.pop('username', None)
    session.pop('user', None)
    return jsonify(status=1)

@app.route('/api/register', methods=["POST"])
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
        # todos estos campos estan llenos
        sql = f"""
                INSERT INTO mn_users ( firstName, lastName, email, userName, pass, cookieUser, date) 
                VALUES 
                ( '{firstName}', '{lastName}', '{email}', '{userName}', '{passW}', '{userCookie}', '{datetime.now()}'  ) 
                """
        id_user = updateData(sql)
        # ahora reemplazar este id por el id de las cookies en las encuestas
        sql2 = f"""
                update mn_eventos set id_user = '{id_user}' where id_user = '{userCookie}'  
                """
        updateEncuesta = updateData(sql2)

        sql2 = f"""
                update mn_tipo_encuesta set id_user = '{id_user}' where id_user = '{userCookie}'  
                """
        updateEncuesta = updateData(sql2)
        # ahora reemplazAR EL USUARIO en los votos
        sql3 = f"""
                update mn_votos_choice set id_user = '{id_user}' where id_user = '{userCookie}'  
                """
        updateVotos = updateData(sql3)

        access_token = create_access_token(identity=id_user)

        sql = f"SELECT * FROM mn_users where id = '{id_user}' "
        getUser = getDataOne(sql)

        response = {
            "name": getUser[1]+' '+getUser[2],
            "email": getUser[3],
            "username": getUser[4],
            "status": id_user,
            "token": access_token
        }
    else:
        response = {
            "status": 0
        }
    return jsonify(response)


# register user invitado
@app.route('/api/crear_user_invitado', methods=["POST"])
def crear_user_invitado():
    body = request.get_json()
    print(body)
    cookieUser = body["cookieUser"]
    pais = body["pais"]
    ipUser = body["ipUser"]

    # todos estos campos estan llenos
    sql = f"""
        INSERT INTO mn_users_cookie ( name, ip, pais, cookie, fecha) 
        VALUES 
        ( 'guest', '{ipUser}', '{pais}', '{cookieUser}', '{datetime.now()}'  ) 
        """
    id_user = updateData(sql)

    response = {
        "status": id_user
    }
    return jsonify(response)


# user not registered
@app.route('/api/events_not_registered', methods=['GET'])
def events_not_registered():
        cookieNotUser = request.args.get('cookieNotUser', '')
        sql = f"SELECT * FROM mn_eventos where id_user = '{cookieNotUser}' order by id desc "
        # buscar por uid las encuestas q tenga en la db
        evento = getData(sql)
        data = []
        if evento:
                totalVotos = 0
                for row in evento:
                        idEvento = row[0]
                
                        # buscar la encuesta creada para saber el tipo de encuesta
                        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{cookieNotUser}' and id_evento = '{idEvento}'  "
                        print("sql asdasdsadasd", sql)
                        # buscar por uid las encuestas q tenga en la db
                        getEncuesta = getDataOne(sql)
                        print("get encuesta", getEncuesta)
                        tipo = getEncuesta[1]
                        id_encuesta = getEncuesta[0]

                        #select cant de votos por tipo encuesta 

                        if tipo == 1:
                                sqlVO = f"SELECT COUNT(*) FROM `mn_votos_choice` WHERE  id_evento = '{idEvento}' "
                                cantVoto = getDataOne(sqlVO)
                        
                        if tipo == 2:
                                sqlVO = f"SELECT COUNT(*) FROM `mn_nube_palabras` WHERE  id_evento = '{idEvento}' "
                                cantVoto = getDataOne(sqlVO)
                        if tipo == 4:
                                sqlVO = f"SELECT COUNT(*) FROM `mn_date_horas_votos` WHERE  id_evento = '{idEvento}' "
                                cantVoto = getDataOne(sqlVO)


                        
                        totalVotos = totalVotos + cantVoto[0]



                        data.append({
                        'id': row[0],
                        'titulo': row[1],
                        'codigo': row[3],
                        'fecha':   time_passed(str(row[8])),
                        'cantVoto': cantVoto[0],
                        'tipo': tipo,
                        'id_encuesta': id_encuesta
                        })

                response = {
                        'encuestas': data,
                        'cantVotos': totalVotos,
                        'cantEncuestas': len(evento),
                        'status': 1,
                }

        else:
                response = {
                        'status': 0,
                }

        return jsonify(response)

# user registered
@app.route('/api/events_user_registered', methods=['GET'])
@jwt_required()
def events_user_registered():
    id_user = get_jwt_identity()
    sqlV = f"SELECT COUNT(*) FROM `mn_votos_choice` WHERE id_user = '{id_user}' "
    cantVotos = getData(sqlV)
    sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' order by id desc "
    # buscar por uid las encuestas q tenga en la db
    evento = getData(sql)

    data = []
    if evento:
        for row in evento:
            idEvento = row[0]
            # buscar cantidad de votos
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

# funcion codigo aleatorio

def codigoAleatorio(s):
    ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k=s))
    return str(ran)
#

@app.route('/api/crear_evento', methods=["POST"])
@jwt_required()
def crear_evento():
    body = request.get_json()
    titulo = body["titulo"]
    descripcion = body["descripcion"]
    id_user = get_jwt_identity()
    codigo = codigoAleatorio(5)

    # buscar eventos del usuario el ultimo para saber el id
    sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' order by id desc "
    # buscar por uid las encuestas q tenga en la db
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
                ( '{titulo}', '{descripcion}', '{codigo}', '{id_user}', 0, 1, 1, '{datetime.now()}'  ) 
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


@app.route('/api/get_encuestas_event', methods=['GET'])
@jwt_required()
def get_encuestas_event():
    id_user = get_jwt_identity()
    codigo = request.args.get('codigo', '')
    sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' and codigo = '{codigo}'  "
    # buscar por uid las encuestas q tenga en la db
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

    # ahora listo las encuestas con sus respectivas opciones
    sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc "
    # buscar por uid las encuestas q tenga en la db
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
                # ahora busco las opciones
                # cargar opciones
                sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{idEcuesta}' "
                # buscar por uid las encuestas q tenga en la db
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
                encuestaTipo.append({
                    'tipo': tipo,
                    'idEcuesta': idEcuesta,
                    'pregunta': pregunta,
                    'opciones': opcionesData,
                    'opciones2': opcionesData,
                    'multiple': multiple
                })
                print("ua guarte tipo 1", encuestaTipo)
            if tipo == 2:
                encuestaTipo.append({
                    'tipo': tipo,
                    'idEcuesta': idEcuesta,
                    'pregunta': pregunta,
                    'multiple': multiple
                })
            if tipo == 3:
                # buscar participantes
                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {idEcuesta}  "
                participantes = getData(sql2)
                # ahora buscar si ya como usuario envie mi respeusta
                integrantes = []
                for row in participantes:
                    integrantes.append({
                        'id': row[0],
                        'value': row[1],
                    })
                # buscar ganadores
                sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {idEcuesta} and ganador > 0  "
                ganadoresP = getData(sql2)
                ganadores = []
                for row in ganadoresP:
                    ganadores.append({
                        'id': row[0],
                        'value': row[1],
                    })
                encuestaTipo.append({
                    'tipo': tipo,
                    'idEcuesta': idEcuesta,
                    'pregunta': pregunta,
                    'premios': premios,
                    'participantes': integrantes,
                    'ganadores': ganadores,
                    'id_evento': id_evento
                })
            if tipo == 4:
                encuestaTipo.append({
                    'tipo': tipo,
                    'idEcuesta': idEcuesta,
                    'pregunta': pregunta,
                    'id_evento': id_evento
                })

            if tipo == 5:
                encuestaTipo.append({
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


@app.route('/api/mover_arriba_posicion_encuesta', methods=["POST"])
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

# get encuesta by codigo event


@app.route('/api/get_event_by_cod_front', methods=["GET"])
def get_event_by_cod_front():
    codigo = request.args.get('codigo', '')
    print(codigo)
    codigo = codigo[0:5]
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}'  "
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        # listar las encuestas para enviarlas de una vez
        sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' order by posicion asc  "
        # buscar por uid las encuestas q tenga en la db
        encuestas = getData(sql)
        encuestaTipo = []
        if encuestas:

            for en in encuestas:
                encuestaTipo.append({
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


# publicar evento


@app.route('/api/publicar_evento', methods=["POST"])
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
    socketio.emit('cambiarStatusEvent', {"codigo": codigo, "status": status})
    response = {
        'status': 1
    }
    return jsonify(response)


# activar modo live evento
@app.route('/api/modo_live_evento', methods=["POST"])
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
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    id_evento = evento[0]
    # update encuesta posicion 1 a play 1
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
        # buscar la encuesta uno ordenada por posicion
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

    socketio.emit('activarModoPresentacion', {
                  "codigo": codigo, "modo": modoLive})
    response = {
        'status': 1
    }
    return jsonify(response)

# cambiar encuesta activa en modo live evento


@app.route('/api/modo_live_evento_encuesta_activa', methods=["POST"])
@jwt_required()
def modo_live_evento_encuesta_activa():
    body = request.get_json()
    id_user = get_jwt_identity()
    codigo = body["codigo"]
    idEncuesta = body["id"]

    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  "
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    id_evento = evento[0]
    # updte evento tambien
    sql = f"""
        update mn_eventos set status = 1, modo = 1 where 
        id = '{id_evento}' and id_user = '{id_user}' 
        """
    updateEvento = updateData(sql)
    # update encuesta posicion 1 a play 1
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
    socketio.emit('cambioDeEncuesta', {
                  "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": idEncuesta})
    response = {
        'status': 1
    }
    return jsonify(response)

# get encuesta activa modo live event


@app.route('/api/get_encuesta_event_live',  methods=["GET"])
def get_encuesta_event_live():
    codigo = request.args.get('codigo', '')
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and modo = 1 "
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and play = 1 "
        en = getDataOne(sql)
        encuestaTipo = []
        play = 0
        if en:
            encuestaTipo.append({
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


# get encuesta by id en modo live modal
@app.route('/api/get_encuestas_by_id_live',  methods=["GET"])
@jwt_required()
def get_encuestas_by_id_live():
    id = request.args.get('id', '')
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id}' and id_user = '{id_user}' "
    # buscar por uid las encuestas q tenga en la db
    en = getDataOne(sql)
    encuestaTipo = []
    if en:
        encuestaTipo.append({
            'id': en[0],
            'tipo': en[1],
            'titulo': en[2],
            'posicion': en[3],
            'play': en[6],
            'multiple': en[7]
        })
        if en[1] == 1:
            # cargar opciones
            sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id}' "
            # buscar por uid las encuestas q tenga en la db
            opcionesDb = getData(sqlOp)
            opcionesData = []
            for op in opcionesDb:
                id_opcion = op[0]
                # buscar si hay votos en esta opcion
                sqlVo = f"SELECT * FROM mn_votos_choice where id_opcion = '{id_opcion}' "
                # buscar por uid las encuestas q tenga en la db
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
        if en[1] == 2:
            response = {
                "status": 1,
                "encuesta":  encuestaTipo,
            }
        if en[1] == 4:
            sql = f"SELECT * FROM mn_date_day where id_encuesta = '{id}' "
            # buscar por uid las encuestas q tenga en la db
            getDias = getData(sql)
            arrayDias = []
            arrayDate = []
            if getDias:
                for dia in getDias:
                    id_dia = dia[0]
                    # aqui buscar las horas del dia
                    sql = f"SELECT * FROM mn_date_horas where id_date_day = '{id_dia}' "
                    # buscar por uid las encuestas q tenga en la db
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


#get encuestas by id user not registered dashboard

# get encuesta by id en modo live modal
@app.route('/api/get_encuestas_by_id_user_not_registered_dashboard',  methods=["GET"])
def get_encuestas_by_id_user_not_registered_dashboard():
    id = request.args.get('id', '')
    id_user = request.args.get('p', '')
    sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id}' and id_user = '{id_user}' "
    # buscar por uid las encuestas q tenga en la db
    en = getDataOne(sql)
    encuestaTipo = []
    if en:
        encuestaTipo.append({
            'id': en[0],
            'tipo': en[1],
            'titulo': en[2],
            'posicion': en[3],
            'play': en[6],
            'multiple': en[7]
        })
        if en[1] == 1:
            # cargar opciones
            sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id}' "
            # buscar por uid las encuestas q tenga en la db
            opcionesDb = getData(sqlOp)
            opcionesData = []
            for op in opcionesDb:
                id_opcion = op[0]
                # buscar si hay votos en esta opcion
                sqlVo = f"SELECT * FROM mn_votos_choice where id_opcion = '{id_opcion}' "
                # buscar por uid las encuestas q tenga en la db
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
        if en[1] == 2:
            response = {
                "status": 1,
                "encuesta":  encuestaTipo,
            }
        if en[1] == 4:
            sql = f"SELECT * FROM mn_date_day where id_encuesta = '{id}' "
            # buscar por uid las encuestas q tenga en la db
            getDias = getData(sql)
            arrayDias = []
            arrayDate = []
            if getDias:
                for dia in getDias:
                    id_dia = dia[0]
                    # aqui buscar las horas del dia
                    sql = f"SELECT * FROM mn_date_horas where id_date_day = '{id_dia}' "
                    # buscar por uid las encuestas q tenga en la db
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


@app.route('/api/get_event_by_cod', methods=["GET"])
@jwt_required()
def get_event_by_cod():
    print("get event ")
    id_user = get_jwt_identity()
    codigo = request.args.get('codigo', '')
    print(codigo)
    codigo = codigo[0:5]
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  "
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' order by posicion asc  "
        # buscar por uid las encuestas q tenga en la db
        encuestas = getData(sql)
        encuestaTipo = []
        play = 0
        if encuestas:
            id_encuesta_primera = encuestas[0][0]
            for en in encuestas:
                if en[6] == 1:
                    play = en[0]
                encuestaTipo.append({
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
            response = {
                "status": 2
            }
    else:
        response = {
            "status": 0
        }

    return jsonify(response)


# sockets
@socketio.on('conectar')
def handle_join_room_event(data):
    socketId = rooms()
    print("id de usuario conectado", socketId)
    print("hola q tal estoy en el socket conectar")
    # aqui guardar en la db el cliente conectado
    sql = f"SELECT * FROM mn_clientes_conectados where id_user = '{data['username']}' and codigo_evento = '{data['room']}'  "
    cliente = getDataOne(sql)
    if cliente:
        print("ya esta conectado")
    else:
        # buscar si el dueño del evento para no sumarlo
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

    app.logger.info("{} has joined the room {}".format(
        data['username'], data['room']))
    join_room(data['room'])
    # en este emit debo enviar las personas conectadas al evento
    sql = f"SELECT * FROM mn_clientes_conectados where  codigo_evento = '{data['room']}'  "
    clientes = getData(sql)
    conectados = len(clientes)
    socketio.emit('join_room_announcement', {
                  'username': data['username'], 'codigo': data['room'], 'conectados': conectados})
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
    socketio.emit('join_room_disconect', {
                  'username': data['username'], 'codigo': data['room'], 'conectados': conectados})
    print('Client disconnected', request.sid)

# create poll simple modo live


@app.route('/api/create_poll_simple_live', methods=['POST'])
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
        # necesito saber la posicion de la ultima encuesta
        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc "
        # buscar por uid las encuestas q tenga en la db
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
            socketio.emit('cambioDeEncuesta', {
                          "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_tipo_encuesta})
        response = {
            'status': 1
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)






@app.route('/api/delete_poll_simple_live', methods=["POST"])
@jwt_required()
def delete_poll_simple_live():
    body = request.get_json()
    id = body["id"]
    id_opcion = body["id_opcion"]
    id_user = get_jwt_identity()
    print("id de la encuesta", id)
    print("id de la opcion", id_opcion)
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


@app.route('/api/delete_poll_simple_live_by_id', methods=["POST"])
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

        # buscar si quedan encuestas y poner activa la primera
        sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  "
        evento = getDataOne(sql)
        if evento:
            id_evento = evento[0]
            # buscar encuestas del evento
            sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and id_user = '{id_user}' order by posicion asc "
            misencuestas = getDataOne(sql)
            print(misencuestas)
            if misencuestas:
                id_encuesta_primera = misencuestas[0]
                # update
                sql = f"""
                                update  mn_tipo_encuesta set play = 1 where id = '{id_encuesta_primera}'  
                                """
                actualizar = deleteData(sql)
                socketio.emit('cambioDeEncuesta', {
                              "tipo": 3, "msj": "elimine una encuesta", "codigo": codigo, "id_encuesta": id_encuesta_primera})
            else:
                socketio.emit('cambioDeEncuesta', {
                              "tipo": 5, "msj": "sin encuestas", "codigo": codigo})

        response = {
            'status': actualizar,
        }
    else:
        response = {
            'status': 'error',
        }

    return jsonify(response)


#delete event by id by user not registered 

@app.route('/api/delete_poll_by_id_not_registered', methods=["POST"])
def delete_poll_by_id_not_registered():
        body = request.get_json()
        id_event = body["id_event"]
        id_encuesta = body["id_encuesta"]
        id_user = body["p"]
        #buscar si el evento existe 

        sql = f"SELECT * FROM mn_eventos where id = '{id_event}' and id_user = '{id_user}'  "
        evento = getDataOne(sql)
        if evento:
                sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id_encuesta}' and id_user = '{id_user}' and id_evento = '{id_event}'  "
                buscarTipo = getDataOne(sql)
                sql = f"""
                DELETE FROM `mn_eventos` WHERE  id = '{id_event}'
                """
                actualizar = deleteData(sql)
                tipo = 0
                if buscarTipo:
                        tipo = buscarTipo[1]
                        sql = f"""
                        DELETE FROM `mn_tipo_encuesta` WHERE  id = '{id_encuesta}'
                        """
                        actualizar = deleteData(sql)
                        if tipo == 1:
                                sql = f"""
                                DELETE FROM `mn_tipo_encuesta_choice` WHERE  id_tipo_encuesta = '{id_encuesta}'
                                """
                                actualizar = deleteData(sql)

                                sql = f"""
                                DELETE FROM `mn_votos_choice` WHERE  id_tipo_encuesta = '{id_encuesta}' 
                                """
                                actualizar = deleteData(sql)
                        if tipo == 2:
                                sql = f"""
                                DELETE FROM `mn_nube_palabras` WHERE  id_tipo_encuesta = '{id_encuesta}'
                                """
                                actualizar = deleteData(sql)
                        
                        if tipo == 4:
                                sql = f"""
                                DELETE FROM `mn_date_day` WHERE  id_encuesta = '{id_encuesta}'
                                """
                                actualizar = deleteData(sql)

                                sql = f"""
                                DELETE FROM `mn_date_horas` WHERE  id_encuesta = '{id_encuesta}'
                                """
                                actualizar = deleteData(sql)

                                sql = f"""
                                DELETE FROM `mn_date_horas_votos` WHERE  id_tipo_encuesta = '{id_encuesta}'
                                """
                                actualizar = deleteData(sql)


                        response = {
                                'status': 1,
                        }
                else:
                        response = {
                        'status': 'error',
                        }
        else:
                response = {
                        'status': 'error',
                }

        return jsonify(response)


@app.route('/api/_sortear1', methods=["GET"])
def sortear1():
    participantes = request.args.get('participantes', '')
    premios = request.args.get('premios', '')
    y = json.loads(participantes)
    # cantidad de participantes
    cantParticipantes = len(y)
    # lista de ganadores
    ganadores = []
    while len(ganadores) < int(premios):
        # generamos numero aleatorio
        n = random.randint(1, cantParticipantes)
        if n not in ganadores:
            # si no existe lo agrego
            ganadores.append(y[(n-1)])

    response = {
        'status': 1,
        'participantes': y,
        'ganadores': ganadores
    }
    return jsonify(response)


@app.route('/api/get_event_by_codigo_buscador', methods=["GET"])
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


# get conectados al rooms

@app.route('/api/get_users_conectados', methods=["GET"])
def get_users_conectados():
    codigo = request.args.get('codigo', '')

    print(request.sid)

    response = {
        'status': 1,
    }

    return jsonify(response)
