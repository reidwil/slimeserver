import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh

from auth import is_valid_username
from chat_storage import (
    load_chat, append_message, flush_chat, 
    update_user_activity, get_online_users
)
from chat import render_chat

# Configure the Streamlit page
st.set_page_config(
    page_title="🟢 Slime Chat",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stTextInput > div > div > input {
        background-color: #2b2b2b;
        color: white;
        border: 1px solid #4CAF50;
        border-radius: 5px;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .chat-container {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #333;
        height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.4;
    }

    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: linear-gradient(135deg, #2b2b2b, #1e1e1e);
        border-radius: 15px;
        border: 2px solid #4CAF50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
    }
    .login-title {
        text-align: center;
        color: #4CAF50;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 0 0 15px #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

def show_login():
    """Display the login screen with welcome image and branding"""
    
    # Large welcome image at the top
    image_b64 = get_image_base64("welcome.jpg")
    if image_b64:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem; padding: 2rem; background: linear-gradient(135deg, #2b2b2b, #1e1e1e); border-radius: 15px; border: 2px solid #4CAF50;">
            <img src="data:image/jpeg;base64,{image_b64}" style="width: 300px; height: 300px; object-fit: cover; border-radius: 15px; border: 3px solid #4CAF50; box-shadow: 0 0 30px rgba(76, 175, 80, 0.5);">
        </div>
        """, unsafe_allow_html=True)
    
    # Login form container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Simple welcome header without image
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #4CAF50;">
        <h1 style="color: #4CAF50; margin: 0;">🟢 Welcome to Slime Chat</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-title">Enter Chat</div>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username (A-Z, a-z, 0-9, underscore only)",
            help="Username can only contain letters, numbers, and underscores"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("Join Chat", use_container_width=True)
        
        if submitted:
            if not username:
                st.error("⚠️ Please enter a username")
            elif not is_valid_username(username):
                st.error("⚠️ Username can only contain letters, numbers, and underscores")
            else:
                st.session_state.username = username
                st.session_state.logged_in = True
                # Add username to URL for persistent login
                st.query_params["user"] = username
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Slimebwoy 2025 branding in bottom corner
    st.markdown("""
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 999;">
        <div style="color: #4CAF50; font-size: 1.8rem; font-weight: bold; text-shadow: 0 0 15px #4CAF50; background: rgba(30, 30, 30, 0.9); padding: 10px 15px; border-radius: 10px; border: 2px solid #4CAF50;">
            Slimebwoy 2025
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_image_base64(image_path):
    """Convert image to base64 for embedding"""
    try:
        import base64
        import os
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Warning: Image file '{image_path}' not found")
            return ""
        
        # Read and encode the image
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            print(f"Successfully loaded image: {len(encoded)} characters")
            return encoded
            
    except Exception as e:
        print(f"Error loading image: {e}")
        return ""

def show_chat():
    """Display the main chat interface"""
    # Update user activity
    update_user_activity(st.session_state.username)
    
    # Auto-refresh every 5 seconds
    st_autorefresh(interval=5000, key="chat_refresh")
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <h1 style="color: #4CAF50;">🟢 Slime Chat</h1>
        <p style="color: #888;">Welcome back, <b style="color: #4CAF50;">{st.session_state.username}</b>!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main chat area
    messages = load_chat()
    rendered_messages = render_chat(messages)
    
    st.markdown("### Chat")
    
    # Chat container
    chat_html = "<div class='chat-container'>"
    if rendered_messages:
        for msg_html in rendered_messages:
            chat_html += f"<div style='margin-bottom: 8px;'>{msg_html}</div>"
    else:
        chat_html += "<div style='color: #666; text-align: center; padding: 2rem;'>No messages yet. Be the first to say hello! 👋</div>"
    chat_html += "</div>"
    
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # Message input
    with st.form("message_form", clear_on_submit=True):
        message = st.text_input(
            "Type your message here...",
            placeholder="What's on your mind?",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([3, 1, 3])
        with col2:
            submitted = st.form_submit_button("Send", use_container_width=True)
        
        if submitted and message.strip():
            append_message(st.session_state.username, message.strip())
            st.rerun()

def show_sidebar():
    """Display the sidebar with online users and admin controls"""
    with st.sidebar:
        st.markdown("## 🟢 Slime Chat")
        
        # Online users tab
        with st.expander("👥 Online Users", expanded=True):
            online_users = get_online_users()
            if online_users:
                st.markdown("**Currently Active:**")
                for user in online_users:
                    if user == st.session_state.get('username'):
                        st.markdown(f"🟢 **{user}** (you)")
                    else:
                        st.markdown(f"🟢 {user}")
                st.markdown(f"*{len(online_users)} user(s) online*")
            else:
                st.markdown("*No users currently online*")
        
        # Admin controls
        with st.expander("⚙️ Admin", expanded=False):
            st.markdown("**Chat Management:**")
            if st.button("🗑️ Clear All Messages", use_container_width=True):
                flush_chat()
                st.success("All messages cleared!")
                st.rerun()
            
            messages = load_chat()
            st.markdown(f"**Messages in chat:** {len(messages)}")
        
        # App info
        with st.expander("ℹ️ About", expanded=False):
            st.markdown("""
            **Slime Chat v2025**
            
            A real-time chat application for slime enthusiasts!
            
            - Auto-refresh every 5 seconds
            - Username-based authentication
            - Online user tracking
            - Message history
            
            Built with ❤️ using Streamlit
            """)
        
        # Logout button at bottom of sidebar
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            # Remove username from URL
            if "user" in st.query_params:
                del st.query_params["user"]
            st.rerun()

def main():
    """Main application logic"""
    # Check URL parameters for persistent login
    query_params = st.query_params
    url_username = query_params.get("user", None)
    
    # Initialize session state with URL parameter check
    if 'logged_in' not in st.session_state:
        if url_username and is_valid_username(url_username):
            st.session_state.logged_in = True
            st.session_state.username = url_username
        else:
            st.session_state.logged_in = False
            st.session_state.username = None
    
    if 'username' not in st.session_state:
        if url_username and is_valid_username(url_username):
            st.session_state.username = url_username
        else:
            st.session_state.username = None
    
    # If we have a valid username in URL but not logged in, log them in
    if url_username and is_valid_username(url_username) and not st.session_state.logged_in:
        st.session_state.logged_in = True
        st.session_state.username = url_username
    
    # If logged in but no URL parameter, add it
    if st.session_state.logged_in and st.session_state.username and not url_username:
        st.query_params["user"] = st.session_state.username
    
    # Route to appropriate screen
    if not st.session_state.logged_in:
        show_login()
    else:
        show_sidebar()
        show_chat()

if __name__ == "__main__":
    main() 