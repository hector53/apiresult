from app import app
from app import socketio
from flask import request
from flask_socketio import join_room, leave_room,  close_room
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
    if conectadosRoom == None:
        close_room(leaveUser['user']['room'])
    else:
        socketio.emit('join_room_disconect', {
        'username': leaveUser['user']['username'], 'codigo': leaveUser['user']['room'], 'conectados': conectadosRoom}, to=leaveUser['user']['room'])
    
    


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
                  

@socketio.on('ping')
def pingCliente(data):
    print("ping recibido del usuario: ",  data['username'])
    # en este emit debo enviar las personas conectadas al evento
    conectadosRoom = getRoomUsers(data['room'])
    socketio.emit('pong', {
                  'username': data['username'], 'codigo': data['room'], 'conectados': conectadosRoom}, to=data['room'])
