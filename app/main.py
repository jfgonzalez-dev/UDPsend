import os

import app.logic as logic
import json
import time
import shutil

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'PARALELEPIPEDO'
sendTime_delay = 0


class ActionEnum:
    RemoveFestivo = 0
    AddFestivo = 1
    RemoveHorario = 2
    AddHorario = 3
    Apply = 4
    Nothing = 5

DATA_FILE = 'data/data.json'
TEMPLATE_FILE = 'app/data.default.json'

# Test values, should be stored in a file with the appropriate retrieve method.
class FileSystem:
    def __init__(self):
        self.__dict__ = self.load_data()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            shutil.copy(TEMPLATE_FILE, DATA_FILE)

        with open(DATA_FILE, 'r') as file:
            return json.load(file)

    def save_data(self):
        with open(DATA_FILE, 'w') as file:
            json.dump(self.__dict__, file, indent=4)


File = FileSystem()


def GetData(mRequest):
    year = int(mRequest.form.get('year'))
    month = int(mRequest.form.get('month')) + 1
    folder = int(mRequest.form.get('folder'))

    festInis = mRequest.form.getlist('festIni')
    festFins = mRequest.form.getlist('festFin')
    festData = []
    for i in range(len(festInis)):
        festData.append({'st': festInis[i], 'ed': festFins[i]})

    times = mRequest.form.getlist('time')
    reps = mRequest.form.getlist('rep')
    vols = mRequest.form.getlist('vol')
    horariosData = []
    for i in range(len(times)):
        horariosData.append({'time': times[i], 'rep': reps[i], 'vol': vols[i]})

    if mRequest.form.get('AddFestivoRow') is not None:
        action = ActionEnum.AddFestivo
    elif mRequest.form.get('PopFestivoRow') is not None:
        action = ActionEnum.RemoveFestivo
    elif mRequest.form.get('AddHorarioRow') is not None:
        action = ActionEnum.AddHorario
    elif mRequest.form.get('PopHorarioRow') is not None:
        action = ActionEnum.RemoveHorario
    elif mRequest.form.get('Apply') is not None:
        action = ActionEnum.Apply
    else:
        action = ActionEnum.Nothing

    return action, horariosData, festData, year, month, folder


def ValidateData(horariosData, festData, year, month, folder, isSending):
    errorMessages = []
    warningMessages = []
    notificationMessages = []

    # Ensure valid folder
    if not 0 < folder < 100:
        warningMessages.append('La carpeta debe estar entre 1 y 99. Se ha asignado automáticamente el valor más alto.')
        folder = 99

    # Fix Horarios None fields
    for i in range(len(horariosData)):
        if horariosData[i]['time'] != '':
            horariosData[i]['rep'] = horariosData[i]['rep'] if horariosData[i]['rep'] is not None else ''
            horariosData[i]['vol'] = horariosData[i]['vol'] if horariosData[i]['vol'] is not None else '5'

    # Only execute this validation when we are about to send UDP
    if isSending:
        # Delete empty Horarios
        nHorRem = 0
        tmpHorariosData = []
        for i in range(len(horariosData)):
            if horariosData[i]['time'] != '':
                tmpHorariosData.append(
                    {'time': horariosData[i]['time'], 'rep': horariosData[i]['rep'], 'vol': horariosData[i]['vol']})
            else:
                nHorRem += 1
        horariosData = tmpHorariosData

        if nHorRem > 0:
            warningMessages.append(
                f'Se ha{"n" if nHorRem > 1 else ""} eliminado {nHorRem} {"filas" if nHorRem > 1 else "fila"} de tramos '
                f'horarios vacía{"s" if nHorRem > 1 else ""}.')

        # Delete empty Festivos
        nFestRem = 0
        tmpFestData = []
        for i in range(0, len(festData)):
            if festData[i]['st'] != '' or festData[i]['ed'] != '':
                tmpFestData.append({'st': festData[i]['st'], 'ed': festData[i]['ed']})
            else:
                nFestRem += 1
        festData = tmpFestData

        if nFestRem > 0:
            warningMessages.append(
                f'Se ha{"n" if nFestRem > 1 else ""} eliminado {nFestRem} {"filas" if nFestRem > 1 else "fila"} de '
                f'festivos vacía{"s" if nFestRem > 1 else ""}.')

        # Fix Festivos empty fields
        nFestPair = 0
        for festPair in festData:
            nFestPair += 1
            if festPair['st'] == '' and festPair['ed'] != '':
                festPair['st'] = festPair['ed']
                notificationMessages.append(
                    f'El campo de inicio de la fila {nFestPair} en la sección de festivos estaba '
                    f'vacío. Se le ha asignado el valor del campo de finalización.')
            elif festPair['ed'] == '' and festPair['st'] != '':
                festPair['ed'] = festPair['st']
                notificationMessages.append(
                    f'El campo de finalización de la fila {nFestPair} en la sección de festivos '
                    f'estaba vacío. Se le ha asignado el valor del campo de inicio.')

            if festPair['st'] > festPair['ed']:
                _tempSt, _tempEd = festPair['st'], festPair['ed']
                festPair['st'], festPair['ed'] = _tempEd, _tempSt
                notificationMessages.append(
                    f'La fecha introducida en el campo de inicio de la fila {nFestPair} en la sección de festivos era '
                    f'posterior a la fecha de finalización. Se han invertido los valores en estos campos.')

    return errorMessages, warningMessages, notificationMessages, horariosData, festData, year, month, folder


