from flask import request, jsonify
from app import app
from app import socketio
from app.schemas import *
from flask_jwt_extended import  jwt_required, get_jwt_identity
from datetime import datetime
from app.request.funciones import *


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
            socketio.emit('CrearEncuestayActivar', {
                           "msj": "crearon una encuesta y la activaron", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)
        else:
            socketio.emit('GuardarEncuesta', {
            "msj": "crearon una encuesta, la guardaron pero no la activaron", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)
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
    codigo = body["codigo"]
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

    socketio.emit('cambioDeEncuesta', {"msj": "borrando una opcion de lña encuesta simple", "codigo": codigo, "id_encuesta": id}, to=codigo)

    response = {
        'status': actualizar,
    }
    return jsonify(response)



@app.route('/api/create_poll_not_user', methods=['POST'])
def create_poll_not_user():
    body = request.get_json()
    print(body)
    pregunta = body["pregunta"]
    opciones = body["opciones"]
    miCodigo = body["miCodigo"]
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

#votar multiple choice
@app.route('/api/_votar_user_not', methods=["POST"])
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
    ipWeb = body["ipWeb"]
    miUid = cookieNotUser
    if login:
        status = 1
        sql = f"SELECT * FROM mn_users where id = '{miUid}' "
        getIP = getDataOne(sql)
        MiIp = getIP[7]
    else:
        status = 1
        sql = f"SELECT * FROM mn_users_cookie where cookie = '{miUid}' "
        print(sql)
        getIP = getDataOne(sql)
        MiIp = getIP[2]
    # buscar si esta encuesta es multiple respuesta o no
    sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and extra = 1   "
    print(sql2)
    encu = getDataOne(sql2)
    if encu:
        comprobarIp = comprobar_ip_multiple_choice(login, MiIp, miUid, id_encuesta)
        if comprobarIp == 0:
            return jsonify(result=5)

        # busco si el usuario ya voto en esta opcion
        sql2 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{miUid}' and id_opcion = '{id_opcion}'    "
        opciones = getData(sql2)
        if opciones:
            return jsonify(result=2)
        else:
            print("no voto")
            # guardar la votacion nueva
            sql = f"""
                        INSERT INTO mn_votos_choice ( id_opcion, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{id_opcion}',
                        '{miUid}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
                        """
            actualizar = updateData(sql)
            if actualizar:
                if modoLive == 1:
                    socketio.emit('cambioDeEncuesta', {
                                  "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)
                socketio.emit('respuestaDelVoto', {
                              "tipo": 1, "id_evento": id_evento, "msj": "votaste", "id_encuesta": id_encuesta}, to=codigo)
                return jsonify(result=status)
            else:
                return jsonify(result=3)
    else:
        sql2 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{miUid}'    "
        print(sql2)
        opciones = getData(sql2)
        print(opciones)
        if opciones:
            return jsonify(result=2)
        else:
            print("no voto")
            #funcion compropbar ip 
            comprobarIp = comprobar_ip_multiple_choice(login, MiIp, miUid, id_encuesta)
            if comprobarIp == 0:
                return jsonify(result=5)
            

            # guardar la votacion nueva
            sql = f"""
                        INSERT INTO mn_votos_choice ( id_opcion, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{id_opcion}',
                        '{miUid}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
                        """
            actualizar = updateData(sql)
            if actualizar:
                if modoLive == 1:
                    socketio.emit('cambioDeEncuesta', {
                                  "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)
                socketio.emit('respuestaDelVoto', {
                              "tipo": 1, "id_evento": id_evento, "msj": "votaste", "id_encuesta": id_encuesta}, to=codigo)
                return jsonify(result=status)
            else:
                return jsonify(result=3)





#funcion comprobar ip multiple choice 
def comprobar_ip_multiple_choice(login, MiIp, miUid, id_encuesta):
    if login:
        sql2 = f"SELECT * FROM mn_users where ip = '{MiIp}' and id NOT IN ({miUid})    "
        getUserIp = getData(sql2)
        if getUserIp:
            #existen por lo tanto buscar si han votado en esta encuesta 
            for user in getUserIp:
                sql2 = f"  SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{user[0]}'   "
                getUserIp2 = getData(sql2)
                print(sql2)
                if getUserIp2:
                    # si ha votado alguien en esta encuesta por lo tanto no necesito buscar mas y pailas 
                    return 0
        sql2 = f"SELECT * FROM mn_users_cookie where ip = '{MiIp}' and cookie NOT IN ('{miUid}')    "
        getUserIp = getData(sql2)
        if getUserIp:
            #existen por lo tanto buscar si han votado en esta encuesta 
            for user in getUserIp:
                sql2 = f"  SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{user[4]}'   "
                getUserIp2 = getData(sql2)
                if getUserIp2:
                    # si ha votado alguien en esta encuesta por lo tanto no necesito buscar mas y pailas 
                    return 0
    else:
        sql2 = f"SELECT * FROM mn_users where ip = '{MiIp}'     "
        getUserIp = getData(sql2)
        if getUserIp:
            #existen por lo tanto buscar si han votado en esta encuesta 
            for user in getUserIp:
                sql2 = f"  SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{user[0]}'   "
                getUserIp2 = getData(sql2)
                print(sql2)
                if getUserIp2:
                    # si ha votado alguien en esta encuesta por lo tanto no necesito buscar mas y pailas 
                    return 0
        sql2 = f"SELECT * FROM mn_users_cookie where ip = '{MiIp}' and cookie NOT IN ('{miUid}')    "
        print(sql2)
        getUserIp = getData(sql2)
        if getUserIp:
            #existen por lo tanto buscar si han votado en esta encuesta 
            for user in getUserIp:
                sql2 = f"  SELECT * FROM mn_votos_choice where id_tipo_encuesta = {id_encuesta} and id_user = '{user[4]}'   "
                getUserIp2 = getData(sql2)
                if getUserIp2:
                    # si ha votado alguien en esta encuesta por lo tanto no necesito buscar mas y pailas 
                    return 0
    return 1


#cancelar voto multiple choice
@app.route('/api/_cancelar_voto_not_registered', methods=["GET"])
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
    if modoLive == '1':
        print("llegue a emitir el cancelar voto")
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)
    socketio.emit('respuestaDelVoto', {
                  "tipo": 1, "id_evento": id_evento, "msj": "cancelo voto", "id_encuesta": id_encuesta}, to=codigo)
    return jsonify(response)

#get multiple choice by id encuesta
@app.route('/api/get_encuesta_by_id', methods=["GET"])
def get_encuesta_by_id():
    idEncuesta = request.args.get('id_encuesta', '')
    p = request.args.get('p', '')
    sql2 = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = {idEncuesta}  "
    print(sql2)
    opciones = getData(sql2)
    data = []
    if opciones:
        # buscar votos
        sql3 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {idEncuesta}  "
        print(sql3)
        votos = getData(sql3)
        totalVotos = len(votos)
        descripcionMeta = ''
        i = 0
        for row in opciones:
            # sacar porcentaje
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
            if i == 0:
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

            # buscar por uid si vote en la encuesta
            miUid = p
            sql3 = f"SELECT * FROM mn_votos_choice where id_user = '{miUid}' and id_tipo_encuesta = '{idEncuesta}'  "
            print(sql3)
            voto = getDataOne(sql3)

            if voto:
                siVote = 1
                miVoto = voto[1]
            else:
                siVote = 0
                miVoto = 0

            i = i+1

        response = {
            'status': 1,
            'totalVotos': totalVotos,
            'opciones': data,
            'siVote': siVote,
            'meta': descripcionMeta,
            'miVoto': miVoto,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)

#guardar multiple choice dashboard add normal

@app.route('/api/guardar_opciones_tipo_1', methods=["POST"])
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
        # consultar la posicion
        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion asc "
        # buscar por uid las encuestas q tenga en la db
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
        # ahora aqui si creo las opciones
        for opcion in opciones:
            opcionValue = opcion["opcion"]
            sql = f"""
                        INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{opcionValue}',
                        '{id_tipo}' ) 
                        """
            actualizar = updateData(sql)

        # cargar opciones
        sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id_tipo}' "
        # buscar por uid las encuestas q tenga en la db
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
        # comprar la opcion si no existe la creo, y si existe la actualizo
        for opcion in opciones:
            opcionValue = opcion["opcion"]
            idOpcion = opcion["id"]
            if idOpcion == 0:
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

        # cargar opciones
        sqlOp = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{id}' "
        # buscar por uid las encuestas q tenga en la db
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

#multiple choice result 

@app.route('/api/get_encuesta_by_id_result', methods=["GET"])
def get_encuesta_by_id_result():
    idEncuesta = request.args.get('id_encuesta', '')
    sql2 = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = {idEncuesta}  "
    opciones = getData(sql2)
    data = []
    if opciones:
        # buscar votos
        sql3 = f"SELECT * FROM mn_votos_choice where id_tipo_encuesta = {idEncuesta}  "
        votos = getData(sql3)
        totalVotos = len(votos)
        i = 0
        for row in opciones:
            # sacar porcentaje
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

            i = i+1

        response = {
            'status': 1,
            'totalVotos': totalVotos,
            'opciones': data,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)


# edit poll simple live


@app.route('/api/edit_poll_simple_live', methods=['POST'])
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
    activar = body["activar"]
    opcionesNueva = body["opcionesNueva"]
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  "
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
            
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
        # ahora insertar las nuevas
        for op2 in opcionesNueva:
            sql = f"""
                    INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{op2}',
                    '{id}' ) 
                    """
            actualizar = updateData(sql)


        sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' and id = '{id}'  "
        encuestaById = getDataOne(sql)
        playEncuesta = encuestaById[6]

        if modo == 1:
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
                            id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id}'
                            """
                tipoEncuesta = updateData(sql)
                socketio.emit('CrearEncuestayActivar', {
                                "msj": "crearon una encuesta y la activaron", "codigo": codigo, "id_encuesta": id}, to=codigo)
            else:
                socketio.emit('GuardarEncuesta', {"msj": "crearon una encuesta la guardaron pero no la activaron", "codigo": codigo, "id_encuesta": id}, to=codigo)
                if playEncuesta==1:
                    socketio.emit('cambioDeEncuesta', {"msj": "editaron la encuesta activa", "codigo": codigo, "id_encuesta": id}, to=codigo)

    response = {
        'status': 1,
    }

    return jsonify(response)

#edit multiple choice user not registered


# edit poll simple live


@app.route('/api/edit_poll_simple_user_not_registered', methods=['POST'])
def edit_poll_simple_user_not_registered():
    body = request.get_json()
    print(body)
    pregunta = body["pregunta"]
    opciones = body["opciones"]
    modo = body["modo"]
    id_evento = body["id_evento"]
    multiple = body["multiple"]
    id = body["id"]
    opcionesNueva = body["opcionesNueva"]
    id_user =  body["p"]

    sql = f"SELECT * FROM mn_eventos where id = '{id_evento}' and id_user = '{id_user}'  "
    evento = getDataOne(sql)
    if evento:
    #busca si la encuesta existe
        sql = f"SELECT * FROM mn_tipo_encuesta where id = '{id}' and id_user = '{id_user}'  "
        tipo_encuesta = getDataOne(sql)
        if tipo_encuesta:
            sql = f"""
            update mn_tipo_encuesta set titulo = '{pregunta}', extra = '{multiple}' where 
            id = '{id}' and id_user = '{id_user}' 
            """
            tipoEncuesta = updateData(sql)
            sql = f"""
            update mn_eventos set titulo = '{pregunta}' where 
            id = '{id_evento}' and id_user = '{id_user}' 
            """
            eventoupdate = updateData(sql)
            for op in opciones:
                opcionTexto = op["opcion"]
                opcionId = op["id"]
                sql = f"""
                update mn_tipo_encuesta_choice set opcion = '{opcionTexto}' where id = '{opcionId}' and id_tipo_encuesta = '{id}' 
                    """
                actualizar = updateData(sql)
            # ahora insertar las nuevas
            for op2 in opcionesNueva:
                sql = f"""
                INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{op2}',
                '{id}' ) 
                """
                actualizar = updateData(sql)


            response = {
                'status': 1,
            }
        else:
            response = {
                'status': 0,
            }
    else:
            response = {
            'status': 1,
            }

    return jsonify(response)