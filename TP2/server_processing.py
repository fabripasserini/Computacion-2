import argparse
import socketserver
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from common.protocol import receive_message_sync, send_message_sync
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance
from processor.image_processor import analyze_images
from processor.advanced_analysis import (
    detect_technologies,
    analyze_seo,
    extract_structured_data,
    analyze_accessibility,
)

# --- Mapeo de tareas a funciones ---

TASK_MAP = {
    "screenshot": generate_screenshot,
    "performance": analyze_performance,
    "images": analyze_images,
    "technologies": detect_technologies,
    "seo": analyze_seo,
    "structured_data": extract_structured_data,
    "accessibility": analyze_accessibility,
}

def execute_task_wrapper(args):
    """
    Wrapper para llamar a la función de tarea correcta con los argumentos correctos.
    """
    task_name, url, image_urls, html_content = args
    
    if task_name not in TASK_MAP:
        return {"error": f"Tarea desconocida: {task_name}"}

    func = TASK_MAP[task_name]
    
    # Separar tareas por los argumentos que necesitan
    if task_name == 'images':
        return func(url, image_urls)
    elif task_name in ['screenshot', 'performance']:
        return func(url)
    elif task_name in ['seo', 'structured_data', 'accessibility']:
        return {task_name: func(html_content)}
    elif task_name == 'technologies':
        return func(html_content, url)
    else:
        # Fallback por si se añade una tarea y no se maneja aquí
        return {"error": f"La tarea '{task_name}' no tiene un manejador de argumentos definido."}


# --- Servidor TCP ---

class TaskHandler(socketserver.BaseRequestHandler):
    """
    Manejador para cada conexión de cliente.
    Recibe una tarea, la ejecuta en el pool de procesos y devuelve el resultado.
    """
    def handle(self):
        print(f"Conexión recibida de {self.client_address}")
        try:
            job = receive_message_sync(self.request)
            if not job or "url" not in job or "tasks" not in job:
                print("Trabajo inválido recibido. Cerrando conexión.")
                return

            url = job["url"]
            tasks = job["tasks"]
            # Argumentos opcionales
            image_urls = job.get("image_urls", [])
            html_content = job.get("html_content", None)
            
            print(f"Trabajo recibido para URL: {url} con tareas: {tasks}")

            # Preparar los argumentos para el pool de procesos
            task_args = [(task, url, image_urls, html_content) for task in tasks]

            # Ejecutar tareas en el pool
            results = list(self.server.pool.map(execute_task_wrapper, task_args))
            
            # Consolidar resultados
            final_result = {"url": url, "status": "completed"}
            for res in results:
                final_result.update(res)

            # Enviar el resultado de vuelta
            send_message_sync(self.request, final_result)
            print(f"Resultados enviados para {url}")

        except Exception as e:
            print(f"Error al manejar la solicitud de {self.client_address}: {e}")
        finally:
            print(f"Cerrando conexión con {self.client_address}")
            self.request.close()

class ProcessingServer(socketserver.ThreadingTCPServer):
    """
    Servidor TCP que utiliza un pool de procesos para manejar tareas.
    """
    def __init__(self, server_address, handler_class, pool):
        super().__init__(server_address, handler_class)
        self.pool = pool
        self.allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(
        description="Servidor de Procesamiento Distribuido",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    parser.add_argument(
        "-n", "--processes", type=int, default=multiprocessing.cpu_count(),
        help="Número de procesos en el pool (default: CPU count)"
    )
    args = parser.parse_args()

    # Usar 'fork' para evitar problemas con Playwright en nuevos procesos
    multiprocessing.set_start_method("fork", force=True)

    with ProcessPoolExecutor(max_workers=args.processes) as pool:
        print(f"Pool de procesos creado con {args.processes} workers.")
        
        server_address = (args.ip, args.port)
        
        with ProcessingServer(server_address, TaskHandler, pool) as server:
            print(f"Servidor de Procesamiento escuchando en {args.ip}:{args.port}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nServidor detenido por el usuario.")
            finally:
                server.shutdown()

if __name__ == "__main__":
    main()