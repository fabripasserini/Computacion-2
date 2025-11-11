
import argparse
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from functools import partial
from urllib.parse import urlparse

from aiohttp import web

from scraper.async_http import fetch_url
from scraper.html_parser import parse_html
from scraper.metadata_extractor import extract_metadata
from common.protocol import send_message_async, receive_message_async

# --- Configuración Global ---
PROCESSING_SERVER_HOST = '127.0.0.1'
PROCESSING_SERVER_PORT = 8001
RATE_LIMIT_REQUESTS = 15  # Max requests
RATE_LIMIT_PERIOD_SECONDS = 60  # Per minute
CACHE_TTL_SECONDS = 3600  # 1 hour

# --- Almacenes de Datos en Memoria ---
tasks_db = {}  # Almacena el estado y resultado de las tareas
cache_db = {}  # Cache para resultados de scraping
rate_limit_db = {} # Para seguimiento de rate limiting por dominio

# Usar un executor para las tareas síncronas de CPU-bound (parsing)
executor = ThreadPoolExecutor(max_workers=4)


# --- Middleware de Rate Limiting (Bonus 2) ---
@web.middleware
async def rate_limit_middleware(request, handler):
    if request.path != '/scrape':
        return await handler(request)

    url = request.query.get('url')
    if not url:
        return await handler(request)
        
    domain = urlparse(url).netloc
    if not domain:
        return web.json_response({"status": "error", "message": "URL inválida"}, status=400)

    now = datetime.now(timezone.utc)
    
    # Limpiar timestamps viejos
    if domain in rate_limit_db:
        rate_limit_db[domain] = [ts for ts in rate_limit_db[domain] if now - ts < timedelta(seconds=RATE_LIMIT_PERIOD_SECONDS)]
    else:
        rate_limit_db[domain] = []

    # Verificar límite
    if len(rate_limit_db[domain]) >= RATE_LIMIT_REQUESTS:
        return web.json_response(
            {"status": "error", "message": f"Límite de peticiones alcanzado para el dominio {domain}. Intente más tarde."},
            status=429
        )

    rate_limit_db[domain].append(now)
    return await handler(request)


# --- Comunicación con el Servidor de Procesamiento ---

async def request_processing(url: str, html_content: str, image_urls: list) -> dict:
    """
    Se conecta al servidor de procesamiento, envía un trabajo y espera los resultados.
    Ahora incluye el contenido HTML para análisis avanzado.
    """
    try:
        reader, writer = await asyncio.open_connection(PROCESSING_SERVER_HOST, PROCESSING_SERVER_PORT)
    except ConnectionRefusedError:
        return {"error": "No se pudo conectar con el servidor de procesamiento."}
    
    job = {
        "url": url,
        "tasks": ["screenshot", "performance", "images", "technologies", "seo", "structured_data", "accessibility"],
        "image_urls": image_urls,
        "html_content": html_content
    }
    
    print(f"Enviando trabajo al servidor de procesamiento para {url}")
    await send_message_async(writer, job)
    
    result = await receive_message_async(reader)
    
    print(f"Resultados recibidos del servidor de procesamiento para {url}")
    writer.close()
    await writer.wait_closed()
    
    return result if result else {"error": "No se recibió respuesta del servidor de procesamiento."}


# --- Tarea de Fondo para Scraping ---

