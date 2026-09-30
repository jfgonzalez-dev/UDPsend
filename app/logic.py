import socket
from datetime import datetime

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
"""The UDP socket instance used for transmitting packets."""

UDP_IP = '192.168.4.1'
"""IP address it will send the UDP packet to."""
UDP_PORT = 12345
"""Port it will send the UDP packet to."""


def main():
    """
    Main function.
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
    Sends the UDP packet.

    Args:
        msg (str): The message to be sent.

    Returns:
        None
    """
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))


def gen_cal(st_year, st_month, fest):
    """
    Generates a 12 months list using the correct format, starting from a specific month and year.

    Args:
        st_year (int): Starting year.
        st_month (int): Starting month (1-12).
        fest (list of dict): Not lective days.

    Returns:
        list of str: List of 12 strings, each representing a month.
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
    Sort timetable using 'time' as key in ascendent order.

    Args:
        timetable (list of dict): Holds timetable data.

    Returns:
        list of dict: Sorted using 'time' as key.
    """
    return sorted(timetable, key=lambda x: x['time'])


def gen_time(timetable):
    """
    Generates a tuple containing the formatted timetable and the number of time slots.

    Args:
        timetable (list of dict): List of dictionaries holding all timetable data.

    Returns:
        tuple[str, str]: The formatted timetable [0] and the number of slots [1].
    """
    _time = [i['time'].replace(':', '').zfill(2) for i in sort_time(timetable)]
    _udp_time = 'H' + '-'.join(_time).ljust(104, '-')
    return _udp_time, f'N{str(len(_time)).zfill(2)}'


def gen_rep(timetable):
    """
    Generates a formatted string representing the playback duration for each time slot.

    Args:
        timetable (list of dict): List of dictionaries holding all timetable data.

    Returns:
        str: The playback duration for each time slot, padded and joined.
    """
    _rep = [i['rep'].zfill(3) for i in sort_time(timetable)]
    return 'T' + '-'.join(_rep).ljust(83, "-")


def gen_vol(timetable):
    """
    Generates a formatted string representing the volume level for each time slot.

    Args:
        timetable (list of dict): List of dictionaries holding all timetable data.

    Returns:
        str: Formatted string with the volume level for each time slot.
    """
    _vol = [i['vol'].zfill(2) for i in sort_time(timetable)]
    return 'V' + '-'.join(_vol).ljust(62, '-')


def gen_fol(folder):
    """
    Generates a formatted string for the playback folder.

    Args:
        folder (int): Folder number.

    Returns:
        str: The playback folder identifier (e.g., 'F01' to 'F99').
    """
    if 0 < int(folder) < 100:
        return f'F{str(folder).zfill(2)}'
    elif folder < 0:
        return 'F01'
    elif folder > 100:
        return 'F99'


def gen_now():
    """
    Generates a formatted string with the current date and time.

    Returns:
        str: The current date and time formatted as 'D-YYYY/MM/DD/HH/MM/SS'.
    """
    return f"D-{datetime.now().strftime('%Y/%m/%d/%H/%M/%S')}"


if __name__ == '__main__':
    main()
    