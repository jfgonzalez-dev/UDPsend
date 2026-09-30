import os

import app.logic as logic
import json
import time
import shutil

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
"""The primary WSGI application instance for the Flask web interface."""
app.config['SECRET_KEY'] = 'PARALELEPIPEDO'

send_time_delay = 0
"""Delay in seconds between UDP packet transmissions."""


class ActionEnum:
    """Enumeration of possible user actions triggered from the web interface."""
    remove_festivo = 0
    add_festivo = 1
    remove_horario = 2
    add_horario = 3
    apply = 4
    nothing = 5

DATA_FILE = 'data/data.json'
"""Path to the active configuration file containing user data."""

TEMPLATE_FILE = 'app/data.default.json'
"""Path to the fallback template used when the active data file is missing."""

class FileSystem:
    """
    Handles loading and saving application data to a local JSON file.

    Automatically generates a new data file from a default template if the 
    target file does not exist upon initialization.
    """

    def __init__(self):
        self.__dict__ = self.load_data()

    def load_data(self):
        """
        Loads data from the JSON configuration file, creating it if necessary.

        Returns:
            dict: The application configuration data.
        """
        if not os.path.exists(DATA_FILE):
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            shutil.copy(TEMPLATE_FILE, DATA_FILE)

        with open(DATA_FILE, 'r') as file:
            return json.load(file)

    def save_data(self):
        """Saves the current instance dictionary state to the JSON configuration file."""
        with open(DATA_FILE, 'w') as file:
            json.dump(self.__dict__, file, indent=4)


File = FileSystem()
"""Global instance used to access and modify the local JSON configuration."""

def get_data(m_request):
    """
    Extracts and structures scheduling and holiday data from the Flask request form.

    Args:
        m_request (flask.Request): The HTTP request object containing the form data.

    Returns:
        tuple: A 6-element tuple containing the requested action (ActionEnum), 
        timetable data (list of dict), holiday data (list of dict), year (int), 
        month (int), and folder (int).
    """
    year = int(m_request.form.get('year'))
    month = int(m_request.form.get('month')) + 1
    folder = int(m_request.form.get('folder'))

    fest_inis = m_request.form.getlist('festIni')
    fest_fins = m_request.form.getlist('festFin')
    fest_data = []
    for i in range(len(fest_inis)):
        fest_data.append({'st': fest_inis[i], 'ed': fest_fins[i]})

    times = m_request.form.getlist('time')
    reps = m_request.form.getlist('rep')
    vols = m_request.form.getlist('vol')
    horarios_data = []
    for i in range(len(times)):
        horarios_data.append({'time': times[i], 'rep': reps[i], 'vol': vols[i]})

    if m_request.form.get('AddFestivoRow') is not None:
        action = ActionEnum.add_festivo
    elif m_request.form.get('PopFestivoRow') is not None:
        action = ActionEnum.remove_festivo
    elif m_request.form.get('AddHorarioRow') is not None:
        action = ActionEnum.add_horario
    elif m_request.form.get('PopHorarioRow') is not None:
        action = ActionEnum.remove_horario
    elif m_request.form.get('Apply') is not None:
        action = ActionEnum.apply
    else:
        action = ActionEnum.nothing

    return action, horarios_data, fest_data, year, month, folder


