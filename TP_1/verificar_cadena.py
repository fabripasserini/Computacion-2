from hashlib import sha256
import json
import sys

BLOCKCHAIN_FILE = "blockchain.json"
REPORT_FILE = "reporte.txt"

def calcular_hash(prev_hash, datos, timestamp):
    datos_str = json.dumps(datos, sort_keys=True)
    bloque_raw = prev_hash + datos_str + timestamp
    return sha256(bloque_raw.encode("utf-8")).hexdigest()

def verificar_cadena():
    try:
        with open(BLOCKCHAIN_FILE, "r") as f:
            cadena = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{BLOCKCHAIN_FILE}'. Asegúrese de ejecutar 'generador.py' primero.", file=sys.stderr)
        return
    except json.JSONDecodeError:
        print(f"Error: El archivo '{BLOCKCHAIN_FILE}' no es un JSON válido.", file=sys.stderr)
        return

    len_data = len(cadena)
    if len_data == 0:
        print("La cadena de bloques está vacía. No hay nada que verificar.")
        return

    print(f"--- Verificando la integridad de la cadena ({len_data} bloques) ---")

    corruptos = []
    bloques_con_alerta = 0
    promedios_frecuencia = []
    promedios_presion = []
    promedios_oxigeno = []

    for i, bloque in enumerate(cadena):
        if bloque.get("alerta"):
            bloques_con_alerta += 1
        
        promedios_frecuencia.append(bloque["datos"]["frecuencia"]["media"])
        promedios_presion.append(bloque["datos"]["presion"]["media"])
        promedios_oxigeno.append(bloque["datos"]["oxigeno"]["media"])

        prev_hash_almacenado = bloque.get("prev_hash")
        
        if i == 0:
            if prev_hash_almacenado != "00000000000000000000000000000000000000000000000000000000000000000":
                corruptos.append(f"Bloque {i+1}: 'prev_hash' incorrecto. Se esperaba el valor inicial.")
        else:
            prev_bloque = cadena[i-1]
            if prev_hash_almacenado != prev_bloque.get("hash"):
                corruptos.append(f"Bloque {i+1}: 'prev_hash' no coincide con el 'hash' del bloque anterior.")
        
        hash_recalculado = calcular_hash(
            bloque.get("prev_hash"),
            bloque.get("datos"),
            bloque.get("timestamp")
        )

        if bloque.get("hash") != hash_recalculado:
            corruptos.append(f"Bloque {i+1}: 'hash' incorrecto. Esperado: {hash_recalculado}, Encontrado: {bloque.get('hash')}.")

    print("\nVerificación de la integridad finalizada.")
    print("-" * 40)

    with open(REPORT_FILE, "w") as f:
        f.write("--- Reporte de la Cadena de Bloques ---\n\n")
        f.write(f"Cantidad total de bloques: {len_data}\n")
        f.write(f"Número de bloques con alertas: {bloques_con_alerta}\n\n")

        if not corruptos:
            f.write("La cadena de bloques es íntegra y no contiene errores.\n\n")
        else:
            f.write(f"Se encontraron un total de {len(corruptos)} errores de integridad:\n")
            for error in corruptos:
                f.write(f"- {error}\n")
            f.write("\n")
        
        f.write("-" * 40 + "\n")
        f.write("Promedios Generales:\n")
        
        if len_data > 0:
            f.write(f"  Frecuencia: {sum(promedios_frecuencia) / len_data:.2f}\n")
            f.write(f"  Presión: {sum(promedios_presion) / len_data:.2f}\n")
            f.write(f"  Oxígeno: {sum(promedios_oxigeno) / len_data:.2f}\n")
        else:
            f.write("  No hay datos para calcular promedios.\n")
        f.write("-" * 40 + "\n")
    
    print(f"Reporte generado en '{REPORT_FILE}'.")

if __name__ == "__main__":
    verificar_cadena()