import re

ALLOWED_CHARS = re.compile(r'^[A-Za-z0-9_]+$')

def is_valid_username(username):
    return bool(ALLOWED_CHARS.match(username)) 