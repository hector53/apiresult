from flask import request, jsonify
from app import app
from app import socketio
from app.schemas import *
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import random
import json
from app.request.funciones import *

# create sorteo live
@app.route('/api/create_sorteo_live', methods=['POST'])
@jwt_required()
def create_sorteo_live():
    body = request.get_json()
    print(body)
    titulo = body["titulo"]
    participantes = body["participantes"]
    participantesArray = json.loads(participantes)
    # cantidad de participantes
    premios = body["premios"]
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
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento, premios, fecha) VALUES ( 3,
                '{titulo}', '{posicion}', '{id_user}', '{id_evento}', '{premios}',  '{datetime.now()}'  ) 
                """
        id_tipo_encuesta = updateData(sql)
        # agregar participantes
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
            socketio.emit('CrearEncuestayActivar', {
                           "msj": "crearon una encuesta y la activaron", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)
        else:
            socketio.emit('GuardarEncuesta', {
            "msj": "crearon una encuesta, la guardaron pero no la activaron", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)

        # buscar participantes
        sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_tipo_encuesta}  "
        participantes = getData(sql2)
        # ahora buscar si ya como usuario envie mi respeusta
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

# edit sorteo modal live


@app.route('/api/edit_sorteo_live_modal', methods=['POST'])
@jwt_required()
def edit_sorteo_live_modal():
    body = request.get_json()
    print(body)
    titulo = body["titulo"]
    participantes = body["participantes"]
    participantesArray = json.loads(participantes)
    print("participantes", participantesArray)
    # cantidad de participantes
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

        # ahora borro los participantes viejos y añado los nuevos
        sql = f"""
                DELETE FROM `mn_sorteos_participantes` WHERE  id_encuesta = '{id_encuesta}'
                """
        actualizar = deleteData(sql)

        # agregar participantes
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
                        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_encuesta}'
                        """
            tipoEncuesta = updateData(sql)
            socketio.emit('CrearEncuestayActivar', {
                           "msj": "crearon una encuesta y la activaron", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)
        else:
            socketio.emit('GuardarEncuesta', {
            "msj": "crearon una encuesta, la guardaron pero no la activaron", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)

            sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and id = '{id_encuesta}' and play = 1  "
            tipoE = getDataOne(sql)
            if tipoE:
                socketio.emit('cambioDeEncuesta', {  "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)

        

        response = {
            'status': 1,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)


# get sorteo by id encuesta
# get sorteo activo modo live
@app.route('/api/get__sorteo_by_id_encuesta_modal', methods=["GET"])
def get__sorteo_by_id_encuesta_modal():
    id_encuesta = request.args.get('id_encuesta', '')
    id_user = request.args.get('p', '')
    sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_user = '{id_user}'  "
    tipoEncuesta = getDataOne(sql2)
    if tipoEncuesta:
        print(tipoEncuesta)
        # buscar participantes
        sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_encuesta}  "
        participantes = getData(sql2)
        # ahora buscar si ya como usuario envie mi respeusta
        integrantes = ''

        for row in participantes:
            integrantes = integrantes + row[1] + '\n'

        response = {
            'status': 1,
            'titulo': tipoEncuesta[2],
            'participantes': integrantes,
            'premios': tipoEncuesta[9],
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)

@app.route('/api/sortear_sorteo_live', methods=['POST'])
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
        # generamos numero aleatorio
        n = random.randint(1, cantParticipantes)
        if n not in ganadores:
            # si no existe lo agrego
            ganadores.append(participantes[(n-1)])
            # update table participantes al ganador
            print("ganador", participantes[(n-1)]['id'])
            sql = f"""
                        update mn_sorteos_participantes set ganador = 1 where 
                        id = '{participantes[(n-1)]['id']}' 
                        """
            guardarGanador = updateData(sql)

    socketio.emit('generarGanadorSorteo', {
                  "ganadores": ganadores, "msj": "generando ganadores", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)

    response = {
        'status': 1,
        'participantes': participantes,
        'ganadores': ganadores
    }

    return jsonify(response)

# get sorteo activo modo live
@app.route('/api/get_datos_sorteo_by_id_encuesta', methods=["GET"])
def get_datos_sorteo_by_id_encuesta():
    id_evento = request.args.get('id_evento', '')
    id_encuesta = request.args.get('id_encuesta', '')
    id_user = request.args.get('p', '')
    sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}'  "
    tipoEncuesta = getDataOne(sql2)
    if tipoEncuesta:
        print(tipoEncuesta)
        # buscar participantes
        sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_encuesta}  "
        participantes = getData(sql2)
        # ahora buscar si ya como usuario envie mi respeusta
        integrantes = []
        for row in participantes:
            integrantes.append({
                'id': row[0],
                'value': row[1],
            })

        # buscar ganadores
        sql2 = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = {id_encuesta} and ganador > 0  "
        ganadoresP = getData(sql2)
        ganadores = []
        for row in ganadoresP:
            ganadores.append({
                'id': row[0],
                'value': row[1],
            })

        response = {
            'status': 1,
            'participantes': integrantes,
            'premios': tipoEncuesta[9],
            'ganadores': ganadores
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)