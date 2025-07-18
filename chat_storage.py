import os
import json
import time
from contextlib import contextmanager
from datetime import datetime

CHAT_FILE = os.path.join(os.path.dirname(__file__), "chat_messages.json")
LOCK_FILE = CHAT_FILE + ".lock"

# Simple cache for messages
_message_cache = None
_last_modified = None

ONLINE_USERS_FILE = os.path.join(os.path.dirname(__file__), "online_users.json")
ONLINE_THRESHOLD = 15  # seconds (reduced from 30 for faster cleanup)

# Cache for online users
_online_cache = None
_online_last_modified = None

@contextmanager
def file_lock(lockfile, timeout=5):
    start = time.time()
    while os.path.exists(lockfile):
        if time.time() - start > timeout:
            raise TimeoutError("Could not acquire file lock.")
        time.sleep(0.05)
    try:
        with open(lockfile, "w") as f:
            f.write("lock")
        yield
    finally:
        if os.path.exists(lockfile):
            os.remove(lockfile)

def load_chat():
    global _message_cache, _last_modified
    
    if not os.path.exists(CHAT_FILE):
        return []
    
    # Check if file has been modified since last cache
    current_modified = os.path.getmtime(CHAT_FILE)
    if _message_cache is not None and _last_modified == current_modified:
        return _message_cache
    
    # Load and cache messages
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        try:
            _message_cache = json.load(f)
            _last_modified = current_modified
            return _message_cache
        except Exception:
            return []

def save_chat(messages):
    global _message_cache, _last_modified
    with file_lock(LOCK_FILE):
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
        # Update cache
        _message_cache = messages
        _last_modified = os.path.getmtime(CHAT_FILE)

def append_message(user, text):
    global _message_cache, _last_modified
    with file_lock(LOCK_FILE):
        messages = load_chat()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # e.g. 2025-01-01 00:00:12.345
        messages.append({"user": user, "text": text, "timestamp": timestamp})
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
        # Update cache
        _message_cache = messages
        _last_modified = os.path.getmtime(CHAT_FILE)

def flush_chat():
    global _message_cache, _last_modified
    with file_lock(LOCK_FILE):
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        # Update cache
        _message_cache = []
        _last_modified = os.path.getmtime(CHAT_FILE) 

def update_user_activity(username):
    """Update the last activity timestamp for a user"""
    global _online_cache, _online_last_modified
    
    # Load current online users
    if os.path.exists(ONLINE_USERS_FILE):
        try:
            with open(ONLINE_USERS_FILE, "r", encoding="utf-8") as f:
                online_users = json.load(f)
        except Exception:
            online_users = {}
    else:
        online_users = {}
    
    # Update user's timestamp
    online_users[username] = datetime.utcnow().isoformat()
    
    # Save back to file
    with open(ONLINE_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(online_users, f, indent=2)
    
    # Update cache
    _online_cache = online_users
    _online_last_modified = os.path.getmtime(ONLINE_USERS_FILE) if os.path.exists(ONLINE_USERS_FILE) else None

def cleanup_stale_users():
    """Remove users who haven't been active recently"""
    global _online_cache, _online_last_modified
    
    if not os.path.exists(ONLINE_USERS_FILE):
        return
    
    try:
        with open(ONLINE_USERS_FILE, "r", encoding="utf-8") as f:
            online_users = json.load(f)
    except Exception:
        return
    
    # Filter out stale users
    now = datetime.utcnow()
    active_users = {}
    
    for username, last_activity_str in online_users.items():
        try:
            last_activity = datetime.fromisoformat(last_activity_str)
            if (now - last_activity).total_seconds() <= ONLINE_THRESHOLD:
                active_users[username] = last_activity_str
        except Exception:
            continue
    
    # Only write back if something changed
    if len(active_users) != len(online_users):
        with open(ONLINE_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(active_users, f, indent=2)
        
        # Update cache
        _online_cache = active_users
        _online_last_modified = os.path.getmtime(ONLINE_USERS_FILE)

def get_online_users():
    """Get list of currently online users (active within last 15 seconds)"""
    global _online_cache, _online_last_modified
    
    # First, cleanup stale users
    cleanup_stale_users()
    
    if not os.path.exists(ONLINE_USERS_FILE):
        return []
    
    # Check cache first
    current_modified = os.path.getmtime(ONLINE_USERS_FILE)
    if _online_cache is not None and _online_last_modified == current_modified:
        online_users = _online_cache
    else:
        # Load from file
        try:
            with open(ONLINE_USERS_FILE, "r", encoding="utf-8") as f:
                online_users = json.load(f)
                _online_cache = online_users
                _online_last_modified = current_modified
        except Exception:
            return []
    
    # Return sorted list of usernames
    return sorted(online_users.keys()) 