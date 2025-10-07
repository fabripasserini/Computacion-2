import datetime
import random
import multiprocessing
import json
import math
import time
import os
import collections
from hashlib import sha256
import sys
import signal
import numpy as np

PAQUETES = 60

def generar_muestra():
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "frecuencia": random.randint(60, 180),
        "presion": [random.randint(110, 180), random.randint(70, 110)],
        "oxigeno": random.randint(90, 100)
    }


def make_math(conn, clave, queue):
    ventana = collections.deque(maxlen=30)
    
    for _ in range(PAQUETES):
        try:
            data = conn.recv()
            valor = data.get(clave)
            
           
            if isinstance(valor, list):
                valor = valor[0]

            ventana.append(valor)
            
            
            media = np.mean(ventana)
            desviacion = np.std(ventana)
            
            resultado = {
                "tipo": clave,
                "timestamp": data.get("timestamp"),
                "media": round(media, 2),
                "desviacion": round(desviacion, 2)
            }
            queue.put(resultado)
            
        except EOFError:
            break
    
    
    queue.put(None)


def make_muestra(conns):
    for i in range(PAQUETES):
        print(f"Generando muestra {i+1}/{PAQUETES}...")

        muestra = generar_muestra()
        for conn in conns:
            conn.send(muestra)
        time.sleep(1)
    
    for conn in conns:
        conn.close()


def validar(queue_entrada, queue_salida):
    bloques = []
    bloques_por_timestamp = {}
    prev_hash = "00000000000000000000000000000000000000000000000000000000000000000"
    analizadores_terminados = 0
    
    while analizadores_terminados < 3:
        resultado = queue_entrada.get()
        
        if resultado is None:
            analizadores_terminados += 1
            continue

        ts = resultado["timestamp"]
        
        if ts not in bloques_por_timestamp:
            bloques_por_timestamp[ts] = {}
        
        bloques_por_timestamp[ts][resultado["tipo"]] = {
            "media": resultado["media"],
            "desviacion": resultado["desviacion"]
        }

        
        if len(bloques_por_timestamp[ts]) == 3:
            datos = bloques_por_timestamp.pop(ts)
            
            
            alerta = (
                datos["frecuencia"]["media"] >= 200 or
                datos["oxigeno"]["media"] < 90 or
                datos["presion"]["media"] >= 200
            )

            
            datos_str = json.dumps({
                "frecuencia": datos["frecuencia"],
                "presion": datos["presion"],
                "oxigeno": datos["oxigeno"]
            }, sort_keys=True)
            
            bloque_raw = prev_hash + datos_str + ts
            current_hash = sha256(bloque_raw.encode("utf-8")).hexdigest()
            
            bloque = {
                "timestamp": ts,
                "datos": datos,
                "alerta": str(alerta),  
                "prev_hash": prev_hash,
                "hash": current_hash
            }

            prev_hash = current_hash
            bloques.append(bloque)
            
            print(f"\n--- Bloque #{len(bloques)-1} Creado ---")
            print(f"Timestamp: {ts}")
            print(f"Hash: {current_hash}")
            if alerta:
                print("ALERTA: true")
            else:
                print("ALERTA: false")
            print("--------------------------\n")
            
    queue_salida.put(bloques)

def handler(sig, frame):
    print("\nCtrl+C detectado. Terminando todos los procesos...")
    for p in multiprocessing.active_children():
        p.terminate()
    sys.exit(1)

def main():
    if multiprocessing.current_process().name == "MainProcess":
        signal.signal(signal.SIGINT, handler)
    
    pipes = [multiprocessing.Pipe() for _ in range(3)]
    queue = multiprocessing.Queue()
    queue_resultados_validados = multiprocessing.Queue()

    generador_p = multiprocessing.Process(target=make_muestra, args=([p[0] for p in pipes],))
    tipos = ["frecuencia", "presion", "oxigeno"]
    analizadores = [
        multiprocessing.Process(target=make_math, args=(pipes[i][1], tipos[i], queue))
        for i in range(3)
    ]
    verificador_p = multiprocessing.Process(target=validar, args=(queue, queue_resultados_validados))

    generador_p.start()
    for p in analizadores:
        p.start()
    verificador_p.start()
    generador_p.join()
    for p in analizadores:
        p.join()
    verificador_p.join()
   
    bloques = queue_resultados_validados.get()
    
    queue.close()
    queue_resultados_validados.close()

    return bloques

if __name__ == "__main__":
    print("Iniciando la simulación. Esto tomará aproximadamente 60 segundos...")
    bloques = main()
    
  

    with open("blockchain.json", "w") as f:
        json.dump(bloques, f, indent=4)
        
    print("Simulación finalizada. Cadena de bloques guardada en blockchain.json")