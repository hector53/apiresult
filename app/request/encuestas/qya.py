from flask import request, jsonify
from app import app
from app import socketio
from app.schemas import *
from flask_jwt_extended import  jwt_required, get_jwt_identity
from datetime import datetime
from app.request.funciones import *


# q&a live
@app.route('/api/create_poll_qya_live', methods=['POST'])
@jwt_required()
def create_poll_qya_live():
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
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento, fecha) VALUES ( 5,
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

#create qya pregunta add normal

@app.route('/api/guardar_pregunta_tipo_5', methods=["POST"])
@jwt_required()
def guardar_pregunta_tipo_5():
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
                ( 5, '{pregunta}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
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


# add question qya front
@app.route('/api/add_qya_live_front', methods=['POST'])
def add_qya_live_front():
    body = request.get_json()
    pregunta = body["pregunta"]
    id_evento = body["id_evento"]
    id_encuesta = body["id_encuesta"]
    codigo = body["codigo"]
    id_user = body["p"]
    modoLive = body["liveMode"]
    parent = body["parent"]

    sql = f"""
        INSERT INTO mn_qya_q ( texto, id_user, id_encuesta, id_evento, parent, date) VALUES ( '{pregunta}',
        '{id_user}', '{id_encuesta}', '{id_evento}', '{parent}', '{datetime.now()}'  ) 
        """
    id_qya = updateData(sql)
    if modoLive == 1:
        print("cambo de encuesta aiadjsouasdoisadhsadijsadihijlsadd")
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta})
    else:
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 6, "tipoEncuesta": 5, "msj": "actualizar encuesta modo normal", "codigo": codigo, "id_encuesta": id_encuesta})
    socketio.emit('respuestaDelVoto', {
                  "tipo": 5, "id_evento": id_evento, "msj": "Nueva pregunta", "id_encuesta": id_encuesta})

    response = {
        'status': id_qya
    }

    return jsonify(response)




