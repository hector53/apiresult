from flask import request, jsonify, abort, make_response, session
from app import app
from app import socketio
from app.schemas import *
from datetime import datetime, date, timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_socketio import join_room, leave_room, rooms
import time
import math
import string
import random
import json
from dateutil import tz
import smtplib
import email.message
import os
import stripe

from app.request.encuestas.multipleChoice import *
from app.request.encuestas.nubeDePalabras import *
from app.request.encuestas.sorteos import *
from app.request.encuestas.diaYHora import *
from app.request.encuestas.qya import *
from app.request.socketRequest import *


stripe.api_key = 'sk_test_51JPBa7D8x9NGALumLFYMEMSJjQBtdlRMjUQKqKc2krlX9SWb7I42g2IdarThKSO35P54gGkEOsEKSr7E0g6oHE9200yFd9j07Q'
price_id = 'price_1JPC1hD8x9NGALum2GYgj1qh'

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


@app.route('/api/set', methods=['GET'])
def setsesion():
    session['misesion'] = 'value'
    return 'ok'


@app.route('/api/getSession', methods=['GET'])
@jwt_required()
def getSession():
    current_user_id = get_jwt_identity()
    # buscar si el usuario tiene ip
    sql = f"SELECT * FROM mn_users where id = '{current_user_id}' "
    buscarUser = getDataOne(sql)
    if buscarUser:
        ip = buscarUser[7]
    else:
        ip = ''
    firtsName = buscarUser[1]
    lastName = buscarUser[2]
    email = buscarUser[3]
    username = buscarUser[4]
    premium = buscarUser[10]
    customerId = buscarUser[12]
    namePlan = ''
    if premium == 0:
        namePlan = 'Limitado'
    if premium == 2: 
        namePlan = 'Pro'


    return jsonify({"id": current_user_id, "ip": ip, "firtsName": firtsName, "lastName": lastName, "email": email, "username": username,
     "premium": premium, "namePlan": namePlan, "customerId": customerId }), 200

@app.route('/api/getSessionAndCodLive', methods=['GET'])
@jwt_required()
def getSessionAndCodLive():
    current_user_id = get_jwt_identity()
    cod = request.args.get('cod', '')
    print("codigo", cod)
    # buscar si el usuario tiene ip
    sql = f"SELECT * FROM mn_users where id = '{current_user_id}' "
    buscarUser = getDataOne(sql)
    if buscarUser:
        #existe entonces busco el evento 
        sql = f"SELECT * FROM mn_eventos where codigo = '{cod}' and id_user = '{current_user_id}' "
        buscarEvento = getDataOne(sql)
        if buscarEvento:
            if buscarEvento[9] == 1: 
                print("el evento esta disabled")
                status = 2
                #esta deshabilitado enviar status 2
            else:
                print("el evento no esta disabled")
                #esta bien enviar status 1
                status = 1
        else:
            status = 0
            
    else:
        #no existe enviar error
        status = 0

    response = {
    "status": status
    }
    return jsonify(response), 200


    


@app.route('/api/get_user_settings', methods=['GET'])
@jwt_required()
def get_user_settings():
    current_user_id = get_jwt_identity()
    # buscar si el usuario tiene ip
    sql = f"SELECT * FROM mn_users where id = '{current_user_id}' "
    buscarUser = getDataOne(sql)
   
    return jsonify({"userData": buscarUser}), 200


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


@app.route('/api/guardar_user_perfil', methods=['POST'])
@jwt_required()
def guardar_user_perfil():
    body = request.get_json()
    firstName = body["firstName"]
    lastName = body["lastName"]
    email = body["email"]
    username = body["username"]
    tipo = body["tipo"]
    currentPass = body["currentPass"]
    newPass = body["newPass"]
    id_user = get_jwt_identity()
    if firstName and lastName and email and username and tipo:
        if tipo == 1: 
            sql = f"""
            update mn_users set firstName = '{firstName}', lastName = '{lastName}', 
            email = '{email}', userName = '{username}' where   id = '{id_user}'  """
            print(sql)
            updateIpUser = updateData(sql)
            response = {
                'status': 1,
            }
            return jsonify(response)
        if tipo == 2: 
            #verficar q la contraseña actual sea la misma de la db
            sql = f"SELECT * FROM mn_users where id = '{id_user}' and pass = '{currentPass}'  "
            # buscar por uid las encuestas q tenga en la db
            userPassActual = getDataOne(sql)
            if userPassActual:
                sql = f"""
                update mn_users set firstName = '{firstName}', lastName = '{lastName}'
                , email = '{email}', userName = '{username}', pass = '{newPass}'  where   id = '{id_user}' """
                print(sql)
                updateIpUser = updateData(sql)
                response = {
                    'status': 1,
                }
                return jsonify(response)
            else: 
                 abort(make_response(jsonify(message="current pass incorrect"), 401))
    else:
         abort(make_response(jsonify(message="data user incorrect"), 401))



