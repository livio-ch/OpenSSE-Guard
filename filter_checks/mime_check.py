from .db_utils import query_database

def check_mime_type_in_db(mime_type):
    """
    Prüft, ob ein MIME-Type in der lokalen Datenbank blockiert ist.
    """
    result = query_database("SELECT value FROM blocked_mimetypes WHERE value = ?", (mime_type,))
    if result:
        return {'status': 'blocked', 'message': 'Blocked MIME type'}
    return None