async def run_scraping_job(task_id: str, url: str):
    """
    La lógica principal de scraping y procesamiento, ejecutada en segundo plano.
    """
    loop = asyncio.get_running_loop()
    
    try:
        # 1. Verificar Caché (Bonus 2)
        now = datetime.now(timezone.utc)
        if url in cache_db and (now - cache_db[url]["timestamp"]) < timedelta(seconds=CACHE_TTL_SECONDS):
            print(f"Cache hit para la URL: {url}")
            cached_data = cache_db[url]
            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["result"] = cached_data["data"]
            return

        # 2. Iniciar Scraping
        tasks_db[task_id]["status"] = "scraping"
        html_content = await fetch_url(url)
        if not html_content:
            raise ValueError(f"No se pudo acceder a la URL: {url}")

        parsing_task = loop.run_in_executor(executor, partial(parse_html, html_content, url))
        metadata_task = loop.run_in_executor(executor, partial(extract_metadata, html_content))
        
        parsed_data = await parsing_task
        meta_tags = await metadata_task

        scraping_data = {
            "title": parsed_data["title"], "links": parsed_data["links"],
            "meta_tags": meta_tags, "structure": parsed_data["structure"],
            "images_count": parsed_data["images_count"],
        }

        # 3. Iniciar Procesamiento
        tasks_db[task_id]["status"] = "processing"
        image_urls = parsed_data.get("image_urls", [])
        processing_data = await request_processing(url, html_content, image_urls)

        # 4. Consolidar y guardar resultado
        final_response = {
            "url": url, "timestamp": now.isoformat(),
            "scraping_data": scraping_data, "processing_data": processing_data,
            "status": "success" if "error" not in processing_data else "partial_failure"
        }
        
        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["result"] = final_response
        
        # Guardar en caché
        cache_db[url] = {"timestamp": now, "data": final_response}

    except Exception as e:
        print(f"Error en la tarea {task_id} para la URL {url}: {e}")
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)


# --- Manejadores de Rutas HTTP (Bonus 1) ---

async def handle_scrape(request: web.Request) -> web.Response:
    """
    Inicia una nueva tarea de scraping y devuelve un ID de tarea.
    """
    url = request.query.get('url')
    if not url:
        return web.json_response({"status": "error", "message": "Falta el parámetro 'url'"}, status=400)

    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending", "url": url, "submitted_at": datetime.now(timezone.utc).isoformat()}
    
    # Iniciar la tarea en segundo plano
    asyncio.create_task(run_scraping_job(task_id, url))
    
    return web.json_response({"status": "pending", "task_id": task_id, "url": url})

async def handle_status(request: web.Request) -> web.Response:
    """Devuelve el estado de una tarea."""
    task_id = request.match_info.get('task_id')
    if not task_id or task_id not in tasks_db:
        return web.json_response({"status": "error", "message": "ID de tarea no encontrado"}, status=404)
    
    task_info = tasks_db[task_id]
    response = {"task_id": task_id, "status": task_info["status"]}
    if task_info["status"] == "failed":
        response["error"] = task_info.get("error")
        
    return web.json_response(response)

async def handle_result(request: web.Request) -> web.Response:
    """Devuelve el resultado de una tarea completada."""
    task_id = request.match_info.get('task_id')
    if not task_id or task_id not in tasks_db:
        return web.json_response({"status": "error", "message": "ID de tarea no encontrado"}, status=404)

    task_info = tasks_db[task_id]
    if task_info["status"] != "completed":
        return web.json_response({"status": "error", "message": f"La tarea aún no está completada. Estado actual: {task_info['status']}"}, status=400)
    
    return web.json_response(task_info["result"])

async def handle_index(request: web.Request) -> web.Response:
    return web.Response(text="Servidor de Scraping Asíncrono. Use /scrape?url=...")


# --- Función Principal ---

def main():
    parser = argparse.ArgumentParser(description="Servidor de Scraping Web Asíncrono", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Workers para el pool de hilos")
    parser.add_argument("--proc-host", default='127.0.0.1', help="Host del servidor de procesamiento")
    parser.add_argument("--proc-port", type=int, default=8001, help="Puerto del servidor de procesamiento")
    args = parser.parse_args()

    global PROCESSING_SERVER_HOST, PROCESSING_SERVER_PORT, executor
    PROCESSING_SERVER_HOST = args.proc_host
    PROCESSING_SERVER_PORT = args.proc_port
    executor = ThreadPoolExecutor(max_workers=args.workers)

    app = web.Application(middlewares=[rate_limit_middleware])
    app.router.add_get("/", handle_index)
    app.router.add_get("/scrape", handle_scrape)
    app.router.add_get("/status/{task_id}", handle_status)
    app.router.add_get("/result/{task_id}", handle_result)

    print(f"Servidor de Scraping escuchando en http://{args.ip}:{args.port}")
    print(f"Conectando al servidor de procesamiento en {args.proc_host}:{args.proc_port}")
    
    web.run_app(app, host=args.ip, port=args.port)

if __name__ == "__main__":
    main()