@app.route('/api/guardar_user_perfil_billing', methods=['POST'])
@jwt_required()
def guardar_user_perfil_billing():
    body = request.get_json()
    company = body["company"]
    address = body["address"]
    city = body["city"]
    zip = body["zip"]
    country = body["country"]
    id_user = get_jwt_identity()
    if company and address and city and zip and country:
        #buscar si existe 
        sql = f"SELECT * FROM mn_users_billing_data where id_user =  '{id_user}'  "
        getBilling = getDataOne(sql)
        if getBilling:
            #existe por lo tanto actualizo
            sql = f"""
            update mn_users_billing_data set companyName = '{company}', address = '{address}'
            , city = '{city}', zip = '{zip}', country = '{country}'  where   id_user = '{id_user}' """
            updateIpUser = updateData(sql)
            response = {
            'status': 1,
            }
        else:
            sql = f"""
            INSERT INTO mn_users_billing_data ( companyName, address, city, zip, country, id_user) VALUES ( '{company}',
            '{address}', '{city}', '{zip}', '{country}', '{id_user}' ) 
            """
            id_billing = updateData(sql)
            response = {
            'status': 1,
            }
        return jsonify(response)
    else:
         abort(make_response(jsonify(message="data user incorrect"), 401))



@app.route('/api/update_plan_user', methods=['POST'])
@jwt_required()
def update_plan_user():
    body = request.get_json()
    session_id = body["session_id"]
    id_user = get_jwt_identity()
    if session_id:
        #buscar si existe 
        sql = f"SELECT * FROM mn_payment_intent_stripe where id_user =  '{id_user}' and id_sesion = '{session_id}' and pagado = 1  "
        print(sql)
        getPagado = getDataOne(sql)
        if getPagado:
            #ya esta pago envio la notificacion
            response = {
            'status': 1,
            }
            return jsonify(response)
        else:
         abort(make_response(jsonify(message="payment intent not paid"), 401))
    else:
         abort(make_response(jsonify(message="data user incorrect"), 401))



