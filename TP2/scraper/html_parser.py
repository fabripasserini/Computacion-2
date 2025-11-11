
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def parse_html(html_content: str, base_url: str):
    """
    Analiza el contenido HTML y extrae la información requerida.
    
    Nota: BeautifulSoup es bloqueante. Para páginas muy grandes, esto podría
    ejecutarse en un executor para no bloquear el event loop de asyncio.
    
    Args:
        html_content: El contenido HTML como string.
        base_url: La URL base para resolver enlaces relativos.

    Returns:
        Un diccionario con los datos extraídos.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 1. Título de la página
    title = soup.title.string.strip() if soup.title else "Sin título"
    
    # 2. Todos los enlaces
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convertir enlaces relativos a absolutos
        full_url = urljoin(base_url, href)
        links.append(full_url)
        
    # 3. URLs de imágenes y cantidad
    image_urls = [img['src'] for img in soup.find_all('img', src=True)]
    images_count = len(image_urls)
    
    # 4. Estructura de headers
    structure = {f"h{i}": len(soup.find_all(f"h{i}")) for i in range(1, 7)}
    
    return {
        "title": title,
        "links": links,
        "image_urls": image_urls, # Para enviar al servidor de procesamiento
        "structure": structure,
        "images_count": images_count,
    }

