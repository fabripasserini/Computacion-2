
import json

def encode_data(data):
    """Serializa datos a JSON."""
    try:
        return json.dumps(data).encode('utf-8')
    except (TypeError, ValueError) as e:
        print(f"Error serializando datos: {e}")
        return None

def decode_data(encoded_data):
    """Deserializa datos desde JSON."""
    try:
        return json.loads(encoded_data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error deserializando datos: {e}")
        return None