@app.route('/api/get_user_billing_data', methods=["GET"])
@jwt_required()
def get_user_billing_data():
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_users_billing_data where id_user = '{id_user}'  "
    getBilling = getDataOne(sql)

    sql = f"SELECT * FROM mn_subscription_users where id_user = '{id_user}' order by id desc  "
    getSuscription = getDataOne(sql)
    if getSuscription:
        activePlan = getSuscription[5]
        renewalPlan = str(getSuscription[4])
    else:
        activePlan = ""
        renewalPlan = ""


    sql = f"SELECT * FROM mn_billing_payment_users where id_user = '{id_user}'  "
    getPayments = getData(sql)
    payments = []
    if getPayments:
        for row in getPayments:
            amount = f"  {row[1]} $" 
            if row[2] == 0:
                plan = 'Limitado'
            if row[2] == 2:
                plan = 'Pro'
            
            payments.append({
                "amount": amount,
                "description": f"Plan {plan}",
                "payment_date": str(row[6]),
                "status":  ' <i class="fa fa-check" style="    color: rgb(61, 179, 158);" aria-hidden="true"></i>',
            })
    


   
    response = {
            "status": 1,
            "dataBilling": getBilling, 
            "renewalPlan": renewalPlan,
            "payments": payments, 
            "activePlan": activePlan
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
    ipUser = body["ipUser"]
    paisUser = body["paisUser"]

    if firstName and lastName and email and userName and passW:
        # todos estos campos estan llenos
        sql = f"""
                INSERT INTO mn_users ( firstName, lastName, email, userName, pass, cookieUser, ip, pais, date) 
                VALUES 
                ( '{firstName}', '{lastName}', '{email}', '{userName}', '{passW}', '{userCookie}',  '{ipUser}',  '{paisUser}', '{datetime.now()}'  ) 
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


# update cookie user invitado
@app.route('/api/update_user_invitado', methods=["POST"])
def update_user_invitado():
    body = request.get_json()
    print(body)
    cookieUserFrom = body["cookieUser"]
    pais = body["pais"]
    ipUser = body["ipUser"]

    sql = f"SELECT * FROM mn_users_cookie where cookie = '{cookieUserFrom}'  "
    # buscar por uid las encuestas q tenga en la db
    cookieUser = getDataOne(sql)
    if cookieUser:
        response = {
            "status": 1
        }
        print("user ya existe ")
    else:
        sql = f"""
        INSERT INTO mn_users_cookie ( name, ip, pais, cookie, fecha) 
        VALUES 
        ( 'guest', '{ipUser}', '{pais}', '{cookieUserFrom}', '{datetime.now()}'  ) 
        """
        id_user = updateData(sql)
        print("user registrado ")

        response = {
            "status": 1
        }
    return jsonify(response)




# update cookie user invitado
@app.route('/api/cancel_user_suscription', methods=["POST"])
@jwt_required()
def cancel_user_suscription():
    body = request.get_json()
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_subscription_users where id_user = '{id_user}'  "
    getUserSub = getDataOne(sql)
    if getUserSub:
        active = getUserSub[5]
        if active == 1:
            active = 0
        else:
            active = 1
        sql = f"""
        update  mn_subscription_users set active = '{active}' where id_user = '{id_user}'
        """
        updateS = updateData(sql)
        response = {
            "active": active
        }
        return jsonify(response)
    else:
        abort(make_response(jsonify(message="data user incorrect"), 401))




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

            # select cant de votos por tipo encuesta

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



# user not registered
@app.route('/api/cron_cancel_suscription_users_by_cancel_method', methods=['GET'])
def cron_cancel_suscription_users_by_cancel_method():
    #buscar los usuarios q tengan la fecha de renovacion de hoy
        
    sql = f"SELECT * FROM mn_subscription_users where renewalDate =  '{date.today()}' and active = 0 and finalizado = 0"
    getUsers = getData(sql)
    if getUsers:
        for user in getUsers:
            #hay usuarios q se le acabo el plan q cancelaron la renovacion asi q los bajo de plan 
            sql = f"""
            update  mn_users set premium = 0 where id = '{user[7]}'  
            """
            updateUser = updateData(sql)

            sql = f"""
            update  mn_subscription_users set finalizado = 1, active = 0 where id = '{user[0]}'  
            """
            updateUser = updateData(sql)
        response = {
        "status": 1, 
        "users": getUsers
        }
    else:
        response = {
        "status": 0 
        }
    
    return jsonify(response)



@app.route('/api/email_de_prueba', methods=['GET'])
def email_de_prueba():
    emailTo = request.args.get('to', '')

    email_content = """
    <p style="text-align: justify;"><img src="https://result.app/img/Logoresult.jpg" alt="" width="300" height="100" /></p>
    <p style="text-align: justify;">Dear Hector Acosta (Nananona C.A.),</p>
    <p style="text-align: justify;">This is a notice that an invoice has been generated on 24th Jul 2021.</p>
    <p style="text-align: justify;">Your payment method is: Credit Card</p>
    <p style="text-align: justify;">Amount Due: $6.95 USD
    Due Date: 3rd Aug 2021</p>
    <p style="text-align: justify;"><strong>Invoice Items</strong></p>
    ---------------------------------------
    <p style="text-align: justify;">Plan Pro</p>
    ---------------------------------------
    <p style="text-align: justify;">Regards,</p>
    Result.app


    """

    msg = email.message.Message()
    msg['Subject'] = 'Customer Invoice'


    msg['From'] = "Result.app <emailresultapp@gmail.com>"
    msg['To'] = emailTo
    password = "199021utf8"
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(email_content)

    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()

    # Login Credentials for sending the mail
    s.login('emailresultapp@gmail.com', password)

    s.sendmail(msg['From'], [msg['To']], msg.as_string())

    response = {
        "status": 0 
        }
    
    return jsonify(response)

#enviar email recordatorio vencimiento
def email_recordatorio_vencimiento(usernames, amount, renewalDate, plan, tipo, id_user, emailTo):
    email_content = f"""
    <p style="text-align: justify;"><img src="https://result.app/img/Logoresult.jpg" alt="" width="300" height="85" /></p>
    <p style="text-align: justify;">Dear {usernames} ,</p>
    <p style="text-align: justify;">This is a notice that an invoice has been generated on {date.today()}.</p>
    <p style="text-align: justify;">Amount Due: {amount} USD </p>
    <p style="text-align: justify;">Due Date: {renewalDate}</p>
    <p style="text-align: justify;"><strong>Invoice Items</strong></p>
    ---------------------------------------
    <p style="text-align: justify;">Plan {plan}</p>
    ---------------------------------------
    <p style="text-align: justify;">Regards,</p>
    Result.app

    """
    sql = f"""
    INSERT INTO mn_notificaciones_user ( mensaje, tipo, id_user, leida, enviada, date, datetime) VALUES ( '{email_content}',
    '{tipo}', '{id_user}', 0, 1, '{date.today()}', '{datetime.now()}' ) 
    """
    id_dia = updateData(sql)
    if id_dia:
        msg = email.message.Message()
        msg['Subject'] = 'Customer Invoice'


        msg['From'] = "Result.app <emailresultapp@gmail.com>"
        msg['To'] = emailTo
        password = "199021utf8"
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(email_content)

        s = smtplib.SMTP('smtp.gmail.com: 587')
        s.starttls()

        # Login Credentials for sending the mail
        s.login('emailresultapp@gmail.com', password)

        s.sendmail(msg['From'], [msg['To']], msg.as_string())


#enviar email recordatorio vencimiento
def email_desactivar_plan_vencimiento(usernames, amount, renewalDate, plan, tipo, id_user, emailTo):
    email_content = f"""
    <p style="text-align: justify;"><img src="https://result.app/img/Logoresult.jpg" alt="" width="300" height="85" /></p>
    <p style="text-align: justify;">Dear {usernames} ,</p>
    <p style="text-align: justify;">This is a notice that an invoice has been generated on {date.today()}.</p>
    <p style="text-align: justify;">your current plan has been deactivated, because the corresponding payment has not been made after 3 days of surrender.</p>
    <p style="text-align: justify;">Amount Due: {amount} USD </p>
    <p style="text-align: justify;">Due Date: {renewalDate}</p>
    <p style="text-align: justify;"><strong>Invoice Items</strong></p>
    ---------------------------------------
    <p style="text-align: justify;">Plan {plan}</p>
    ---------------------------------------
    <p style="text-align: justify;">Regards,</p>
    Result.app

    """
    sql = f"""
    INSERT INTO mn_notificaciones_user ( mensaje, tipo, id_user, leida, enviada, date, datetime) VALUES ( '{email_content}',
    '{tipo}', '{id_user}', 0, 1, '{date.today()}', '{datetime.now()}' ) 
    """
    id_dia = updateData(sql)
    if id_dia:
        msg = email.message.Message()
        msg['Subject'] = 'Customer Invoice'


        msg['From'] = "Result.app <emailresultapp@gmail.com>"
        msg['To'] = emailTo
        password = "199021utf8"
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(email_content)

        s = smtplib.SMTP('smtp.gmail.com: 587')
        s.starttls()

        # Login Credentials for sending the mail
        s.login('emailresultapp@gmail.com', password)

        s.sendmail(msg['From'], [msg['To']], msg.as_string())


# user not registered
@app.route('/api/cron_suscription_users_by_vencimiento', methods=['GET'])
def cron_suscription_users_by_vencimiento():
    #buscar los usuarios q tengan la fecha de renovacion de hoy
        
    sql = f""" 
    SELECT * FROM mn_subscription_users where renewalDate <=  '{date.today()}' 
    and active = 1 and finalizado = 0
    """
    print(sql)
    getUsers = getData(sql)
    if getUsers:
        #necesito los nombres del usuario 
        

        for user in getUsers:
            id_user = user[7]
            sql = f""" 
            SELECT * FROM mn_users where id = '{id_user}' 
            """
            dataUser = getDataOne(sql)
            print(dataUser)
            nombres = F"{dataUser[1]} {dataUser[2]}"
            dateVencida =  datetime.strptime(str(user[4]), '%Y-%m-%d').date()        #Ahora vamos a definir el día de hoy, la fecha actual.
            today = date.today()
            #Posterior a ello realizamos una resta entre estas fechas y lo convertimos a días.
            remaining_days = (today - dateVencida).days

            if remaining_days >=1: 
                if remaining_days == 4:
                    sql = f"""
                    update  mn_users set premium = 0 where id = '{user[7]}'  
                    """
                    updateUser = updateData(sql)

                    sql = f"""
                    update  mn_subscription_users set finalizado = 1, active = 0 where id = '{user[0]}'  
                    """
                    updateUser = updateData(sql)
                    email_desactivar_plan_vencimiento(nombres, 11, dateVencida, "Pro", 0, id_user, dataUser[3])
                    status = "Valio verga perdio su plan"
                else:
                    print("enviar mensaje por email y guardar notificacion")
                    sql = f""" 
                    SELECT * FROM mn_notificaciones_user where tipo = 0 and id_user = '{id_user}' and date =  '{date.today()}'   """
                    print("notificaciones user", sql)
                    getInvoiceHoy = getData(sql)
                    if getInvoiceHoy:
                        status = "Ya se le envio el recordatorio"
                    else: 
                        status = "no se le ha enviado nada entonces enviar la noti y el email"
                        email_recordatorio_vencimiento(nombres, 11, dateVencida, "Pro", 0, id_user, dataUser[3])
            #Finalmente mandamos a imprimir los días restantes
            print(f"tiene {remaining_days} días de vencido")
            response = {
            "status": status, 
            "vencida": f"tiene {remaining_days} días de vencido"
            }
    else:
        response = {
        "status": "y yo q se"
        }
    
    return jsonify(response)


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
                'disabled': row[9],
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


@app.route('/api/events_users_not_registered', methods=['GET'])
def events_users_not_registered():
    id_user = request.args.get('p', '')

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




@app.route('/api/cambiar_nombre_evento_by_cod', methods=['GET'])
@jwt_required()
def cambiar_nombre_evento_by_cod():
    id_user = get_jwt_identity()
    codigo = request.args.get('cod', '')
    nombre = request.args.get('nombre', '')
    sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' and codigo = '{codigo}'  "
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        sql = f"""
        update mn_eventos set titulo = '{nombre}' where 
        id = '{id_evento}' 
        """
        id_tipo = updateData(sql)
        response = {
            "status": 1
        }
        return jsonify(response)
    else:
        abort(make_response(jsonify(message="data user incorrect"), 401))

@app.route('/api/cambiar_fecha_evento_by_cod', methods=['GET'])
@jwt_required()
def cambiar_fecha_evento_by_cod():
    id_user = get_jwt_identity()
    codigo = request.args.get('cod', '')
    fecha = request.args.get('fecha', '')
    zonaHoraria = request.args.get('zonaHoraria', '')
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(zonaHoraria)
    print("llego la fecha", fecha)
    sql = f"SELECT * FROM mn_eventos where id_user = '{id_user}' and codigo = '{codigo}'  "
    # buscar por uid las encuestas q tenga en la db
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
        #utc = datetime.strptime(str(horaini), '%Y-%m-%d %H:%M:%S')
       # utc = fecha.replace(tzinfo=from_zone)
      #  central = utc.astimezone(to_zone)
      #  print(central)
      #  fecha = str(central)
        #guardo la fehca nuea
        sql = f"""
        update mn_eventos set fecha = '{fecha}' where 
        id = '{id_evento}' 
        """
        id_tipo = updateData(sql)
        response = {
            "status": 1
        }
        return jsonify(response)
    else:
        abort(make_response(jsonify(message="data user incorrect"), 401))








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
            "fecha": str(fecha)
        }

        return jsonify(response)

    else:
        print("no tiene")
        response = {
            "status": 0,
            "eventName": nameEvent,
            "eventStatus": eventStatus,
            "eventModo": eventModo,
            "fecha": str(fecha)
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
        if evento[9] == 1:
            response = {
            "status": 0,
            }
            return jsonify(response)

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
        update mn_eventos set status = '{status}', modo = 0 where 
        codigo = '{codigo}' and id_user = '{id_user}'
        """
    evento = updateData(sql)
    socketio.emit('cambiarStatusEvent', {
                  "codigo": codigo, "status": status}, to=codigo)
    socketio.emit('cambiarStatusEvent', {
                  "codigo": codigo, "status": status}, to=codigo+"_admin")
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
                  "codigo": codigo, "modo": modoLive}, to=codigo)
    socketio.emit('activarModoPresentacion', {
                  "codigo": codigo, "modo": modoLive}, to=codigo+"_admin")
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
    socketio.emit('cambiarEncuestaActiva', {
        "msj": "cambiando de encuesta activa", "codigo": codigo, "id_encuesta": idEncuesta}, to=codigo)
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

        if en[1] == 5:
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


