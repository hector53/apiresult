from app import app
from app import socketio
from flask import request, jsonify
from flask_socketio import join_room, leave_room,  close_room, rooms
from app.schemas import *


users = []
def getUserBySid(sid):
    status = 0
    #buscar user si existe el usuario con el username y el room 
    sql = f"SELECT * FROM mn_clientes_conectados where sid = '{sid}'  "
    # buscar por uid las encuestas q tenga en la db
    buscarUserinRoom = getDataOne(sql)
    if buscarUserinRoom:
        status = 1
    return status

def ingresarUser(id, id_user, room):
    status = 0
    #buscar user si existe el usuario con el username y el room 
    sql = f"SELECT * FROM mn_clientes_conectados where id_user = '{id_user}' and room = '{room}' "
    # buscar por uid las encuestas q tenga en la db
    buscarUserinRoom = getDataOne(sql)

    if buscarUserinRoom:
        status = 1
        #osea q ya existe el user en el room seguro esta abriendo una nueva pestaña 
    else:
        #no existe 
        sql = f"""
        INSERT INTO mn_clientes_conectados ( sid, room, id_user) VALUES
        (  '{id}', '{room}', '{id_user}') 
        """
        nuevoUserRoom = updateData(sql)
    return status


def getCountUsersRoom(room):
    sql = f"SELECT * FROM mn_clientes_conectados where  room = '{room}' "
    # buscar por uid las encuestas q tenga en la db
    buscarUsersInRoom = getData(sql)
    return len(buscarUsersInRoom)

def leaveUserRoom(sid):
    response = {
        "status": 0
    }
    #buscar user si existe el usuario con el username y el room 
    sql = f"SELECT * FROM mn_clientes_conectados where sid = '{sid}'  "
    # buscar por uid las encuestas q tenga en la db
    buscarUserinRoom = getDataOne(sql)

    if buscarUserinRoom:
        response = {
        "status": 1, 
        "room": buscarUserinRoom[2], 
        "username": buscarUserinRoom[3]
        }
        #si existe lo borro 
        sql = f"""
        delete from mn_clientes_conectados where sid = '{sid}'
        """
        deleteUserInRoom = updateData(sql)
    return response

def userJoin(id, username, room):
    global users
    user = {"id": id, "username": username, "room": room }
    users.append(user)
    print("usuarios conectados", users)
    return user

def getCurrentUser(id):
    global users
    return next(x for x in users if x["id"] == id )

def getCurrentUsername(username):
    global users
    return next(x for x in users if x["username"] == username )

def getRoomUsers(room):
    global users
    i = 0
    for row in users:
        if row["room"]==room:
            i=i+1
    return i

def userLeave(id):
    global users
    i = 0
    for row in users:
        if row["id"]==id:
            users.pop(i)
            return {"status":1, "user": row}
        i=i+1
    return {"status":0}


@socketio.event
def connect():
    print("cliente conectado DESDE CONEECT", request.sid)


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

    leaveUser = leaveUserRoom(request.sid)
    print("leave user di", leaveUser)
    if leaveUser["status"] == 1: 
        leave_room(leaveUser["room"])
        conectadosRoom = getCountUsersRoom(leaveUser["room"])
        socketio.emit('join_room_disconect', {
        'username': leaveUser["username"], 'codigo': leaveUser["room"], 'conectados': conectadosRoom}, to=leaveUser["room"])
        if conectadosRoom == 0:
            close_room(leaveUser["room"])
        return {"user": leaveUser["username"], "conectados": conectadosRoom}
    else:
        return 0

        #lo borre 
    
    
    


@socketio.on('desconectar')
def desconectarManual():
    global users
    print('Client disconnected manual', request.sid)

    leaveUser = leaveUserRoom(request.sid)
    print("leave user di", leaveUser)
    if leaveUser["status"] == 1: 
        leave_room(leaveUser["room"])
        conectadosRoom = getCountUsersRoom(leaveUser["room"])
        socketio.emit('join_room_disconect', {
        'username': leaveUser["username"], 'codigo': leaveUser["room"], 'conectados': conectadosRoom}, to=leaveUser["room"])
        if conectadosRoom == 0:
            close_room(leaveUser["room"])
        return {"user": leaveUser["username"], "conectados": conectadosRoom}
    else:
        return 0
    
    
    


# sockets
@socketio.on('joinRoom')
def joinRoom(data):
    print("id de usuario conectado", request.sid)
    joinUserRoom =  ingresarUser(request.sid, data['username'], data['room'])
    print("join user room statuys", joinUserRoom)
    if joinUserRoom == 0:
        join_room(data['room'])
    conectadosRoom = getCountUsersRoom(data['room'])
    socketio.emit('join_room_announcement', {
                  'username': data['username'], 'codigo': data['room'], 'conectados': conectadosRoom}, to=data['room'])

@socketio.on('enviarReaccion')
def enviarReaccion(data):
    print("enviar reaccion", request.sid)
    # en este emit debo enviar las personas conectadas al evento
    socketio.emit('recibiReaccion', {
                  'username': data['username'], 'codigo': data['room'], 'tipo': data['tipo']}, to=data['room'])
                  

@socketio.event
def ping(data):
    print("ping recibido del usuario: ",  data['username'])
    usuarioActual = getUserBySid(request.sid)
    conectadosRoom = getCountUsersRoom(data['room'])
    return {"user": data['username'], "ifUser": usuarioActual, "conectados": conectadosRoom}

def ack(data):
    print("me llego el callback")



@app.route('/api/desconectar_user_manual', methods=["POST"])
def desconectar_user_manual():
    print("llegue aqui")
    body = request.get_json()
    username = body["username"]
    room = body["room"]
    getUser = getCurrentUsername(username)
    print("get user: ", getUser)

    response = {
        "status": 1
    }

    return jsonify(response)

