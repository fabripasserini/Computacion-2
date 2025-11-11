import struct
import asyncio
import json
from .serialization import encode_data, decode_data

# Un entero de 4 bytes sin signo para la longitud del mensaje
HEADER_FORMAT = '!I'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# --- Funciones Asíncronas ---

async def send_message_async(writer: asyncio.StreamWriter, data):
    """
    Serializa, empaqueta y envía un mensaje a través de un stream asíncrono.
    """
    serialized_data = encode_data(data)
    if not serialized_data:
        return

    try:
        header = struct.pack(HEADER_FORMAT, len(serialized_data))
        writer.write(header)
        await writer.drain()
        writer.write(serialized_data)
        await writer.drain()
    except (ConnectionResetError, BrokenPipeError) as e:
        print(f"Error de conexión al enviar mensaje asíncrono: {e}")

async def receive_message_async(reader: asyncio.StreamReader):
    """
    Recibe, desempaqueta y deserializa un mensaje desde un stream asíncrono.
    """
    try:
        header = await reader.readexactly(HEADER_SIZE)
        if not header:
            return None
        
        msg_len = struct.unpack(HEADER_FORMAT, header)[0]

        serialized_data = await reader.readexactly(msg_len)
        if not serialized_data:
            return None

        return decode_data(serialized_data)
    except (asyncio.IncompleteReadError, ConnectionResetError) as e:
        print(f"Error de conexión al recibir mensaje asíncrono: {e}")
        return None

# --- Funciones Síncronas ---

def send_message_sync(sock, data):
    """
    Serializa, empaqueta y envía un mensaje a través de un socket síncrono.
    """
    serialized_data = encode_data(data)
    if not serialized_data:
        return False
    
    try:
        header = struct.pack(HEADER_FORMAT, len(serialized_data))
        sock.sendall(header)
        sock.sendall(serialized_data)
        return True
    except (ConnectionResetError, BrokenPipeError) as e:
        print(f"Error de conexión al enviar mensaje síncrono: {e}")
        return False

def receive_message_sync(sock):
    """
    Recibe, desempaqueta y deserializa un mensaje desde un socket síncrono.
    """
    try:
        header = sock.recv(HEADER_SIZE)
        if not header or len(header) < HEADER_SIZE:
            return None
        
        msg_len = struct.unpack(HEADER_FORMAT, header)[0]
        
        # Recibir el resto del mensaje en un bucle para asegurar que se lee todo
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = sock.recv(min(msg_len - bytes_recd, 4096))
            if not chunk:
                raise ConnectionResetError("La conexión se cerró inesperadamente.")
            chunks.append(chunk)
            bytes_recd += len(chunk)
        
        serialized_data = b''.join(chunks)
        return decode_data(serialized_data)
    except (ConnectionResetError, struct.error) as e:
        print(f"Error de conexión al recibir mensaje síncrono: {e}")
        return None