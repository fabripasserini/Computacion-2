
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import base64

async def take_screenshot_async(url: str, timeout: int = 30000) -> bytes | None:
    """
    Toma una captura de pantalla de una URL de forma asíncrona.

    Args:
        url: La URL de la página a capturar.
        timeout: Tiempo de espera en milisegundos.

    Returns:
        Los datos de la imagen en bytes, o None si falla.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout, wait_until='networkidle')
            screenshot_bytes = await page.screenshot(type='png', full_page=True)
            await browser.close()
            return screenshot_bytes
    except PlaywrightTimeoutError:
        print(f"Error de timeout al navegar a {url}")
        return None
    except Exception as e:
        print(f"Error inesperado al tomar la captura de {url}: {e}")
        return None

def generate_screenshot(url: str) -> dict:
    """
    Función síncrona que envuelve la operación asíncrona de Playwright.
    Se ejecuta en el pool de procesos.
    """
    print(f"Procesando [screenshot] para: {url}")
    try:
        # Playwright es asíncrono por naturaleza, así que necesitamos correr
        # un event loop de asyncio aquí.
        screenshot_bytes = asyncio.run(take_screenshot_async(url))
        if screenshot_bytes:
            return {"screenshot": base64.b64encode(screenshot_bytes).decode('utf-8')}
        else:
            return {"screenshot": None, "error_screenshot": f"No se pudo generar la captura para {url}"}
    except Exception as e:
        return {"screenshot": None, "error_screenshot": f"Error en el proceso de captura: {e}"}

