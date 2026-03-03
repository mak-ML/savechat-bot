import re
from typing import Optional

def sanitize_input(text: str, max_length: int = 4096) -> str:
    if not text:
        return ""
    text = text[:max_length]
    text = re.sub(r'[^\w\s\-.,!?@#]', '', text)
    return text.strip()

def validate_sql_query(query: str) -> bool:
    query_lower = query.lower().strip()
    
    dangerous_keywords = [
        'drop', 'delete', 'update', 'insert', 
        'alter', 'truncate', 'create', 'grant',
        'revoke', 'exec', 'execute'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            return False
    
    if not query_lower.startswith('select'):
        return False
        
    return True

def is_valid_user_id(user_id: int) -> bool:
    return 0 < user_id < 10**12