# get encuestas by id user not registered dashboard

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
        if evento[9] == 1:
            response = {
            "status": 0,
            }
            return jsonify(response)

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
                "fecha": str(evento[8]),
                "statusEvent": evento[7],
                "modo": evento[5],
                "tipoEncuesta": encuestaTipo,
                "encuestaActiva": play
            }
        else:
            # pasar el evento a stop
            """
            sql = f"""
            # update mn_eventos set modo = 0 where id = '{id_evento}'
            """
            updateEvento = updateData(sql)
            """
            response = {
                "id":  evento[0],
                "status": 2,
                "statusEvent": evento[7],
                "modo": evento[5],
                "titulo": evento[1],
                "fecha": str(evento[8]),
            }
    else:
        response = {
            "status": 0
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
    encuestaActiva = 0
    tipo = 0
    if buscarTipo:

        tipo = buscarTipo[1]
        encuestaActiva = buscarTipo[6]
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

        if encuestaActiva == 1:
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
                    socketio.emit('EliminarEncuestaActiva', {
                        "tipo": 3, "msj": "elimine una encuesta", "codigo": codigo, "id_encuesta": id_encuesta_primera}, to=codigo)
                else:
                    socketio.emit('sinEncuestasAlEliminar', {
                                  "msj": "sin encuestas", "codigo": codigo}, to=codigo)

        response = {
            'status': actualizar,
        }
    else:
        response = {
            'status': 'error',
        }

    return jsonify(response)


# delete event by id by user not registered

@app.route('/api/delete_poll_by_id_not_registered', methods=["POST"])
def delete_poll_by_id_not_registered():
    body = request.get_json()
    id_event = body["id_event"]
    id_encuesta = body["id_encuesta"]
    id_user = body["p"]
    # buscar si el evento existe

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


@app.route('/api/borrar_evento_by_admin', methods=['POST'])
@jwt_required()
def borrar_evento_by_admin():
    body = request.get_json()
    codigo = body["codigo"]
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  "
    print(sql)
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        sql = f"""
        delete from mn_eventos where ID = '{id_evento}'
        """
        borrar = updateData(sql)
        response = {
            "status": 1
        }
        return jsonify(response)
    else:
        abort(make_response(jsonify(message="data user incorrect"), 401))


@app.route('/api/duplicar_evento_by_admin', methods=['POST'])
@jwt_required()
def duplicar_evento_by_admin():
    body = request.get_json()
    codigo = body["codigo"]
    id_user = get_jwt_identity()
    titulo =  body["titulo"]
    codigoNew = codigoAleatorio(5)
    sql = f"SELECT * FROM mn_eventos where codigo = '{codigo}' and id_user = '{id_user}'  "
    print(sql)
    evento = getDataOne(sql)
    if evento:
        id_evento = evento[0]
        titulo = str(evento[1])+"_duplicate"
        #ahora crear un evento con las mismas caracteristicas 
        sql = f"""
        INSERT INTO mn_eventos ( titulo, descripcion, codigo, id_user, modo, tipoUser,  status, fecha) 
        VALUES 
        ( '{titulo}', '', '{codigoNew}', '{id_user}', 0, 1, 1, '{datetime.now()}'  ) 
        """
        id_eventoNew = updateData(sql)
        # ahora buscar las encuestas del evento y recorrerlar para irlas creando una por una 
        sql = f"SELECT * FROM mn_tipo_encuesta where id_evento = '{id_evento}' and id_user = '{id_user}'  "
        print(sql)
        encuestasViejas = getData(sql)
        for row in encuestasViejas:
            tipoVieja = row[1]
            tituloVieja = row[2]
            idEncuestaVieja = row[0]
            sql = f"SELECT * FROM mn_tipo_encuesta where id_user = '{id_user}' and id_evento = '{id_evento}' order by posicion desc "
            # buscar por uid las encuestas q tenga en la db
            enPosicion = getDataOne(sql)
            if enPosicion:
                posicion = enPosicion[3]+1
            else:
                posicion = 0+1
            sql = f"""
            INSERT INTO mn_tipo_encuesta ( tipo, titulo, posicion,  id_user, id_evento,  fecha) VALUES ( '{tipoVieja}',
            '{tituloVieja}', '{posicion}', '{id_user}', '{id_eventoNew}',  '{datetime.now()}'  ) 
            """
            id_tipo_encuesta = updateData(sql)
            if tipoVieja == 1: 
                #encuesta siomple debo crear las opciones q tiene 
                #para crerarlas primero debo buscarlas 
                sql = f"SELECT * FROM mn_tipo_encuesta_choice where id_tipo_encuesta = '{idEncuestaVieja}'  "
                # buscar por uid las encuestas q tenga en la db
                esOpciones = getData(sql)
                for op in esOpciones: 
                    sql = f"""
                    INSERT INTO mn_tipo_encuesta_choice ( opcion, id_tipo_encuesta) VALUES ( '{op[1]}',
                    '{id_tipo_encuesta}' ) 
                    """
                    actualizar = updateData(sql)
            if tipoVieja == 3:
                #sorteo 
                sql = f"SELECT * FROM mn_sorteos_participantes where id_encuesta = '{idEncuestaVieja}'  "
                # buscar por uid las encuestas q tenga en la db
                esParticipantes = getData(sql)
                for pa in esParticipantes:
                    sql = f"""
                    INSERT INTO mn_sorteos_participantes ( value, id_encuesta) VALUES ( '{pa[1]}',
                    '{id_tipo_encuesta}' ) 
                    """
                    actualizar = updateData(sql)
            if tipoVieja == 4:
                #diayhora
                sql = f"SELECT * FROM mn_date_day where id_encuesta = '{idEncuestaVieja}'  "
                # buscar por uid las encuestas q tenga en la db
                esDia = getData(sql)
                for di in esDia:
                    sql = f"""
                    INSERT INTO mn_date_day ( fecha, id_encuesta) VALUES ( '{di[1]}',
                    '{id_tipo_encuesta}' ) 
                    """
                    id_dia_nuevo = updateData(sql)
                    #ahora buscar las horas de este dia 
                    sql = f"SELECT * FROM mn_date_horas where id_date_day = '{di[0]}'  "
                    # buscar por uid las encuestas q tenga en la db
                    esHora = getData(sql)
                    for ho in esHora:
                        sql = f"""
                        INSERT INTO mn_date_horas ( hora, id_date_day, id_encuesta) VALUES ( '{ho[1]}',
                        '{id_dia_nuevo}', '{id_tipo_encuesta}' ) 
                        """
                        actualizar = updateData(sql)
        response = {
            "status": 1,
            "codigo": codigoNew
        }
        return jsonify(response)
    else:
        abort(make_response(jsonify(message="data user incorrect"), 401))


#stripe
@app.route('/api/get_data_by_stripe', methods=['POST'])
@jwt_required()
def get_data_by_stripe():
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_users where id = '{id_user}'  "
    userData = getDataOne(sql)
    email = userData[3]
    customer = userData[12]
    if customer == '0':
        session = stripe.checkout.Session.create(
        success_url=url_site_front+'upgrade/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_site_front+'upgrade/error',
        customer_email=email,
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
        'price': price_id,
        # For metered billing, do not pass quantity
        'quantity': 1
        }],
        )
    else:
        print("customer = ", customer)
        session = stripe.checkout.Session.create(
        success_url=url_site_front+'upgrade/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_site_front+'upgrade/error',
        customer=customer,
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
        'price': price_id,
        # For metered billing, do not pass quantity
        'quantity': 1
        }],
        )
        
        
        
    #guardar en la db le sesion generada al usuario para luego de pagado poder verificar si pago o no y aprobarle su suscripcion
    sql = f"""
    INSERT INTO mn_payment_intent_stripe ( id_sesion, id_user, amount, descripcion, date, id_plan) VALUES ( '{session.id}',
    '{id_user}', 11, 'Pago del plan Pro', '{datetime.now()}', 2 ) 
    """
    actualizar = updateData(sql)
    response = {
        "status": 1, 
        "redirect": session.url, 
    }

    return jsonify(response)

