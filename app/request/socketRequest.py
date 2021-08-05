from app import app
from app import socketio
from flask import request, jsonify
from flask_socketio import join_room, leave_room,  close_room, rooms
from app.schemas import *


users = []

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
    global users
    print('Client disconnected', request.sid)

   
    
    leaveUser = userLeave(request.sid)
    leave_room(leaveUser['user']['room'])
    conectadosRoom = getRoomUsers(leaveUser['user']['room'])
    socketio.emit('join_room_disconect', {
        'username': leaveUser['user']['username'], 'codigo': leaveUser['user']['room'], 'conectados': conectadosRoom}, to=leaveUser['user']['room'])
    if conectadosRoom == None:
        close_room(leaveUser['user']['room'])


@socketio.on('desconectar')
def desconectarManual():
    global users
    print('Client disconnected de forma manual', request.sid)

   
    
    leaveUser = userLeave(request.sid)
    leave_room(leaveUser['user']['room'])
    conectadosRoom = getRoomUsers(leaveUser['user']['room'])
    socketio.emit('join_room_disconect', {
        'username': leaveUser['user']['username'], 'codigo': leaveUser['user']['room'], 'conectados': conectadosRoom}, to=leaveUser['user']['room'])
    if conectadosRoom == None:
        close_room(leaveUser['user']['room'])
    
    
    


# sockets
@socketio.on('joinRoom')
def joinRoom(data):
    print("id de usuario conectado", request.sid)
    userJoin(request.sid, data['username'], data['room'])
    conectadosRoom = getRoomUsers(data['room'])
    join_room(data['room'])
    # en este emit debo enviar las personas conectadas al evento
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
    usuarioActual = getCurrentUser(request.sid)
    print("usuario actual", usuarioActual)
    # en este emit debo enviar las personas conectadas al evento
    conectadosRoom = getRoomUsers(data['room'])
    print("hola room", rooms(request.sid))
    socketio.emit('pong', {
                  'username': data['username'], 'codigo': data['room'], 'conectados': conectadosRoom}, to=data['room'], callback=ack)
    return 'one', 2

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