@app.route('/', methods=['GET', 'POST'])
def editData():
    print('EditData Route')

    if request.method == 'GET':
        print('GET METHOD CALLED!')
        # Grab file version
        horariosData = File.horariosDataFile
        festData = File.festDataFile
        year = File.yearFile
        month = File.monthFile - 1
        folder = File.folderFile
        return render_template('editData.html', festData=festData, nFestivosData=len(festData),
                               horariosData=horariosData, nHorariosData=len(horariosData), year=year,
                               month=month, folder=folder)
    elif request.method == 'POST':
        action, horariosData, festData, year, month, folder = GetData(request)

        isSendingUDP = action == ActionEnum.Apply
        errorMessages, warningMessages, notificationMessages, horariosData, festData, year, month, folder = ValidateData(
            horariosData,
            festData, year,
            month,
            folder,
            isSendingUDP)

        if action == ActionEnum.AddFestivo:
            festData.append({'st': '', 'ed': ''})
        elif action == ActionEnum.RemoveFestivo:
            if len(festData) < 1:
                warningMessages.append('La lista de festivos ya esta vacía')
            else:
                festData.pop()
        elif action == ActionEnum.AddHorario:
            if len(horariosData) < 20:
                horariosData.append({'time': '', 'rep': '', 'vol': '5'})
            else:
                warningMessages.append('Número de tramos horarios máximo alcanzado.')
        elif action == ActionEnum.RemoveHorario:
            if len(horariosData) < 1:
                warningMessages.append('La lista de tramos horarios ya esta vacía')
            else:
                horariosData.pop()
        elif action == ActionEnum.Apply:
            decoded_horariosData = []
            cont = 0
            for i in horariosData:
                cont += 1
                try:
                    if 'm' in str(i['rep']):
                        if float(i['rep'].replace('m', '')) * 60 > 999:
                            decoded_horariosData.append({'time': i['time'], 'rep': '999'})
                        else:
                            decoded_horariosData.append(
                                {'time': i['time'], 'rep': str(int(float(i['rep'].replace('m', '')) * 60))})
                    else:
                        decoded_horariosData.append(
                            {'time': i['time'], 'rep': str(int(i['rep'].replace('s', '')))})
                except ValueError:
                    errorMessages.append(
                        f'Error en el campo "Duración" de la fila {cont} en la sección horarios. "{i['rep']}" no es una '
                        'duración válida.')

            if len(errorMessages) == 0:
                # Send Commands
                logic.udp_send(logic.gen_now())
                print(f'UDP enviado: {logic.gen_now()}')
                time.sleep(sendTime_delay)

                logic.udp_send(logic.gen_fol(folder))
                print(f'UDP enviado: {logic.gen_fol(folder)}')
                time.sleep(sendTime_delay)

                for tim in logic.gen_time(horariosData):
                    logic.udp_send(tim)
                    print(f'UDP enviado: {tim}')
                    time.sleep(sendTime_delay)

                _gen_rep = logic.gen_rep(decoded_horariosData)
                logic.udp_send(_gen_rep)
                print(f'UDP enviado: {_gen_rep}')
                time.sleep(sendTime_delay)

                logic.udp_send(logic.gen_vol(horariosData))
                print(f'UDP enviado: {logic.gen_vol(horariosData)}')
                time.sleep(sendTime_delay)

                for cal in logic.gen_cal(year, month, festData):
                    logic.udp_send(cal)
                    print(f'UDP enviado: {cal}')
                    time.sleep(sendTime_delay)

        # Update data
        File.horariosDataFile = horariosData
        File.festDataFile = festData
        File.yearFile = year
        File.monthFile = month
        File.folderFile = folder

        # Save data to JSON (disk)
        File.save_data()

        # Flash messages
        for notificationMessage in notificationMessages:
            flash(notificationMessage, 'info')

        for warningMessage in warningMessages:
            flash(warningMessage, 'warning')

        if len(errorMessages) != 0:
            for errorMessage in errorMessages:
                flash(errorMessage, 'danger')
            flash('Mensajes UDP no enviados. Es necesario corregir los campos erróneos antes de enviar los '
                  'mensajes.', 'danger')
        elif request.form.get('Apply') is not None:
            flash('Mensajes UDP enviados.', 'success')

        return redirect(url_for('editData'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/apple-touch-icon.ico')
def apple_icon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'static'), 'apple-touch-icon.png')


@app.route('/icon')
def icon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'static'), 'favicon-32x32.png')


@app.route('/manifest')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static', 'static'), 'site.webmanifest')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
