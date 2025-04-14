import logging
from api_interfaces.otx_api import OTXAPI
from .db_utils import query_database

# OTX Instanz
api_provider = OTXAPI()

def check_file_hash_in_db(file_hash):
    """
    Prüft, ob ein gegebener Dateihash in der lokalen Datenbank blockiert ist oder
    als IOC über OTX gemeldet wurde.
    """
    # Erst lokal prüfen
    result = query_database("SELECT value FROM blocked_files WHERE file_hash = ?", (file_hash,))
    if result:
        return {'status': 'blocked', 'message': 'Blocked file hash (database)'}

    # Danach OTX prüfen
    otx_result = api_provider.check_hash(file_hash)
    if otx_result:
        return {
            'status': 'blocked',
            'message': 'Malicious file hash detected in OTX',
            'details': otx_result
        }

    return None  # Erlaubt
