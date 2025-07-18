import random
import hashlib

def get_username_color(username):
    # Deterministically assign a color based on username hash
    colors = [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6",
        "#bcf60c", "#fabebe", "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3",
        "#808000", "#ffd8b1", "#000075", "#808080", "#ffffff", "#000000"
    ]
    h = int(hashlib.sha256(username.encode()).hexdigest(), 16)
    return colors[h % len(colors)]


def render_chat(messages):
    last_10 = messages[-10:]  # keep chronological order (oldest to newest)
    rendered = []
    
    for i, msg in enumerate(last_10):
        # Format timestamp to tenths of a second
        ts = msg.get('timestamp', '')
        if ts:
            try:
                dt, ms = ts.split('.')
                ts_disp = f"{dt}.{ms[0]}"
            except Exception:
                ts_disp = ts
        else:
            ts_disp = ''
        
        color = get_username_color(msg['user'])
        rendered.append(
            f"<span style='color:#888;font-size:0.9em'>[{ts_disp}]</span> "
            f"<b style='color:{color}'>{msg['user']}</b>: "
            f"<span>{msg['text']}</span>"
        )
    return rendered