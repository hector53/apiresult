from datetime import datetime
import time
import math
def time_passed(fecha):
    timestamp = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
    timestamp = datetime.timestamp(timestamp)
    print("timestamp", timestamp)
    print("fecha normal", datetime.fromtimestamp(timestamp))
    fechaNormal = datetime.fromtimestamp(timestamp)
    year = fechaNormal.strftime("%Y")
    print("año ", year)
    print(int(time.time()))
    diff = int(time.time()) - int(timestamp)
    print(diff)
    if diff == 0:
        return 'justo ahora'

    if diff > 604800:
        dia = fechaNormal.strftime("%d")
        mes = fechaNormal.strftime("%b")
        #mes = mes[1:2]
        return f"{dia} {mes}"

    if diff < 604800:
        intervals = ['days', 86400]
    if diff < 86400:
        intervals = ['h', 3600]
    if diff < 3600:
        intervals = ['min', 60]
    if diff < 60:
        intervals = ['seg', 1]

    value = math.floor(diff/intervals[1])
    return f"{value} {intervals[0]}"