# edit question qya front
@app.route('/api/edit_qya_live_front', methods=['POST'])
def edit_qya_live_front():
    body = request.get_json()
    pregunta = body["pregunta"]
    id_evento = body["id_evento"]
    id_encuesta = body["id_encuesta"]
    codigo = body["codigo"]
    id_user = body["p"]
    modoLive = body["liveMode"]
    idP = body["idP"]

    # buscar la pregunta pra ver si es del usuario
    sql2 = f"SELECT * FROM mn_qya_q where id_encuesta = {id_encuesta} and id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{idP}'  "
    getPregunta = getData(sql2)
    if getPregunta:
        sql = f"""
                update mn_qya_q set texto = '{pregunta}' where id = '{idP}'
                """
        updateQYA = updateData(sql)
        response = {
            'status': 1
        }
        if modoLive == 1:
            socketio.emit('cambioDeEncuesta', {
                          "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta})
        socketio.emit('respuestaDelVoto', {
                      "tipo": 5, "id_evento": id_evento, "msj": "Nueva pregunta", "id_encuesta": id_encuesta})
    else:
        response = {
            'status': 0
        }

    return jsonify(response)

# delete pregunta by admin
@app.route('/api/delete_qya_live_admin', methods=['POST'])
def delete_qya_live_admin():
    body = request.get_json()
    id_evento = body["id_evento"]
    id_encuesta = body["id_encuesta"]
    codigo = body["codigo"]
    id_user = body["p"]
    idP = body["idP"]
    modoLive = body["liveMode"]

    # buscar la pregunta pra ver si es del usuario
    sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}' and id_user = '{id_user}'  "
    getEncuestas = getData(sql2)
    if getEncuestas:
        sql = f"""
                delete from mn_qya_q where id =  '{idP}'
                """
        updateQYA = updateData(sql)

        sql = f"""
                delete from mn_qya_q where parent =  '{idP}'
                """
        updateQYA = updateData(sql)
        response = {
            'status': 1
        }

        if modoLive == 1:
            print("cambo de encuesta aiadjsouasdoisadhsadijsadihijlsadd")
            socketio.emit('cambioDeEncuesta', {
                          "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta})
        else:
            socketio.emit('cambioDeEncuesta', {
                          "tipo": 6, "tipoEncuesta": 5, "msj": "actualizar encuesta modo normal", "codigo": codigo, "id_encuesta": id_encuesta})
        socketio.emit('respuestaDelVoto', {
                      "tipo": 5, "id_evento": id_evento, "msj": "borre una pregunta", "id_encuesta": id_encuesta})
    else:
        response = {
            'status': 0
        }

    return jsonify(response)

# delete prefunta by user
@app.route('/api/delete_qya_live_user', methods=['POST'])
def delete_qya_live_user():
    body = request.get_json()
    id_evento = body["id_evento"]
    id_encuesta = body["id_encuesta"]
    codigo = body["codigo"]
    id_user = body["p"]
    idP = body["idP"]
    modoLive = body["liveMode"]

    # buscar la pregunta pra ver si es del usuario
    sql2 = f"SELECT * FROM mn_qya_q where id = {idP} and id_evento = '{id_evento}' and id_encuesta = '{id_encuesta}' and id_user = '{id_user}'  "
    getQYA = getData(sql2)
    if getQYA:
        sql = f"""
                delete from mn_qya_q where id =  '{idP}'
                """
        updateQYA = updateData(sql)

        sql = f"""
                delete from mn_qya_q where parent =  '{idP}'
                """
        updateQYA = updateData(sql)
        response = {
            'status': 1
        }
        if modoLive == 1:
            socketio.emit('cambioDeEncuesta', {
                          "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta})
        socketio.emit('respuestaDelVoto', {
                      "tipo": 5, "id_evento": id_evento, "msj": "borre una pregunta", "id_encuesta": id_encuesta})
    else:
        response = {
            'status': 0
        }

    return jsonify(response)



# like encuesta qya
@app.route('/api/like_encuesta_qya_front', methods=['POST'])
def like_encuesta_qya_front():
    body = request.get_json()
    qya = body["qya"]
    codigo = body["codigo"]
    id_evento = body["id_evento"]
    id_encuesta = body["id_encuesta"]
    id_user = body["p"]
    modoLive = body["liveMode"]
    # crear funciones para validar q el id del evento existe y q el usuario existe

    sql = f"SELECT * FROM mn_qya_q where id = '{qya}' and id_evento = '{id_evento}' and id_encuesta = '{id_encuesta}'  "
    getQYA = getDataOne(sql)
    likeCount = int(getQYA[6])

    sql = f"SELECT * FROM mn_qya_like where id_qya_q = '{qya}' and id_user = '{id_user}'  "
    likeQYA = getDataOne(sql)
    if likeQYA:
        # ya votó
        sql = f"""
                DELETE FROM mn_qya_like where id = '{likeQYA[0]}' and id_user = '{id_user}'
                """
        borrarQYA = updateData(sql)
        likeCount = likeCount - 1
        response = {
            'status': 0
        }
    else:
        # votar
        sql = f"""
                INSERT INTO mn_qya_like ( id_qya_q, id_user, id_encuesta, id_evento, date) VALUES ( '{qya}',
                '{id_user}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
                """
        id_like_qya = updateData(sql)
        likeCount = likeCount + 1
        response = {
            'status': 1,
            'qya': id_like_qya
        }
    sql = f"""
        update  mn_qya_q set like_count = '{likeCount}' where 
        id = '{qya}' and id_evento = '{id_evento}' and id_encuesta = '{id_encuesta}' 
        """
    id_like_qya = updateData(sql)

    if modoLive == 1:
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta})
    socketio.emit('respuestaDelVoto', {
                  "tipo": 5, "id_evento": id_evento, "msj": "Nueva voto en hora", "id_encuesta": id_encuesta})

    return jsonify(response)


# get qya front
@app.route('/api/get_preguntas_qya_front', methods=["GET"])
def get_preguntas_qya_front():
    id_evento = request.args.get('id_evento', '')
    id_encuesta = request.args.get('id_encuesta', '')
    id_user = request.args.get('p', '')
    sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}'  "
    tipoEncuesta = getData(sql2)
    if tipoEncuesta:
        print("buscar qya siu tiene preguntas")
        sql3 = f"SELECT  * FROM mn_qya_q where id_encuesta = '{id_encuesta}' and id_evento = '{id_evento}' and parent = 0 order by like_count desc  "
        getQyA = getData(sql3)

        PreguntasEncuestaQyA = []
        for row in getQyA:
            # buscar las respuestas a la pregunta
            sql3 = f"SELECT  * FROM mn_qya_q where id_encuesta = '{id_encuesta}' and id_evento = '{id_evento}' and parent = '{row[0]}' order by id desc  "
            replyQyA = getData(sql3)
            replyEncuestaQyA = []
            for row2 in replyQyA:
                replyEncuestaQyA.append({
                    'id': row2[0],
                    'texto': row2[1],
                    'usuario': "Moderador",
                    'fecha': time_passed(str(row2[7]))
                })

            # buscar nomb re de uysuario
            sql3 = f"SELECT  * FROM mn_users where id = '{row[2]}'   "
            getUser = getDataOne(sql3)
            if getUser:
                nombreUsuario = getUser[1] + " " + getUser[2]
            else:
                nombreUsuario = "Anonimo"

            PreguntasEncuestaQyA.append({
                'id': row[0],
                'texto': row[1],
                'usuario': nombreUsuario,
                'id_user': row[2],
                'likes': row[6],
                'fecha': time_passed(str(row[7])),
                'reply': replyEncuestaQyA
            })

        response = {
            'status': 1,
            'preguntas': PreguntasEncuestaQyA,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)