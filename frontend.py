"""
Streamlit frontend for the FastAPI image/video sharing app.

Run:
    pip install streamlit requests
    streamlit run streamlit_app.py

Start FastAPI separately. Default API URL: http://127.0.0.1:8000
"""
import os
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(
    page_title="SnapShare",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    .stApp { background:  #0e1117; font-family: 'DM Sans', sans-serif; }
    [data-testid="stHeader"] { background: rgba(246,247,251,.9); }
    .block-container { max-width: 1180px; padding-top: 1.6rem; padding-bottom: 3rem; }
    .hero { background: linear-gradient(120deg,#17172f 0%,#34356d 58%,#6c63d9 100%);
            padding: 2rem 2.2rem; border-radius: 24px; color: white; margin-bottom: 1.4rem; }
    .hero h1 { font-family: 'Manrope',sans-serif; font-size: 2.25rem; font-weight: 800; margin: 0 0 .4rem 0; }
    .hero p { color: #e0e2ff; margin: 0; font-size: 1rem; }
    .eyebrow { text-transform: uppercase; letter-spacing: .16em; font-size: .72rem; font-weight: 700; color: #b9bbff; margin-bottom: .5rem; }
    .section-title { font-family: 'Manrope',sans-serif; font-size: 1.35rem; font-weight: 800; color: #20213a; }
    .muted { color: #73758b; font-size: .9rem; }
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px;
    }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 11px; font-weight: 700; min-height: 2.7rem;
    }
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
        background: #5b55d6; border-color: #5b55d6;
    }
    div[data-testid="stFileUploader"] { background: white; border-radius: 14px; padding: .4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None
if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL


def api_url(path: str) -> str:
    return st.session_state.api_url.rstrip("/") + path


def error_message(response):
    try:
        body = response.json()
        detail = body.get("detail", body)
        if isinstance(detail, list):
            return " · ".join(str(item.get("msg", item)) for item in detail)
        return str(detail)
    except Exception:
        return response.text or f"Request failed (HTTP {response.status_code})."


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}


def api_request(method, path, **kwargs):
    try:
        return requests.request(method, api_url(path),  **kwargs)
    except requests.RequestException as exc:
        st.error(
            f"Could not connect to FastAPI at **{st.session_state.api_url}**. "
            "Make sure your backend is running and the URL is correct.\n\n"
            f"Details: {exc}"
        )
        return None


def login(email, password):
    response = api_request(
        "POST",
        "/auth/jwt/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response is None:
        return False
    if response.ok:
        payload = response.json()
        st.session_state.token = payload.get("access_token")
        st.session_state.email = email
        st.success("Logged in successfully.")
        return True
    st.error(f"Login failed: {error_message(response)}")
    return False


def register(email, password):
    response = api_request(
        "POST",
        "/auth/register",
        json={"email": email, "password": password},
    )
    if response is None:
        return False
    if response.status_code in (200, 201):
        st.success("Account created. You can now log in.")
        return True
    st.error(f"Registration failed: {error_message(response)}")
    return False


def fetch_feed():
    response = api_request("GET", "/feed", headers=auth_headers())
    if response is None:
        return None
    if response.status_code == 401:
        st.session_state.token = None
        st.session_state.email = None
        st.warning("Your session expired. Please log in again.")
        return None
    if not response.ok:
        st.error(f"Could not load feed: {error_message(response)}")
        return None
    return response.json().get("posts", [])


def show_auth():
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Your moments, together</div>
          <h1>Welcome to SnapShare</h1>
          <p>Share photos and videos, discover the community feed, and keep your memories in one place.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        login_tab, register_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            st.subheader("Good to see you again")
            with st.form("login_form"):
                email = st.text_input("Email address", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", type="primary", width="stretch")
            if submitted:
                if not email.strip() or not password:
                    st.warning("Enter your email and password.")
                elif login(email.strip(), password):
                    st.rerun()
        with register_tab:
            st.subheader("Join SnapShare")
            with st.form("register_form"):
                new_email = st.text_input("Email address", key="register_email", placeholder="you@example.com")
                new_password = st.text_input("Password", type="password", key="register_password")
                confirm_password = st.text_input("Confirm password", type="password")
                create = st.form_submit_button("Create account", type="primary", width="stretch")
            if create:
                if not new_email.strip() or not new_password:
                    st.warning("Enter an email and password.")
                elif new_password != confirm_password:
                    st.warning("Passwords do not match.")
                elif len(new_password) < 8:
                    st.warning("Use a password with at least 8 characters.")
                elif register(new_email.strip(), new_password):
                    st.info("Now log in with your new account.")


def render_post(post):
    with st.container(border=True):
        top_left, top_right = st.columns([4, 1])
        email = post.get("email") or "Community member"
        with top_left:
            st.markdown(f"**{email}**")
            created = post.get("created_at")
            if created:
                try:
                    parsed = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    st.caption(parsed.strftime("%d %b %Y · %I:%M %p"))
                except (ValueError, TypeError):
                    st.caption(str(created))
        with top_right:
            if post.get("is_owner"):
                st.caption("Your post")
        url = post.get("url", "")
        file_type = (post.get("file_type") or "image").lower()
        if url:
            try:
                if file_type == "video":
                    st.video(url)
                else:
                    st.image(url, width="stretch")
            except Exception:
                st.markdown(f"[Open media]({url})")
        caption = post.get("caption")
        if caption:
            st.markdown(caption)
        st.caption(post.get("file_name") or "")
        if post.get("is_owner") and post.get("id"):
            key = f"delete_{post['id']}"
            if st.button("🗑️ Delete post", key=key, type="secondary"):
                response = api_request(
                    "DELETE",
                    f"/posts/{post['id']}",
                    headers=auth_headers(),
                )
                if response is not None:
                    if response.ok:
                        st.success("Post deleted.")
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {error_message(response)}")


def show_app():
    with st.sidebar:
        st.markdown("## 📸 SnapShare")
        st.caption("A little space for your moments.")
        st.divider()
        st.markdown("**Signed in as**")
        st.write(st.session_state.email or "User")
        st.divider()

    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Community media feed</div>
          <h1>Moments worth sharing.</h1>
          <p>Upload a photo or video, add a caption, and catch up with the community.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    upload_col, tips_col = st.columns([1.25, 1], gap="large")
    with upload_col:
        with st.container(border=True):
            st.markdown("### ✨ Share something")
            with st.form("upload_form", clear_on_submit=True):
                uploaded = st.file_uploader(
                    "Choose a photo or video",
                    type=["png", "jpg", "jpeg", "webp", "gif", "mp4", "mov", "webm", "m4v"],
                    help="Your file is uploaded to the backend, then stored by ImageKit.",
                )
                caption = st.text_area("Caption", placeholder="What would you like to share?", max_chars=2000)
                submit_upload = st.form_submit_button("Upload post", type="primary", width="stretch")
            if submit_upload:
                if uploaded is None:
                    st.warning("Choose a photo or video first.")
                else:
                    files = {
                        "file": (
                            uploaded.name,
                            uploaded.getvalue(),
                            uploaded.type or "application/octet-stream",
                        )
                    }
                    with st.spinner("Uploading your media…"):
                        response = api_request(
                            "POST",
                            "/upload",
                            headers=auth_headers(),
                            files=files,
                            data={"caption": caption},
                            timeout=180,
                        )
                    if response is not None:
                        if response.ok:
                            st.success("Your post is live!")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {error_message(response)}")
    with tips_col:
        with st.container(border=True):
            st.markdown("### 💡 Quick guide")
            st.markdown(
                "- **Log in** to access your feed.\n"
                "- Upload an image or video and add an optional caption.\n"
                "- You can delete posts that belong to your account.\n"
                "- Media is stored through your configured ImageKit account."
            )

    st.divider()
    feed_title, refresh_col = st.columns([4, 1])
    with feed_title:
        st.markdown('<div class="section-title">Community feed</div>', unsafe_allow_html=True)
        st.markdown('<div class="muted">The latest posts, all in one place.</div>', unsafe_allow_html=True)
    with refresh_col:
        refresh = st.button("↻ Refresh feed", width="stretch")
    if refresh:
        st.rerun()

    posts = fetch_feed()
    if posts is None:
        return
    if not posts:
        st.info("No posts yet. Be the first to share a moment!")
        return

    # Keep the feed readable while using the full page width.
    for post in posts:
        render_post(post)


st.session_state.api_url = st.session_state.api_url.rstrip("/")
if st.session_state.token:
    show_app()
else:
    show_auth()
