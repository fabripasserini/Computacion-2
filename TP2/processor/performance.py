
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import time

async def measure_performance_async(url: str, timeout: int = 30000) -> dict | None:
    """
    Mide el rendimiento de carga de una página de forma asíncrona.

    Args:
        url: La URL a analizar.
        timeout: Tiempo de espera en milisegundos.

    Returns:
        Un diccionario con los datos de rendimiento, o None si falla.
    """
    performance_data = {
        "load_time_ms": 0,
        "num_requests": 0,
        "total_size_kb": 0,
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Contadores
            request_count = 0
            total_size = 0

            def on_response(response):
                nonlocal request_count, total_size
                request_count += 1
                # response.body_size() puede ser útil, pero a veces es 0.
                # Usamos headers para una estimación más fiable.
                size = response.headers.get('content-length')
                if size:
                    total_size += int(size)

            page.on("response", on_response)

            start_time = time.time()
            
            await page.goto(url, timeout=timeout, wait_until='load')
            
            end_time = time.time()

            await browser.close()

            performance_data["load_time_ms"] = int((end_time - start_time) * 1000)
            performance_data["num_requests"] = request_count
            performance_data["total_size_kb"] = round(total_size / 1024, 2)
            
            return performance_data

    except PlaywrightTimeoutError:
        print(f"Error de timeout al analizar rendimiento de {url}")
        return None
    except Exception as e:
        print(f"Error inesperado al analizar rendimiento de {url}: {e}")
        return None

def analyze_performance(url: str) -> dict:
    """
    Función síncrona que envuelve la operación asíncrona de análisis.
    """
    print(f"Procesando [performance] para: {url}")
    try:
        perf_data = asyncio.run(measure_performance_async(url))
        if perf_data:
            return {"performance": perf_data}
        else:
            return {"performance": None, "error_performance": f"No se pudo analizar el rendimiento para {url}"}
    except Exception as e:
        return {"performance": None, "error_performance": f"Error en el proceso de análisis de rendimiento: {e}"}

