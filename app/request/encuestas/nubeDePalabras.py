from flask import request, jsonify
from app import app
from app import socketio
from app.schemas import *
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import string
import random
from app.request.funciones import *

def codigoAleatorio(s):
    ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k=s))
    return str(ran)

# encuesta nube not user
@app.route('/api/create_nube_not_user', methods=['POST'])
def create_nube_not_user():
    body = request.get_json()
    print(body)
    titulo = body["titulo"]
    miCodigo = codigoAleatorio(5)
    cookieNotUser = body["cookieNotUser"]
    ipWeb = body["ipWeb"]
    # consultar si el usuario existe sino guardarlo
    sql = f"SELECT * FROM mn_users_cookie where cookie = '{cookieNotUser}' "
    getUser = getDataOne(sql)
    if getUser:
        print("ya existe")
    else:
        # guardarlo
        sql = f"""
                INSERT INTO mn_users_cookie ( name, ip, cookie, fecha) VALUES ( 'guest',
                '{ipWeb}', '{cookieNotUser}', '{datetime.now()}'  ) 
                """
        id_user = updateData(sql)

    sql = f"""
        INSERT INTO mn_eventos ( titulo, descripcion, codigo, id_user, modo, tipoUser, status, fecha) VALUES ( '{titulo}',
        '', '{miCodigo}', '{cookieNotUser}', 0, 0, 1,  '{datetime.now()}'  ) 
        """
    id_evento = updateData(sql)
    sql = f"""
        INSERT INTO mn_tipo_encuesta ( tipo, titulo, id_user, id_evento, fecha) VALUES ( 2,
        '{titulo}', '{cookieNotUser}', '{id_evento}',  '{datetime.now()}'  ) 
        """
    id_tipo_encuesta = updateData(sql)

    response = {
        'codigo': miCodigo,
        'status': 1
    }
    return jsonify(response)


# nube de palabras create

@app.route('/api/create_poll_nube_palabras_live', methods=['POST'])
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
        # necesito saber la posicion de la ultima encuesta
        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc "
        # buscar por uid las encuestas q tenga en la db
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

#add nbube live front 

@app.route('/api/add_palabra_live_front', methods=['POST'])
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
    if modoLive == 1:
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta})
    socketio.emit('respuestaDelVoto', {
                  "tipo": 2, "id_evento": id_evento, "msj": "Nueva palabra", "id_encuesta": id_encuesta})

    response = {
        'status': id_nube_palabras
    }

    return jsonify(response)

#get respuestas 
@app.route('/api/get_respuestas_by_user_nube_palabras', methods=["GET"])
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
        # ahora buscar si ya como usuario envie mi respeusta
        sql4 = f"SELECT * FROM mn_nube_palabras where id_tipo_encuesta = {id_encuesta} and id_evento = '{id_evento}' and id_user = '{id_user}'  "
        nubePalabrasRespuesta = getData(sql4)
        siRespondi = 0
        if nubePalabrasRespuesta:
            siRespondi = 1

        response = {
            'status': 1,
            'palabras': nubePalabras,
            'siRespondi': siRespondi,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)

#guardar nube de palabras en dashboard add normal
@app.route('/api/guardar_pregunta_tipo_2', methods=["POST"])
@jwt_required()
def guardar_pregunta_tipo_2():
    print("llegue aqui")
    body = request.get_json()
    id = body["id"]
    pregunta = body["pregunta"]
    id_user = get_jwt_identity()
    codigo = body["codigo"]
    # buscar id del evento por le codigo
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}' "
    # buscar por uid las encuestas q tenga en la db
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
        # necesito saber la posicion de la ultima encuesta
        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc "
        # buscar por uid las encuestas q tenga en la db
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


# edit poll nuibe de palabras live
@app.route('/api/edit_nube_palabras_live', methods=['POST'])
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
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id})

    response = {
        'status': 1,
    }

    return jsonify(response)


# edit poll nuibe de palabras live
@app.route('/api/edit_nube_palabras_user_not_registered', methods=['POST'])
def edit_nube_palabras_user_not_registered():
    body = request.get_json()
    print(body)
    pregunta = body["pregunta"]
    id = body["id"]
    id_user = body["p"]
    id_evento = body["id_evento"]
    sql = f"SELECT * FROM mn_eventos where id = '{id_evento}' and id_user = '{id_user}'  "
    evento = getDataOne(sql)
    if evento:
        #busca si la encuesta existe
        sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id}' and id_user = '{id_user}'  "
        tipo_encuesta = getDataOne(sql)
        if tipo_encuesta:
            #aqui si puedo hacer un update 
            sql = f"""
            update mn_eventos set titulo = '{pregunta}' where 
            id = '{id_evento}' and id_user = '{id_user}' 
            """
            eventoupdate = updateData(sql)
            sql = f"""
            update mn_tipo_encuesta set titulo = '{pregunta}' where 
            id = '{id}' and id_user = '{id_user}' 
            """
            tipoEncuesta = updateData(sql)

            response = {
                'status': 1,
            }
        else:
            response = {
            'status': 0,
            }
    else:
        response = {
        'status': 0,
        }

    return jsonify(response)
