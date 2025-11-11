
from bs4 import BeautifulSoup

def extract_metadata(html_content: str):
    """
    Extrae metadatos relevantes de un contenido HTML.
    
    Args:
        html_content: El contenido HTML como string.

    Returns:
        Un diccionario con los metadatos.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    meta_tags = {}
    
    # Description
    desc = soup.find('meta', attrs={'name': 'description'})
    if desc and desc.get('content'):
        meta_tags['description'] = desc['content']
        
    # Keywords
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    if keywords and keywords.get('content'):
        meta_tags['keywords'] = keywords['content']
        
    # Open Graph tags
    og_tags = soup.find_all('meta', property=lambda p: p and p.startswith('og:'))
    for tag in og_tags:
        prop = tag.get('property')
        content = tag.get('content')
        if prop and content:
            meta_tags[prop] = content
            
    return meta_tags

