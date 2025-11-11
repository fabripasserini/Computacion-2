
import requests
from PIL import Image
import base64
from io import BytesIO
from urllib.parse import urljoin

def create_thumbnail(image_bytes: bytes, size: tuple = (128, 128)) -> bytes | None:
    """
    Crea un thumbnail a partir de los bytes de una imagen.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail(size)
        
        # Guardar la imagen en formato PNG en memoria
        thumb_io = BytesIO()
        img.save(thumb_io, format='PNG')
        return thumb_io.getvalue()
    except Exception as e:
        print(f"Error al crear thumbnail: {e}")
        return None

def download_and_process_image(image_url: str, base_url: str) -> str | None:
    """
    Descarga una imagen, crea un thumbnail y lo codifica en base64.
    """
    try:
        # Construir URL absoluta si es relativa
        full_url = urljoin(base_url, image_url)
        
        response = requests.get(full_url, timeout=10, stream=True)
        response.raise_for_status()

        # Leer solo una cantidad limitada de datos para evitar ataques
        content = response.raw.read(2 * 1024 * 1024, decode_content=True) # Límite de 2MB

        thumbnail_bytes = create_thumbnail(content)
        
        if thumbnail_bytes:
            return base64.b64encode(thumbnail_bytes).decode('utf-8')
        return None
    except requests.RequestException as e:
        print(f"Error al descargar la imagen {full_url}: {e}")
        return None
    except Exception as e:
        print(f"Error al procesar la imagen {full_url}: {e}")
        return None

def analyze_images(base_url: str, image_urls: list, max_images: int = 5) -> dict:
    """
    Descarga las imágenes principales, genera thumbnails y los devuelve en base64.
    Se ejecuta en el pool de procesos.
    """
    print(f"Procesando [images] para: {base_url}")
    thumbnails = []
    
    # Limitar la cantidad de imágenes a procesar
    for img_url in image_urls[:max_images]:
        if not img_url:
            continue
        
        thumbnail_b64 = download_and_process_image(img_url, base_url)
        if thumbnail_b64:
            thumbnails.append(thumbnail_b64)
            
    return {"thumbnails": thumbnails}

