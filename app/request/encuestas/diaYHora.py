from flask import request, jsonify
from app import app
from app import socketio
from app.schemas import *
from flask_jwt_extended import  jwt_required, get_jwt_identity
from datetime import datetime
from dateutil import tz
import json
import string
import random
from app.request.funciones import *
mesFecha = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep",
            "Oct", "Nov", "Dic"]
def codigoAleatorio(s):
    ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k=s))
    return str(ran)
    

# encuesta dia y hora modo not user

@app.route('/api/create_diayhora_not_user', methods=['POST'])
def create_diayhora_not_user():
    body = request.get_json()
    print(body)
    titulo = body["titulo"]
    dias = body["dias"]
    horas = body["horas"]
    horasArray = json.loads(horas)
    miCodigo = codigoAleatorio(5)
    cookieNotUser = body["cookieNotUser"]
    ipWeb = body["ipWeb"]
    zonaHoraria = body["zonaHoraria"]
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(zonaHoraria)
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
        INSERT INTO mn_tipo_encuesta ( tipo, titulo, id_user, id_evento, fecha) VALUES ( 4,
        '{titulo}', '{cookieNotUser}', '{id_evento}',  '{datetime.now()}'  ) 
        """
    id_tipo_encuesta = updateData(sql)

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

    response = {
        'codigo': miCodigo,
        'status': 1
    }
    return jsonify(response)

# create dia y hora live q
@app.route('/api/create_diayhora_live', methods=['POST'])
@jwt_required()
def create_diayhora_live():
    body = request.get_json()
    titulo = body["titulo"]
    dias = body["dias"]
    diasArray = json.loads(dias)
    horas = body["horas"]
    horasArray = json.loads(horas)
    print(horasArray)
    # cantidad de participantes
    codigo = body["codigo"]
    activar = body["activar"]
    id_user = get_jwt_identity()
    # METHOD 1: Hardcode zones:
    zonaHoraria = body["zonaHoraria"]
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(zonaHoraria)
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
                INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento,  fecha) VALUES ( 4,
                '{titulo}', '{posicion}', '{id_user}', '{id_evento}',  '{datetime.now()}'  ) 
                """
        id_tipo_encuesta = updateData(sql)
        # agregar participantes
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
            socketio.emit('CrearEncuestayActivar', {
                           "msj": "crearon una encuesta y la activaron", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)
        else:
            socketio.emit('GuardarEncuesta', {
            "msj": "crearon una encuesta, la guardaron pero no la activaron", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)

        response = {
            'status': 1,
            'id': id_tipo_encuesta,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)


# editar encueta dia y hora
@app.route('/api/edit_diayhora_live', methods=['POST'])
@jwt_required()
def edit_diayhora_live():
    body = request.get_json()
    titulo = body["titulo"]
    dias = body["dias"]
    diasArray = json.loads(dias)
    horas = body["horas"]
    horasArray = json.loads(horas)
    print(horasArray)
    # cantidad de participantes
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
                # inserto
                sql = f"""
                                INSERT INTO mn_date_day ( fecha, id_encuesta) VALUES ( '{fechaDia}',
                                '{id_tipo_encuesta}' ) 
                                """
                id_dia = updateData(sql)
                idsDiaNoBorrar.append(id_dia)
                for h in d['horas']:
                    horaini = h['ini']
                    horaini = datetime.strptime(
                        horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
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
                # editar
                print("editar horas")
                idsDiaNoBorrar.append(idDb)
                for h in d['horas']:
                    idHoraDb = h['id']
                    if idHoraDb == 0:
                        # inserto
                        horaini = h['ini']
                        horaini = datetime.strptime(
                            horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
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
                        # edito
                        horaini = h['ini']
                        horaini = datetime.strptime(
                            horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
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

        # borrar los ids q no esten incluidos en el array de dias y horas
        #arrayT = [2,3,4,5,6]
        notBorrar = ''
        f = 1

        for t in idsDiaNoBorrar:
            if f == len(idsDiaNoBorrar):
                notBorrar = notBorrar + str(t)
            else:
                notBorrar = notBorrar + str(t) + ','
            f = f+1

        sql = f"""
                delete from mn_date_day where id not in ({notBorrar}) and id_encuesta = '{id_tipo_encuesta}'
                """
        print(sql)
        borrarSobrantes = updateData(sql)

        notBorrar = ''
        f = 1

        for t in idsHoraNoBorrar:
            if f == len(idsHoraNoBorrar):
                notBorrar = notBorrar + str(t)
            else:
                notBorrar = notBorrar + str(t) + ','
            f = f+1

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

        sql = f"SELECT * FROM mn_tipo_encuesta where  id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}' "
        tipoEncuesta = getDataOne(sql)
        playEncuesta = tipoEncuesta[6]

        sql = f"""
        update mn_tipo_encuesta set titulo = '{titulo}' where 
        id_evento = '{id_evento}' and id_user = '{id_user}' and id = '{id_tipo_encuesta}'
        """
        tipoEncuesta = updateData(sql)



        

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

            if playEncuesta==1:
                socketio.emit('cambioDeEncuesta', {
                       "msj": "editaron la encuesta activa", "codigo": codigo, "id_encuesta": id_tipo_encuesta}, to=codigo)

        response = {
            'status': 1,
            'id': id_tipo_encuesta,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)



#edit dia hora user not registered 


# editar encueta dia y hora
@app.route('/api/edit_diayhora_user_not_registered', methods=['POST'])
def edit_diayhora_user_not_registered():
    body = request.get_json()
    titulo = body["titulo"]
    dias = body["dias"]
    diasArray = json.loads(dias)
    horas = body["horas"]
    horasArray = json.loads(horas)
    print(horasArray)
    id_evento = body["id_evento"]
    id_tipo_encuesta = body["id_encuesta"]
    id_user = body["p"]
    # METHOD 1: Hardcode zones:
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Caracas')
    sql = f"SELECT * FROM mn_eventos where id = '{id_evento}' and id_user = '{id_user}'  "
    evento = getDataOne(sql)
    if evento:
        idsDiaNoBorrar = []
        idsHoraNoBorrar = []
        sql = f"""
        update mn_eventos set titulo = '{titulo}' where 
        id = '{id_evento}' and id_user = '{id_user}' 
        """
        eventoupdate = updateData(sql)
        sql = f"""
        update mn_tipo_encuesta set titulo = '{titulo}' where 
        id = '{id_tipo_encuesta}' and id_user = '{id_user}' 
        """
        tipoEncuesta = updateData(sql)
        for d in horasArray:
            idDb = d['idDb']
            fechaDia = d['id']
            if idDb == 0:
                # inserto
                sql = f"""
                                INSERT INTO mn_date_day ( fecha, id_encuesta) VALUES ( '{fechaDia}',
                                '{id_tipo_encuesta}' ) 
                                """
                id_dia = updateData(sql)
                idsDiaNoBorrar.append(id_dia)
                for h in d['horas']:
                    horaini = h['ini']
                    horaini = datetime.strptime(
                        horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
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
                # editar
                print("editar horas")
                idsDiaNoBorrar.append(idDb)
                for h in d['horas']:
                    idHoraDb = h['id']
                    if idHoraDb == 0:
                        # inserto
                        horaini = h['ini']
                        horaini = datetime.strptime(
                            horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
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
                        # edito
                        horaini = h['ini']
                        horaini = datetime.strptime(
                            horaini, '%Y-%m-%dT%H:%M:%S.%f%z')
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

        # borrar los ids q no esten incluidos en el array de dias y horas
        #arrayT = [2,3,4,5,6]
        notBorrar = ''
        f = 1

        for t in idsDiaNoBorrar:
            if f == len(idsDiaNoBorrar):
                notBorrar = notBorrar + str(t)
            else:
                notBorrar = notBorrar + str(t) + ','
            f = f+1

        sql = f"""
                delete from mn_date_day where id not in ({notBorrar}) and id_encuesta = '{id_tipo_encuesta}'
                """
        print(sql)
        borrarSobrantes = updateData(sql)

        notBorrar = ''
        f = 1

        for t in idsHoraNoBorrar:
            if f == len(idsHoraNoBorrar):
                notBorrar = notBorrar + str(t)
            else:
                notBorrar = notBorrar + str(t) + ','
            f = f+1

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

        response = {
            'status': 1,
            'id': id_tipo_encuesta,
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)


# votar encuesta dia y hora
@app.route('/api/votar_encuesta_dia_y_hora_front', methods=['POST'])
def votar_encuesta_dia_y_hora_front():
    body = request.get_json()
    hora = body["hora"]
    codigo = body["codigo"]
    id_evento = body["id_evento"]
    id_encuesta = body["id_encuesta"]
    id_user = body["p"]
    modoLive = body["liveMode"]
    # crear funciones para validar q el id del evento existe y q el usuario existe

    sql = f"SELECT * FROM mn_date_horas_votos where id_date_hora = '{hora}' and id_user = '{id_user}'  "
    votoHora = getDataOne(sql)
    if votoHora:
        # ya votó
        sql = f"""
                DELETE FROM mn_date_horas_votos where id_date_hora = '{hora}' and id_user = '{id_user}'
                and id_tipo_encuesta = '{id_encuesta}' and id_evento = '{id_evento}'
                """
        id_voto_hora = updateData(sql)
        response = {
            'status': 0
        }
    else:
        # votar
        sql = f"""
                INSERT INTO mn_date_horas_votos ( id_date_hora, id_user, id_tipo_encuesta, id_evento, fecha) VALUES ( '{hora}',
                '{id_user}', '{id_encuesta}', '{id_evento}', '{datetime.now()}'  ) 
                """
        id_voto_hora = updateData(sql)
        response = {
            'status': 1,
            'id_voto': id_voto_hora
        }

    if modoLive == 1:
        socketio.emit('cambioDeEncuesta', {
                      "tipo": 1, "msj": "cambia encuesta", "codigo": codigo, "id_encuesta": id_encuesta}, to=codigo)
    socketio.emit('respuestaDelVoto', {
                  "tipo": 4, "id_evento": id_evento, "msj": "Nueva voto en hora", "id_encuesta": id_encuesta}, to=codigo)

    return jsonify(response)


# get diayhora activo modo live
@app.route('/api/get_datos_diayhora_by_id_encuesta', methods=["GET"])
def get_datos_diayhora_by_id_encuesta():
    id_evento = request.args.get('id_evento', '')
    id_encuesta = request.args.get('id_encuesta', '')
    id_user = request.args.get('p', '')
    sql2 = f"SELECT * FROM mn_tipo_encuesta where id = {id_encuesta} and id_evento = '{id_evento}'  "
    tipoEncuesta = getDataOne(sql2)
    if tipoEncuesta:
        print(tipoEncuesta)
        # buscar participantes
        sql2 = f"SELECT * FROM mn_date_day where id_encuesta = {id_encuesta}  "
        dias = getData(sql2)
        # ahora buscar si ya como usuario envie mi respeusta
        diasyhoras = []
        # buscar horas ganadoras para tenerlas aquí :D
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
                # buscar los votos de esta hora y si ha votado en esta hora
                sql2 = f"SELECT * FROM mn_date_horas_votos where id_date_hora = {id_hora}  "
                votosHoras = getData(sql2)
                cantVotosHoras = len(votosHoras)
                # buscar si el usuario voto en esta hora
                sql2 = f"SELECT * FROM mn_date_horas_votos where id_date_hora = {id_hora} and id_user = '{id_user}'  "
                siVoteHora = getData(sql2)
                if siVoteHora:
                    sivoteH = 1
                else:
                    sivoteH = 0

                # ver si es ganador o no
                votoGanador = 0
                if siHayMayorVoto == 1:
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

        # buscar cantidad de votos totales de la encuesta
        sql2 = f"SELECT * FROM mn_date_horas_votos where id_tipo_encuesta = {id_encuesta}  "
        votosTotales = getData(sql2)
        # buscar cantidad de usuarios q han votado
        sql2 = f"SELECT count(DISTINCT id_user) as usuarios FROM `mn_date_horas_votos` where id_tipo_encuesta = '{id_encuesta}'  "
        usuariosTotales = getDataOne(sql2)
        response = {
            'status': 1,
            'dias': diasyhoras,
            'votosTotales': len(votosTotales),
            'usuariosTotales': usuariosTotales[0]
        }
    else:
        response = {
            'status': 0
        }

    return jsonify(response)