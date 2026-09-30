import socket
from datetime import datetime

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = '192.168.4.1'
UDP_PORT = 12345


def main():
    """
    Función principal.
    """
    horarios_data_file = [
        {'time': '09:30', 'rep': '45s', 'vol': '5'},
        {'time': '10:30', 'rep': '45s', 'vol': '10'},
        {'time': '11:30', 'rep': '60s', 'vol': '5'}
    ]
    fest_data_file = [
        {'st': '2024-05-11', 'ed': '2024-05-13'},
        {'st': '2024-06-03', 'ed': '2024-06-18'},
        {'st': '2024-11-10', 'ed': '2024-11-10'}
    ]
    print(gen_time(horarios_data_file))
    year = int(input('Año: '))
    start_month = int(input('Mes: '))
    [print(cal) for cal in gen_cal(year, start_month, fest_data_file)]
    [udp_send(cal) for cal in gen_cal(year, start_month, fest_data_file)]


def udp_send(msg):
    """
    Manda mensaje UDP.

    Args:
        msg (str): The message to be sent.

    Returns:
        None
    """
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))


def gen_cal(st_year, st_month, fest):
    """
    Genera una lista de 12 meses en el formato adecuado, comenzando desde un mes y año específicos.

    Args:
        st_year (int): Año de inicio.
        st_month (int): Mes de inicio (1-12).
        fest (list of dict): Días festivos.

    Returns:
        List[str]: Lista de 12 cadenas de caracteres, cada una representando un mes.
    """
    month_list = 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'CA', 'CB', 'CC'
    day_list = 'L', 'M', 'X', 'J', 'V', 'S', 'D'
    _udp_cal_y = []
    for i in range(12):
        month_index = (st_month + i - 1) % 12
        cur_year = st_year + (st_month + i - 1) // 12
        _udp_cal_m = month_list[month_index]

        for day in range(1, 32):  # Days from 1 to 31
            try:
                _date = datetime(cur_year, month_index + 1, day)
                _day = day_list[_date.weekday()]
                _date_str = _date.strftime('%Y-%m-%d')

                for j in fest:
                    if j['st'] == '' and j['ed'] != '':
                        j['st'] = j['ed']
                    elif j['ed'] == '' and j['st'] != '':
                        j['ed'] = j['st']

                if any(datetime.strptime(j['st'], '%Y-%m-%d').date() <= _date.date() <= datetime.strptime(j['ed'], '%Y-%m-%d').date() for j in fest):
                    _udp_cal_m += 'F'
                else:
                    _udp_cal_m += _day
            except ValueError:
                pass  # Do nothing, since the day is invalid

        _udp_cal_y.append(_udp_cal_m.ljust(33, '-'))  # Ensure the string is exactly 33 characters long

    return _udp_cal_y


def sort_time(timetable):
    """
    Ordena el horario por la clave 'time' en orden ascendente.

    Args:
        timetable (list of dict): Lista de diccionarios con todos los datos del horario.

    Returns:
        list of dict: Lista de diccionarios ordenada por la clave 'time'.
    """
    return sorted(timetable, key=lambda x: x['time'])


def gen_time(timetable):
    """
    Genera una tupla que contiene el horario y el número de tramos horarios en el formato adecuado.

    Args:
        timetable (list of dict): Lista de diccionarios con todos los datos del horario.

    Returns:
        Tuple[str, str]: Tupla de 2 cadenas de caracteres: el horario[0] y el nº de tramos[1].
    """
    _time = [i['time'].replace(':', '').zfill(2) for i in sort_time(timetable)]
    _udp_time = 'H' + '-'.join(_time).ljust(104, '-')
    return _udp_time, f'N{str(len(_time)).zfill(2)}'


def gen_rep(timetable):
    """
    Genera una cadena con el tiempo de reproducción de cada tramo horario en el formato adecuado.

    Args:
        timetable (list of dict): Lista de diccionarios con todos los datos del horario.

    Returns:
        str: Cadena de caracteres con el tiempo de reproducción de cada tramo horario.
    """
    _rep = [i['rep'].zfill(3) for i in sort_time(timetable)]
    return 'T' + '-'.join(_rep).ljust(83, "-")


def gen_vol(timetable):
    """
    Genera una cadena con el tiempo de reproducción de cada tramo horario en el formato adecuado.

    Args:
        timetable (list of dict): Lista de diccionarios con todos los datos del horario.

    Returns:
        str: Cadenas de caracteres con el tiempo de reproducción de cada tramo horario.
    """
    _vol = [i['vol'].zfill(2) for i in sort_time(timetable)]
    return 'V' + '-'.join(_vol).ljust(62, '-')


def gen_fol(folder):
    """
    Genera una cadena con la carpeta de reproducción en el formato adecuado.

    Args:
        folder (int): Número de la carpeta como cadena.

    Returns:
        str: Nombre de la carpeta formateado con una "F" al inicio y con un cero a la izquierda si es necesario.
    """
    if 0 < int(folder) < 100:
        return f'F{str(folder).zfill(2)}'
    elif folder < 0:
        return 'F01'
    elif folder > 100:
        return 'F99'


def gen_now():
    """
    Genera una cadena con la fecha y hora actual en el formato adecuado.

    Returns:
        str: Cadena con el formato 'D-YYYY/MM/DD/HH/MM/SS' representando la fecha y hora actual.
    """
    return f'D-{datetime.now().strftime('%Y/%m/%d/%H/%M/%S')}'


if __name__ == '__main__':
    main()
    