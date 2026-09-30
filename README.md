# UDPsend
Aplicación web que codifica y envía un paquete UDP para configurar el timbre escolar del IES Mar de Cádiz hasta el año 2024.

Los mensajes UDP enviados se mandan también por la terminal para poder comprobarlos. Los datos del programa se almacenan en "data/data.json" entre sesión y sesión.

"main.py" contiene la variable "send_time_delay". Esta variable determina el tiempo que espera el programa entre cada mensaje UDP enviado.

## Requisitos
- Flask - 3.1.3
- itsdangerous - 2.2.0
- Jinja2 - 3.1.6
- markdown2 - 2.5.5
- MarkupSafe - 3.0.3
- pdoc - 16.0.0
- Pygments - 2.21.0
- Werkzeug - 3.1.9

## Instalación
Aunque UDPsend se hizo pensando en ejecutarlo desde Windows 10, a continuación se indican los pasos para usarlo también en otras distribuciones.

### Scripts de instalación
Si es la primera vez que se usa el programa, se deberán ejecutar en este orden:
1. Install_Python.bat
2. Install_Flask.bat
3. UDPsend.bat

Esto instalará las dependencias necesarias antes de ejecutar el programa. En el resto de los casos, bastará con ejecutar directamente **"UDPsend.bat"**.

### requirements.txt
Alternativamente, se pueden instalar las dependencias de este programa usando el comando:
```
pip install -r requirements.txt
```

## Reglas de codificación 
Los mensajes UDP se condifican siguiendo el siguiente conjunto de reglas:

### Formato para enviar y grabar calendario en EEPROM
|  Código  |   Valor   |
|----------|-----------|
| `C1`     | Enero     |
| `C2`     | Febrero   |
| ...      | ...       |
| `CA`     | Octubre   |
| `CB`     | Noviembre |
| `CC`     | Diciembre |
| `L`      | Lunes     |
| `M`      | Martes    |
| `X`      | Miércoles |
| ...      | ...       |
| `D`      | Domingo   |
| `F`      | Festivo   |
| `-`      |           |

En caso de tener la cadena menos de 33 caracteres, se incluirán `-` al final hasta completar la cadena.

```
Meses 2021
C1FFFFFFFFSDLMXJVSDLMXJVSDLMXJVSD
C2LMXJVSDLMXJVSDLMXJVSDLMXJVSD---
C3FMXJVSDLMXJVSDLMXJVSDLMXJVSDFFF
C4FFSDLMXJVSDLMXJVSDLMXJVSDLMXJV-
C5SDFMXJVSDLMXJVSDLMXJVSDLMXJVSDL
C6MXJVSDLMXJVSDLMXJVSDLMXJVSDLMX-
C7JVSDLMXJVSDLMXJVSDLMXJVSDLMXJVS
C8DLMXJVSDLMXJVSDLMXJVSDLMXJVSDLM

Meses 2020
C9MXJVSDLMXJVSDLMXJVSDLMXJVSDLMX-
CAJVSDLMXJVSDFMXJVSDLMXJVSDLMXJVS
CBDFMXJVSDLMXJVSDLMXJVSDLMXJVSDL- 
CCMXJVSDFFXJVSDLMXJVSDLMXFFFFFFFF
```
*\*Hay que adaptar cada año*.

### Formato para enviar horario de cambio de clase (pos 399 en EEPROM)
```
H0830-0840-0850-0930-1030-1125-1205-1300-1400-1440-1450-1500-1545-1645-1745-1845-1900-2000-2100-2145-2200
```
*\*Aunque hay 21 tramos posibles, solo serán efectivos los primeros que coincidan con el número de tramos horarios habilitados.*

### Formato para enviar tiempo de reproducción de cada canción (pos 800 en EEPROM) 
Tiempo de Reproducción en segundos (060 ->  60 segundos,   120 ->  120 segundos)
```
T120-045-045-045-045-120-120-045-045-045-045-120-045-045-045-045-045-045-045-045-045
```
*\*Aunque hay 21 valores posibles, solo serán efectivos los primeros que coincidan con el número de tramos horarios habilitados.*

### Volumen  Tramos horarios  (pos 670 en EEPROM)
Valores entre 5 y 30.
```
V25-18-18-25-25-25-25-25-25-18-18-25-25-25-25-25-25-25-25-25-25
```
*\*Aunque hay 21 valores posibles, solo serán efectivos los primeros que coincidan con el número de tramos horarios habilitados.*

### Número de Tramos horarios  habilitados  (pos 650 en EEPROM)

NXX  &rarr;  XX Numero de toques de timbre  00 hasta 21. Debe ser igual a los cambios de clase programados anteriormente.   
```
N17
```

### Número de la carpeta donde situar las canciones  (pos 625 en EEPROM)
FXX  &rarr;  XX Numero de carpeta  00 hasta 99.
```
F01
```

### Formato para poner DS3132 en hora
```
D-aaaa/mm/dd/hh/mm/ss
```