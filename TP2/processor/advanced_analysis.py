"""
Módulo para análisis avanzado de páginas web.
"""
import json
from bs4 import BeautifulSoup
from webtech import WebTech

def detect_technologies(html_content, url):
    """
    Detecta las tecnologías utilizadas en una página web.
    """
    try:
        wt = WebTech()
        results = wt.start(url, html=html_content)
        # Convert results to a more JSON-friendly format
        tech_list = []
        for tech in results:
            tech_list.append({
                "name": tech.name,
                "version": tech.version,
                "categories": [c.name for c in tech.categories]
            })
        return {"technologies": tech_list}
    except Exception as e:
        return {"error": f"Technology detection failed: {str(e)}"}

def analyze_seo(html_content):
    """
    Realiza un análisis SEO básico.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    seo_data = {
        "title": soup.title.string if soup.title else None,
        "title_length": len(soup.title.string) if soup.title else 0,
        "meta_description": None,
        "meta_description_length": 0,
        "h1_tags": [h1.text.strip() for h1 in soup.find_all('h1')],
        "images_missing_alt": 0,
        "lang": soup.html.get('lang', None) if soup.html else None,
    }

    # Meta Description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        seo_data["meta_description"] = meta_desc.get('content', '')
        seo_data["meta_description_length"] = len(seo_data["meta_description"])

    # Alt tags
    for img in soup.find_all('img'):
        if not img.get('alt', '').strip():
            seo_data["images_missing_alt"] += 1
            
    # Basic SEO Score
    score = 0
    if 10 < seo_data["title_length"] < 70:
        score += 25
    if 70 < seo_data["meta_description_length"] < 160:
        score += 25
    if seo_data["h1_tags"]:
        score += 25
    if seo_data["images_missing_alt"] == 0:
        score += 25
    seo_data["seo_score"] = score

    return seo_data

def extract_structured_data(html_content):
    """
    Extrae datos estructurados (JSON-LD) de la página.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    structured_data = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return {"structured_data": structured_data}

def analyze_accessibility(html_content):
    """
    Realiza un análisis de accesibilidad básico.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    accessibility_info = {
        "lang_attribute_present": soup.html.has_attr('lang') if soup.html else False,
        "images_missing_alt": 0,
        "links_missing_text": 0,
    }

    # Alt tags
    for img in soup.find_all('img'):
        if not img.get('alt', '').strip():
            accessibility_info["images_missing_alt"] += 1
            
    # Link text
    for a in soup.find_all('a'):
        if not a.text.strip() and not a.find('img'): # Simple check
            accessibility_info["links_missing_text"] += 1

    return accessibility_info
