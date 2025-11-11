
import requests
import argparse
import json
import time

def main():
    parser = argparse.ArgumentParser(description="Cliente para el Servidor de Scraping Asíncrono")
    parser.add_argument("server_url", help="URL base del servidor (ej: http://127.0.0.1:8000)")
    parser.add_argument("scrape_url", help="URL del sitio a scrapear (ej: https://www.python.org)")
    args = parser.parse_args()

    server_base_url = args.server_url.rstrip('/')

    try:
        # 1. Iniciar la tarea de scraping
        scrape_api_url = f"{server_base_url}/scrape"
        params = {"url": args.scrape_url}
        
        print(f"Enviando solicitud para iniciar scraping de: {args.scrape_url}")
        response = requests.get(scrape_api_url, params=params, timeout=30)
        response.raise_for_status()
        
        initial_data = response.json()
        if initial_data.get("status") != "pending" or "task_id" not in initial_data:
            print("Error: La respuesta inicial del servidor no fue la esperada.")
            print(json.dumps(initial_data, indent=2))
            return
            
        task_id = initial_data["task_id"]
        print(f"Tarea iniciada con ID: {task_id}\n")

        # 2. Consultar el estado de la tarea periódicamente
        status_url = f"{server_base_url}/status/{task_id}"
        while True:
            print("Consultando estado de la tarea...")
            status_response = requests.get(status_url, timeout=10)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            current_status = status_data.get("status")
            print(f"Estado actual: {current_status.upper()}")

            if current_status == "completed":
                break
            elif current_status == "failed":
                print("\n--- La Tarea Falló ---")
                print(f"Error: {status_data.get('error', 'Causa desconocida')}")
                return
            
            time.sleep(5) # Esperar 5 segundos antes de la siguiente consulta

        # 3. Obtener el resultado final
        print("\nTarea completada. Obteniendo resultados...")
        result_url = f"{server_base_url}/result/{task_id}"
        result_response = requests.get(result_url, timeout=60)
        result_response.raise_for_status()

        # Imprimir la respuesta JSON formateada
        print("\n--- Respuesta Final del Servidor ---")
        print(json.dumps(result_response.json(), indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")
    except json.JSONDecodeError:
        print("\nError: La respuesta del servidor no es un JSON válido.")
        print("Respuesta recibida:")
        print(response.text if 'response' in locals() else "No se recibió respuesta.")

if __name__ == "__main__":
    main()