@app.route('/api/get_portal_customer_by_user_id', methods=['GET'])
@jwt_required()
def get_portal_customer_by_user_id():
    id_user = get_jwt_identity()
    sql = f"SELECT * FROM mn_users_billing_data where id_user = '{id_user}'  "
    userData = getDataOne(sql)
    customer_id = userData[7]
    return_url = url_site_front+'dashboard'
    print("customer id", customer_id)

    session = stripe.billing_portal.Session.create(
    customer=customer_id,
    return_url=return_url,
    )

    # redirect to the URL for the session
    #   return redirect(session.url, code=303)
    response = {
        "status": 1, 
        "redirect": session.url, 
    }

    return jsonify(response)



@app.route('/webhook_stripe', methods=['POST'])
def webhook_received():
    webhook_secret = ''
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']

    if event_type == 'checkout.session.completed':
    # Payment is successful and the subscription is created.
    # You should provision the subscription and save the customer ID to your database.
        sesionId = data_object["id"]
        customerId = data_object["customer"]
        print("customer id = ", customerId)
        #buscar por al sesion id el intent registrado en la db y verificar q existe y de ahi necesito el id_user
        sql2 = f"SELECT * FROM mn_payment_intent_stripe where id_sesion = '{sesionId}'  "
        getSesionDb = getDataOne(sql2)
        if getSesionDb:
            id_plan = getSesionDb[7]
            #coincide por lo tanto se realizo el pago correctamente 
            id_user = getSesionDb[2]
            sql2 = f"SELECT * FROM mn_users_billing_data where id_user = '{id_user}' and customer_id = '{customerId}' "
            getCustomer = getDataOne(sql2)
            if getCustomer:
                print("ya existe el customer seguramente esta metiendole mas plata al plan o otra cosa")
            else:
                #crear customer billing
                sql = f"""
                INSERT INTO mn_users_billing_data ( companyName, address, city, zip, country, id_user, customer_id ) 
                VALUES
                 ( '', '', '', '', '', '{id_user}', '{customerId}'  ) 
                """
                idUserBilling = updateData(sql)
            #ahora actualizamos el plan del usuario 
            sql = f"""
            update mn_users set premium =  '{id_plan}', customer_id = '{customerId}' where id = '{id_user}'
            """
            updateUserPlan = updateData(sql)
            #ahora pasamos el payment intent a pagado 
            sql = f"""
            update mn_payment_intent_stripe set pagado = 1 where id_sesion = '{sesionId}'
            """
            updateSesionPayment = updateData(sql)
        print(data)
    elif event_type == 'invoice.paid':
    # Continue to provision the subscription as payments continue to be made.
    # Store the status in your database and check when a user accesses your service.
    # This approach helps you avoid hitting rate limits.
      print(data)
    elif event_type == 'invoice.payment_failed':
    # The payment failed or the customer does not have a valid payment method.
    # The subscription becomes past_due. Notify your customer and send them to the
    # customer portal to update their payment information.
      print(data)
    elif event_type == 'customer.subscription.deleted':
        #se cancelo la suscripcion actualizar la base de datos :D 
        customerId = data_object["customer"]
        sql2 = f"SELECT * FROM mn_users_billing_data where  customer_id = '{customerId}' "
        getCustomer = getDataOne(sql2)
        id_user = getCustomer[6]
        sql = f"""
        update mn_users set premium =  0 where id = '{id_user}'
        """
        updateUserPlan = updateData(sql)
        #deshablitar los eventos q tenga mayor a 5 
        sql2 = f"SELECT * FROM mn_eventos where  id_user = '{id_user}' order by id asc "
        getEventos = getData(sql2)
        i = 0
        for row in getEventos:
            if i >= 5:
                sql = f"""
                update mn_eventos set disabled =  1 where id = '{row[0]}'
                """
                disableEvento = updateData(sql)
            i = i + 1
        print(data)
    else:
      print('Unhandled event type {}'.format(event_type))

    return jsonify({'status': 'success'})