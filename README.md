# 🟢 Slime Chat

A real-time chat application built with Streamlit that allows multiple users to chat with each other in a shared room.

## Features

- 🔐 **Simple Login**: Username-based authentication (A-Z, a-z, 0-9, underscore allowed)
- 💬 **Real-time Chat**: Messages update automatically every 5 seconds
- 👥 **Online Users**: See who's currently active in the sidebar
- 🎨 **Dark Theme**: Modern grey chat interface with colored usernames
- ⏰ **timestamps**: Each message shows when it was sent
- 🗑️ **Admin Controls**: Flush all messages when needed
- 📱 **Responsive**: Works on desktop and mobile browsers

## How to Run Locally

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <your-repo-url>
   cd slimeserver
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run slime_chat.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, visit that URL manually

### Multi-User Testing

To test with multiple users:
1. Open the app in different browsers (Chrome, Firefox, Edge, etc.)
2. Or open multiple incognito/private windows
3. Log in with different usernames
4. Start chatting!

## File Structure

```
slimeserver/
├── slime_chat.py      # Main Streamlit app
├── chat_storage.py    # Message and user storage functions
├── chat.py           # Chat rendering functions
├── auth.py           # Username validation
├── requirements.txt   # Python dependencies
├── chat_messages.json # Stored chat messages (auto-created)
└── online_users.json # Online user tracking (auto-created)
```

## Usage

1. **Login**: Enter a username (alphanumeric + underscore only)
2. **Chat**: Type messages in the input box and press Send
3. **View Online Users**: Check the "👥 Online" tab in the sidebar
4. **Admin**: Use the "⚙️ Admin" tab to flush all messages
5. **Auto-refresh**: Chat updates automatically every 5 seconds

## Technical Details

- **Storage**: Uses JSON files for persistence (suitable for local/demo use)
- **Online Detection**: Users are considered online if active within 15 seconds
- **Message Limit**: Shows last 10 messages in chat
- **Auto-cleanup**: Removes inactive users automatically

---

Built with ❤️ using Streamlit 