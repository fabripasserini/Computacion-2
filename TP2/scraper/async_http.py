
import aiohttp

async def fetch_url(url: str, timeout: int = 30) -> str | None:
    """
    Obtiene el contenido HTML de una URL de forma asíncrona.

    Args:
        url: La URL a la que se va a hacer el fetch.
        timeout: Tiempo de espera para la solicitud.

    Returns:
        El contenido de la página como string, o None si hay un error.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                # Decodificar manualmente para manejar mejor los errores
                content = await response.read()
                return content.decode('utf-8', errors='ignore')
    except aiohttp.ClientError as e:
        print(f"Error de cliente al acceder a {url}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al hacer fetch de {url}: {e}")
        return None