def validate_data(horarios_data, fest_data, year, month, folder, is_sending):
    """
    Validates and corrects timetable and holiday data before processing or transmission.

    Args:
        horarios_data (list of dict): The timetable data to validate.
        fest_data (list of dict): The holiday data to validate.
        year (int): The selected year.
        month (int): The selected month.
        folder (int): The target folder number.
        is_sending (bool): Indicates if the data is about to be sent via UDP, 
            triggering stricter filtering such as empty row deletion.

    Returns:
        tuple: An 8-element tuple containing error messages (list of str), 
        warning messages (list of str), notification messages (list of str), 
        and the cleaned timetable data, holiday data, year, month, and folder.
    """
    error_messages = []
    warning_messages = []
    notification_messages = []

    # Ensure valid folder
    if not 0 < folder < 100:
        warning_messages.append('La carpeta debe estar entre 1 y 99. Se ha asignado automáticamente el valor más alto.')
        folder = 99

    # Fix Horarios None fields
    for i in range(len(horarios_data)):
        if horarios_data[i]['time'] != '':
            horarios_data[i]['rep'] = horarios_data[i]['rep'] if horarios_data[i]['rep'] is not None else ''
            horarios_data[i]['vol'] = horarios_data[i]['vol'] if horarios_data[i]['vol'] is not None else '5'

    # Only execute this validation when we are about to send UDP
    if is_sending:
        # Delete empty Horarios
        n_hor_rem = 0
        tmp_horarios_data = []
        for i in range(len(horarios_data)):
            if horarios_data[i]['time'] != '':
                tmp_horarios_data.append(
                    {'time': horarios_data[i]['time'], 'rep': horarios_data[i]['rep'], 'vol': horarios_data[i]['vol']})
            else:
                n_hor_rem += 1
        horarios_data = tmp_horarios_data

        if n_hor_rem > 0:
            warning_messages.append(
                f'Se ha{"n" if n_hor_rem > 1 else ""} eliminado {n_hor_rem} {"filas" if n_hor_rem > 1 else "fila"} de tramos '
                f'horarios vacía{"s" if n_hor_rem > 1 else ""}.')

        # Delete empty Festivos
        n_fest_rem = 0
        tmp_fest_data = []
        for i in range(0, len(fest_data)):
            if fest_data[i]['st'] != '' or fest_data[i]['ed'] != '':
                tmp_fest_data.append({'st': fest_data[i]['st'], 'ed': fest_data[i]['ed']})
            else:
                n_fest_rem += 1
        fest_data = tmp_fest_data

        if n_fest_rem > 0:
            warning_messages.append(
                f'Se ha{"n" if n_fest_rem > 1 else ""} eliminado {n_fest_rem} {"filas" if n_fest_rem > 1 else "fila"} de '
                f'festivos vacía{"s" if n_fest_rem > 1 else ""}.')

        # Fix Festivos empty fields
        n_fest_pair = 0
        for fest_pair in fest_data:
            n_fest_pair += 1
            if fest_pair['st'] == '' and fest_pair['ed'] != '':
                fest_pair['st'] = fest_pair['ed']
                notification_messages.append(
                    f'El campo de inicio de la fila {n_fest_pair} en la sección de festivos estaba '
                    f'vacío. Se le ha asignado el valor del campo de finalización.')
            elif fest_pair['ed'] == '' and fest_pair['st'] != '':
                fest_pair['ed'] = fest_pair['st']
                notification_messages.append(
                    f'El campo de finalización de la fila {n_fest_pair} en la sección de festivos '
                    f'estaba vacío. Se le ha asignado el valor del campo de inicio.')

            if fest_pair['st'] > fest_pair['ed']:
                _temp_st, _temp_ed = fest_pair['st'], fest_pair['ed']
                fest_pair['st'], fest_pair['ed'] = _temp_ed, _temp_st
                notification_messages.append(
                    f'La fecha introducida en el campo de inicio de la fila {n_fest_pair} en la sección de festivos era '
                    f'posterior a la fecha de finalización. Se han invertido los valores en estos campos.')

    return error_messages, warning_messages, notification_messages, horarios_data, fest_data, year, month, folder


