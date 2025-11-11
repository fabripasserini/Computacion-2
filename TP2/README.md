# TP2 - Sistema de Scraping y Análisis Web Distribuido

Este proyecto implementa un sistema distribuido de scraping y análisis web utilizando Python, compuesto por dos servidores que trabajan de forma coordinada.

## Estructura del Proyecto

```
TP2/
├── server_scraping.py          
├── server_processing.py        
├── client.py                   
├── scraper/
│   ├── __init__.py
│   ├── html_parser.py         
│   ├── metadata_extractor.py  
│   └── async_http.py           
├── processor/
│   ├── __init__.py
│   ├── screenshot.py           
│   ├── performance.py         
│   └── image_processor.py      
├── common/
│   ├── __init__.py
│   ├── protocol.py            
│   └── serialization.py        
├── requirements.txt
└── README.md
```

## Instalación

1.  **Clonar el repositorio:**
    ```bash
    
    # git clone https://github.com/fabripasserini/Computacion-2.git 
    # cd TP2
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    python3 -m venv TP2/venv
    source TP2/venv/bin/activate
    ```

3.  **Instalar dependencias de Python:**
    ```bash
    pip install -r TP2/requirements.txt
    ```

4.  **Instalar navegadores para Playwright:**
    ```bash
    playwright install
    # Si hay problemas con dependencias del sistema, ejecutar:
    # sudo TP2/venv/bin/playwright install-deps
    ```

## Ejecución

Para ejecutar el sistema, primero debes iniciar el servidor de procesamiento, luego el servidor de scraping, y finalmente puedes usar el cliente para enviar solicitudes.

### 1. Iniciar el Servidor de Procesamiento (Parte B)

Este servidor maneja tareas computacionalmente intensivas.

```bash
source TP2/venv/bin/activate
python TP2/server_processing.py -i 127.0.0.1 -p 8001 -n $(nproc) &
```

-   `-i`: Dirección IP de escucha.
-   `-p`: Puerto de escucha.
-   `-n`: Número de procesos en el pool (por defecto, el número de CPUs). El `&` al final lo ejecuta en segundo plano.

### 2. Iniciar el Servidor de Scraping (Parte A)

Este es el servidor principal con el que interactúa el cliente.

```bash
source TP2/venv/bin/activate
python TP2/server_scraping.py -i 127.0.0.1 -p 8000 --proc-host 127.0.0.1 --proc-port 8001 &
```

-   `-i`: Dirección IP de escucha para el servidor de scraping.
-   `-p`: Puerto de escucha para el servidor de scraping.
-   `--proc-host`: Host del servidor de procesamiento.
-   `--proc-port`: Puerto del servidor de procesamiento.
-   El `&` al final lo ejecuta en segundo plano.

### 3. Ejecutar el Cliente de Prueba

Una vez que ambos servidores estén en funcionamiento, puedes enviar una solicitud de scraping.

```bash
source TP2/venv/bin/activate
python TP2/client.py http://127.0.0.1:8000 https://www.python.org
```

-   El primer argumento es la URL base del servidor de scraping.
-   El segundo argumento es la URL del sitio web a scrapear.

### Detener los Servidores

Para detener los servidores que se ejecutan en segundo plano, puedes usar `jobs` para listar los procesos y `kill %<job_id>` para terminarlos, o `pkill -f server_processing.py` y `pkill -f server_scraping.py`.

```bash
# Listar procesos en segundo plano
jobs

# Terminar un proceso específico (reemplaza <job_id> con el número del job)
# kill %<job_id>

# O terminar por nombre de archivo
pkill -f server_processing.py
pkill -f server_scraping.py
```

## Notas Adicionales

-   El argumento `-w` (workers) en `server_scraping.py` controla el tamaño del `ThreadPoolExecutor` utilizado para tareas síncronas (parsing HTML). `aiohttp` es asíncrono y maneja la concurrencia de clientes por sí mismo.
-   Se utiliza `playwright` para la generación de screenshots y análisis de rendimiento, lo que requiere la instalación de los navegadores correspondientes.
-   La comunicación entre `server_scraping.py` y `server_processing.py` se realiza mediante sockets TCP con un protocolo de mensajes con longitud prefijada.
