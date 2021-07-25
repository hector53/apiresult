from app import app
from app import socketio
from flask import request
from flask_socketio import join_room, leave_room,  close_room
from app.schemas import *


@socketio.event
def connect():
    print("cliente conectado DESDE CONEECT", request.sid)


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)
    sql = f"SELECT * FROM mn_clientes_conectados where  id_room = '{request.sid}'  "
    clientes = getDataOne(sql)
    if clientes: 
        room = clientes[2]
        id_user = clientes[3]
        leave_room(room)
    sql = f"""
        delete from mn_clientes_conectados where id_room = '{request.sid}' 
        """
    actualizar = updateData(sql)
    if clientes:
        sql = f"SELECT * FROM mn_clientes_conectados where  codigo_evento = '{room}'  "
        clientes = getData(sql)
        conectados = len(clientes)
        if conectados == None:
            close_room(room)
        else:
            socketio.emit('join_room_disconect', {
            'username': id_user, 'codigo': room, 'conectados': conectados}, to=room)
    
    


# sockets
@socketio.on('joinRoom')
def joinRoom(data):
    print("id de usuario conectado", request.sid)
    #buscar q el usuario a conectarse no este en el room 
    sql = f"SELECT * FROM mn_clientes_conectados where  codigo_evento = '{data['room']}' and id_user = '{data['username']}'  "
    userRoom = getDataOne(sql)

    print("valor busqueda rroom", userRoom)
    if userRoom == None:
        #no existe por lo tanto lo guardo de resto nei
        sql = f"""
        INSERT INTO mn_clientes_conectados ( id_room, codigo_evento, id_user) VALUES ( '{request.sid}',
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
                  'username': data['username'], 'codigo': data['room'], 'conectados': conectados}, to=data['room'])
                  
    print("emiti el socket")
