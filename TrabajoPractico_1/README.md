#Trabajo Practico N°1

##Descripcion: 
Este proyecto implementa un sistema distribuido en procesos para el análisis de datos biométricos y su almacenamiento en una cadena de bloques local. El sistema se divide en dos partes principales.

###Generador.py
Este archivo se encarga de:
Generar 60 muestras de datos biométricos simulados (frecuencia, presión y oxígeno) en tiempo real (1 por segundo).
Distribuir estos datos a tres procesos analizadores 
Procesar cada señal en paralelo, calculando la media y la desviación estándar 
Validar los resultados en un proceso verificador, marcando los bloques con una alerta si es necesario.
Construir un bloque de la cadena por cada muestra procesada, calculando su hash SHA-256.
Persistir la cadena de bloques completa en el archivo `blockchain.json` al finalizar la ejecución.

###Verificar_cadena.py

Este archivo se encarga de:
eer** el archivo `blockchain.json`.
Recalcular y verificar el hash de cada bloque 
Verificar que el encadenamiento de los bloques sea correcto.
Generar un reporte llamado `resultados.txt` 

##Ejecucion
Para la ejecucion se debe seguir el siguente orden:
1. python generador.py
2. python verificar_cadena.py
3. cat reporte.txt Pra observar los resultados