@app.route('/', methods=['GET', 'POST'])
def edit_data():
    """
    Handles the main web interface for viewing and editing UDP transmission data.

    GET requests render the current configuration loaded from local storage. 
    POST requests process form submissions, validate the data, update storage, 
    and optionally trigger UDP network transmissions if the apply action is invoked.

    Returns:
        werkzeug.wrappers.Response: The rendered HTML template or a redirect response.
    """
    print('EditData Route')

    if request.method == 'GET':
        print('GET METHOD CALLED!')
        # Grab file version
        horarios_data = File.horariosDataFile
        fest_data = File.festDataFile
        year = File.yearFile
        month = File.monthFile - 1
        folder = File.folderFile
        return render_template('editData.html', festData=fest_data, nFestivosData=len(fest_data),
                               horariosData=horarios_data, nHorariosData=len(horarios_data), year=year,
                               month=month, folder=folder)
    elif request.method == 'POST':
        action, horarios_data, fest_data, year, month, folder = get_data(request)

        is_sending_udp = action == ActionEnum.apply
        error_messages, warning_messages, notification_messages, horarios_data, fest_data, year, month, folder = validate_data(
            horarios_data,
            fest_data, year,
            month,
            folder,
            is_sending_udp)

        if action == ActionEnum.add_festivo:
            fest_data.append({'st': '', 'ed': ''})
        elif action == ActionEnum.remove_festivo:
            if len(fest_data) < 1:
                warning_messages.append('La lista de festivos ya esta vacía')
            else:
                fest_data.pop()
        elif action == ActionEnum.add_horario:
            if len(horarios_data) < 20:
                horarios_data.append({'time': '', 'rep': '', 'vol': '5'})
            else:
                warning_messages.append('Número de tramos horarios máximo alcanzado.')
        elif action == ActionEnum.remove_horario:
            if len(horarios_data) < 1:
                warning_messages.append('La lista de tramos horarios ya esta vacía')
            else:
                horarios_data.pop()
        elif action == ActionEnum.apply:
            decoded_horarios_data = []
            cont = 0
            for i in horarios_data:
                cont += 1
                try:
                    if 'm' in str(i['rep']):
                        if float(i['rep'].replace('m', '')) * 60 > 999:
                            decoded_horarios_data.append({'time': i['time'], 'rep': '999'})
                        else:
                            decoded_horarios_data.append(
                                {'time': i['time'], 'rep': str(int(float(i['rep'].replace('m', '')) * 60))})
                    else:
                        decoded_horarios_data.append(
                            {'time': i['time'], 'rep': str(int(i['rep'].replace('s', '')))})
                except ValueError:
                    error_messages.append(
                        f'Error en el campo "Duración" de la fila {cont} en la sección horarios. "{i['rep']}" no es una '
                        'duración válida.')

            if len(error_messages) == 0:
                # Send Commands
                logic.udp_send(logic.gen_now())
                print(f'UDP enviado: {logic.gen_now()}')
                time.sleep(send_time_delay)

                logic.udp_send(logic.gen_fol(folder))
                print(f'UDP enviado: {logic.gen_fol(folder)}')
                time.sleep(send_time_delay)

                for tim in logic.gen_time(horarios_data):
                    logic.udp_send(tim)
                    print(f'UDP enviado: {tim}')
                    time.sleep(send_time_delay)

                _gen_rep = logic.gen_rep(decoded_horarios_data)
                logic.udp_send(_gen_rep)
                print(f'UDP enviado: {_gen_rep}')
                time.sleep(send_time_delay)

                logic.udp_send(logic.gen_vol(horarios_data))
                print(f'UDP enviado: {logic.gen_vol(horarios_data)}')
                time.sleep(send_time_delay)

                for cal in logic.gen_cal(year, month, fest_data):
                    logic.udp_send(cal)
                    print(f'UDP enviado: {cal}')
                    time.sleep(send_time_delay)

        # Update data
        File.horariosDataFile = horarios_data
        File.festDataFile = fest_data
        File.yearFile = year
        File.monthFile = month
        File.folderFile = folder

        # Save data to JSON (disk)
        File.save_data()

        # Flash messages
        for notification_message in notification_messages:
            flash(notification_message, 'info')

        for warning_message in warning_messages:
            flash(warning_message, 'warning')

        if len(error_messages) != 0:
            for error_message in error_messages:
                flash(error_message, 'danger')
            flash('Mensajes UDP no enviados. Es necesario corregir los campos erróneos antes de enviar los '
                  'mensajes.', 'danger')
        elif request.form.get('Apply') is not None:
            flash('Mensajes UDP enviados.', 'success')

        return redirect(url_for('editData'))


@app.route('/favicon.ico')
def favicon():
    """Serves the primary favicon for the web interface."""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/apple-touch-icon.ico')
def apple_icon():
    """Serves the Apple touch icon for iOS bookmarks."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'static'), 'apple-touch-icon.png')


@app.route('/icon')
def icon():
    """Serves the standard 32x32 pixel application icon."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'static'), 'favicon-32x32.png')


@app.route('/manifest')
def manifest():
    """Serves the web application manifest for PWA installation."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'static'), 'site.webmanifest')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
