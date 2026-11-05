import streamlit as st
import streamlit.components.v1 as components
import html
import secrets
import pandas as pd
from datetime import datetime, timedelta
from modules.translation_module import translate_text, SUPPORTED_LANGUAGES
from modules.tts_module import generate_audio
from modules.speech_module import recognize_speech_from_mic
from modules.data_manager import save_translation, get_history, clear_history
from modules.user_manager import signup, login, load_users

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="EasyLingo — AI Translation", page_icon="🌐", layout="wide")

def load_css(path):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css("assets/style.css")

# Password autocomplete fix
components.html("""
<script>
(function() {
    let bound = false;
    function fix() {
        try {
            const pw = window.parent.document.querySelectorAll('input[type="password"]');
            if (pw.length >= 2) pw.forEach(i => { if (i.getAttribute('autocomplete') !== 'new-password') i.setAttribute('autocomplete','new-password'); });
            else if (pw.length === 1 && pw[0].getAttribute('autocomplete') !== 'current-password') pw[0].setAttribute('autocomplete','current-password');
        } catch(e){}
    }
    function init() {
        try {
            const body = window.parent.document.body;
            if (!body) { setTimeout(init, 150); return; }
            fix();
            if (!bound) { bound = true; new MutationObserver(fix).observe(body, {childList:true, subtree:true}); }
        } catch(e){ setTimeout(init, 150); }
    }
    init();
})();
</script>
""", height=0)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    'page': 'home', 
    'user': None, 
    'theme': 'light',
    'show_auth': False,  # Unified auth state
    'translated_text': '', 
    'toast': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.toast:
    msg, icon = st.session_state.toast
    st.toast(msg, icon=icon)
    st.session_state.toast = None

# ============================================================
# HELPERS & CALLBACKS
# ============================================================
def complete_login(username, message="Welcome back", icon="✅"):
    st.session_state.user = username
    st.session_state.show_auth = False
    st.session_state.page = 'home'
    st.session_state.toast = (f"{message}, {username}" if username else message, icon)

def cb_guest_login():
    guest_name = f"guest_{secrets.token_hex(3)}"
    users = load_users()
    if guest_name not in users:
        signup(guest_name, secrets.token_hex(16))
    complete_login(guest_name, "Signed in as guest", "👋")

def cb_signout():
    st.session_state.user = None
    st.session_state.page = 'home'
    st.session_state.show_auth = False
    st.session_state.toast = ("Signed out", "👋")

# ============================================================
# UNIFIED AUTH MODAL
# ============================================================
@st.dialog("Welcome to EasyLingo")
def auth_modal():
    st.markdown('<p style="color:#A1A1AA;font-size:1rem;margin-bottom:1rem;">Sign in or create an account to access your dashboard.</p>', unsafe_allow_html=True)
    
    # Guest Login Button (Always visible at the top)
    if st.button("👤  Continue as Guest", use_container_width=True, key="guest_login_btn"):
        cb_guest_login()
        st.rerun()
        
    st.markdown('<div class="auth-divider">or use email</div>', unsafe_allow_html=True)
    
    # Tabs for Login and Signup
    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="your-username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.form_submit_button("Sign in", type="primary", use_container_width=True):
                success, msg = login(username, password)
                if success:
                    complete_login(username)
                    st.rerun()
                else:
                    st.error(msg)
                    
    with tab_signup:
        with st.form("signup_form"):
            new_user = st.text_input("Username", placeholder="At least 3 characters")
            new_pass = st.text_input("Password", type="password", placeholder="At least 4 characters")
            confirm_pass = st.text_input("Confirm password", type="password", placeholder="Re-enter your password")
            if st.form_submit_button("Create account", type="primary", use_container_width=True):
                if len(new_user) < 3 or len(new_pass) < 4:
                    st.warning("Username must be 3+ chars, password 4+ chars.")
                elif new_pass != confirm_pass:
                    st.warning("Passwords do not match. Please re-enter.")
                else:
                    success, msg = signup(new_user, new_pass)
                    if success:
                        complete_login(new_user, "Welcome", "🎉")
                        st.rerun()
                    else:
                        st.error(msg)

# ============================================================
# NAVBAR
# ============================================================
def render_navbar():
    if st.session_state.user:
        cols = st.columns([4, 1, 1, 0.6, 1.5, 1])
        with cols[0]:
            st.markdown('<div class="nav-logo"><span class="nav-logo-mark">🌐</span>EasyLingo</div>', unsafe_allow_html=True)
        with cols[1]:
            if st.button("Dashboard", use_container_width=True, key="nav_dash"):
                st.session_state.page = 'home'; st.rerun()
        with cols[2]:
            if st.button("History", use_container_width=True, key="nav_hist"):
                st.session_state.page = 'history'; st.rerun()
        with cols[3]:
            icon = "☀️" if st.session_state.theme == 'dark' else "🌙"
            if st.button(icon, key="theme_toggle", use_container_width=True):
                st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'; st.rerun()
        with cols[4]:
            initials = st.session_state.user[:2].upper()
            st.markdown(f'<div class="nav-user"><span class="nav-user-avatar">{initials}</span>{html.escape(st.session_state.user)}</div>', unsafe_allow_html=True)
        with cols[5]:
            st.button("Sign out", key="signout", use_container_width=True, on_click=cb_signout)
    else:
        cols = st.columns([3.5, 0.8, 0.9, 0.9, 0.6, 1, 1.3])
        with cols[0]:
            st.markdown('<div class="nav-logo"><span class="nav-logo-mark">🌐</span>EasyLingo</div>', unsafe_allow_html=True)
        with cols[1]:
            if st.button("Home", use_container_width=True, key="nav_home"):
                st.session_state.page = 'home'; st.rerun()
        with cols[2]:
            st.markdown('<a href="#features" class="nav-link">Features</a>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown('<a href="#reviews" class="nav-link">Reviews</a>', unsafe_allow_html=True)
        with cols[4]:
            icon = "☀️" if st.session_state.theme == 'dark' else "🌙"
            if st.button(icon, key="theme_toggle", use_container_width=True):
                st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'; st.rerun()
        with cols[5]:
            if st.button("Sign in", key="nav_signin", use_container_width=True):
                st.session_state.show_auth = True; st.rerun()
        with cols[6]:
            if st.button("Get started", key="nav_signup", type="primary", use_container_width=True):
                st.session_state.show_auth = True; st.rerun()

render_navbar()

# ============================================================
# LANDING PAGE
# ============================================================
def render_landing():
    st.html("""
    <section class="hero">
      <div class="hero-grid"></div><div class="hero-glow"></div>
      <div class="hero-content">
        <div class="hero-badge"><span class="hero-badge-dot"></span>Now with real-time speech translation</div>
        <h1 class="hero-title">Speak any language.<br><span class="gradient-text">Instantly.</span></h1>
        <p class="hero-subtitle">Break language barriers with AI-powered translation across 15+ languages. Text, speech, and audio — all in one seamless experience.</p>
        <div class="hero-cta"><a href="#features" class="btn-secondary">Explore features</a></div>
        <div class="hero-stats">
          <div><div class="hero-stat-value">15+</div><div class="hero-stat-label">Languages</div></div>
          <div><div class="hero-stat-value">3</div><div class="hero-stat-label">Modes</div></div>
          <div><div class="hero-stat-value">100%</div><div class="hero-stat-label">Free</div></div>
          <div><div class="hero-stat-value">24/7</div><div class="hero-stat-label">Available</div></div>
        </div>
      </div>
    </section>
    """)
    st.html("""
    <section class="section" id="features">
      <div class="section-inner">
        <div class="section-header"><span class="section-eyebrow">Features</span><h2 class="section-title">Everything you need to break barriers</h2><p class="section-subtitle">Powerful tools designed for seamless multilingual communication.</p></div>
        <div class="features-grid">
          <div class="feature-card"><div class="feature-icon">🎙️</div><h3>Speech recognition</h3><p>Convert spoken words into text instantly with browser-native AI models — no downloads.</p></div>
          <div class="feature-card"><div class="feature-icon">🔊</div><h3>Natural text-to-speech</h3><p>Listen to translations in clear, native pronunciation in the target language.</p></div>
          <div class="feature-card"><div class="feature-icon">🌍</div><h3>15+ languages</h3><p>Communicate across borders with support for major global and regional languages.</p></div>
          <div class="feature-card"><div class="feature-icon">🔒</div><h3>Privacy first</h3><p>Your translation history stays on your device. We never see your content.</p></div>
          <div class="feature-card"><div class="feature-icon">⚡</div><h3>Instant results</h3><p>Lightning-fast translations with near-zero latency across all supported languages.</p></div>
          <div class="feature-card"><div class="feature-icon">📜</div><h3>History tracking</h3><p>Review, manage, and clear your past translations from a single clean dashboard.</p></div>
        </div>
      </div>
    </section>
    """)
    st.html("""
    <section class="how-section" id="how">
      <div class="section-inner">
        <div class="section-header"><span class="section-eyebrow">How it works</span><h2 class="section-title">Get started in seconds</h2><p class="section-subtitle">Four simple steps from input to output.</p></div>
        <div class="steps-grid">
          <div class="step"><div class="step-number">01</div><h3>Choose mode</h3><p>Select Text, Speech, or Audio translation.</p></div>
          <div class="step"><div class="step-number">02</div><h3>Pick languages</h3><p>Choose your source and target languages.</p></div>
          <div class="step"><div class="step-number">03</div><h3>Provide input</h3><p>Type your text or record your voice.</p></div>
          <div class="step"><div class="step-number">04</div><h3>Get output</h3><p>Read the text or listen to the audio.</p></div>
        </div>
      </div>
    </section>
    """)
    st.html("""
    <section class="section" id="reviews">
      <div class="section-inner">
        <div class="section-header"><span class="section-eyebrow">Reviews</span><h2 class="section-title">Loved by users worldwide</h2><p class="section-subtitle">Join thousands of people communicating without borders.</p></div>
        <div class="reviews-grid">
          <div class="review-card"><div class="stars">★★★★★</div><p class="review-text">"This tool saved me during my trip to Japan. The speech-to-speech feature is incredibly fast and accurate — it felt like having a personal interpreter in my pocket."</p><div class="reviewer"><div class="reviewer-avatar">SM</div><div><div class="reviewer-name">Sarah Mitchell</div><div class="reviewer-role">Traveler</div></div></div></div>
          <div class="review-card"><div class="stars">★★★★★</div><p class="review-text">"I use EasyLingo to translate study materials. The audio output helps me practice pronunciation perfectly. A genuine game-changer for language students."</p><div class="reviewer"><div class="reviewer-avatar">DL</div><div><div class="reviewer-name">David Lawson</div><div class="reviewer-role">Student</div></div></div></div>
          <div class="review-card"><div class="stars">★★★★★</div><p class="review-text">"A highly reliable tool for quick translations. The interface is clean, and I love that it keeps a full history of everything I translate."</p><div class="reviewer"><div class="reviewer-avatar">PK</div><div><div class="reviewer-name">Priya Kapoor</div><div class="reviewer-role">Professional</div></div></div></div>
        </div>
      </div>
    </section>
    """)
    st.markdown('<div class="cta-standalone-btn">', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("Create free account →", type="primary", use_container_width=True, key="cta_signup"):
            st.session_state.show_auth = True; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.html("""
    <section class="cta-section">
      <div class="section-inner"><h2 class="cta-title">Ready to break language barriers?</h2><p class="cta-subtitle">Join thousands of users communicating seamlessly across the globe.</p></div>
    </section>
    """)

# ============================================================
# DASHBOARD FOOTER
# ============================================================
def render_dash_footer():
    st.html("""
    <footer class="dash-footer">
      <div class="dash-footer-brand"><span class="nav-logo-mark">🌐</span>EasyLingo</div>
      <div class="dash-footer-copy">© 2026 EasyLingo · All rights reserved</div>
      <div class="dash-footer-links">
        <a href="#">Help</a><span class="sep">•</span><a href="#">Privacy</a><span class="sep">•</span><a href="#">Terms</a><span class="sep">•</span><a href="#">Feedback</a>
      </div>
    </footer>
    """)

# ============================================================
# DASHBOARD
# ============================================================
# ============================================================
# DASHBOARD
# ============================================================
# ============================================================
# DASHBOARD
# ============================================================
def render_dashboard():
    # 👇 RESTORED: Dashboard background and layout styling
    st.markdown("""
    <style>
    .stApp { background: var(--bg-elevated) !important; }
    .stApp .block-container {
        padding: 1.5rem clamp(1.5rem, 2.5vw, 3rem) 3rem !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    history_df = get_history(st.session_state.user)
    total = len(history_df)
    top_lang, lang_counts, streak, this_week = "—", None, 0, 0

    if total > 0:
        top_lang = history_df["Target_Lang"].mode()[0] if not history_df["Target_Lang"].mode().empty else "—"
        lang_counts = history_df["Target_Lang"].value_counts().head(5)
        try:
            dates = pd.to_datetime(history_df["Timestamp"]).dt.date
            dates_set = set(dates)
            today = datetime.now().date()
            check = today
            while check in dates_set:
                streak += 1
                check = check - timedelta(days=1)
            if streak == 0 and (today - timedelta(days=1)) in dates_set:
                check = today - timedelta(days=1)
                while check in dates_set:
                    streak += 1
                    check = check - timedelta(days=1)
        except Exception: streak = 0
        try:
            week_ago = datetime.now() - timedelta(days=7)
            this_week = int((pd.to_datetime(history_df["Timestamp"]) >= week_ago).sum())
        except Exception: this_week = 0

    initials = (st.session_state.user or "U")[:2].upper()
    today_str = datetime.now().strftime("%A, %d %B")

    st.html(f'''
    <div class="dash-welcome">
      <div class="dash-welcome-left"><div class="dash-avatar-lg">{initials}</div><div><h1 class="dash-welcome-title">Welcome back, {html.escape(st.session_state.user)} 👋</h1><p class="dash-welcome-sub">Here's your translation activity at a glance.</p></div></div>
      <span class="dash-welcome-date">📅 {today_str}</span>
    </div>
    ''')

    streak_label = f"{streak} day{'s' if streak != 1 else ''}" if streak > 0 else "Start today"
    st.html(f"""
    <div class="dash-stats-v2">
      <div class="dash-stat-card accent-indigo"><div class="dash-stat-icon-wrap">📊</div><div class="dash-stat-info"><div class="dash-stat-label">Total translations</div><div class="dash-stat-value">{total}</div><div class="dash-stat-delta">{'+' + str(this_week) + ' this week' if this_week else 'Get started'}</div></div></div>
      <div class="dash-stat-card accent-purple"><div class="dash-stat-icon-wrap">🌍</div><div class="dash-stat-info"><div class="dash-stat-label">Top language</div><div class="dash-stat-value">{html.escape(top_lang)}</div><div class="dash-stat-delta">Most used</div></div></div>
      <div class="dash-stat-card accent-pink"><div class="dash-stat-icon-wrap">🔥</div><div class="dash-stat-info"><div class="dash-stat-label">Current streak</div><div class="dash-stat-value">{streak_label}</div><div class="dash-stat-delta">{'Keep it up!' if streak > 0 else 'Translate to start'}</div></div></div>
      <div class="dash-stat-card accent-emerald"><div class="dash-stat-icon-wrap">🗣️</div><div class="dash-stat-info"><div class="dash-stat-label">Languages available</div><div class="dash-stat-value">{len(SUPPORTED_LANGUAGES)}</div><div class="dash-stat-delta">Worldwide</div></div></div>
    </div>
    """)

    # Translator Card
    with st.container(border=True):
        mode = st.radio("Translation mode", ["Text to Text", "Text to Speech", "Speech to Speech"], horizontal=True, key="mode_select")
        c1, c2 = st.columns(2)
        with c1: source_lang = st.selectbox("From", list(SUPPORTED_LANGUAGES.keys()), index=0, key="src_lang")
        with c2: target_lang = st.selectbox("To", list(SUPPORTED_LANGUAGES.keys()), index=1, key="tgt_lang")

        col_in, col_out = st.columns(2, gap="large")
        input_text = ""

        with col_in:
            st.markdown('<div class="translator-label">Input</div>', unsafe_allow_html=True)
            if mode in ("Text to Text", "Text to Speech"):
                input_text = st.text_area(" ", height=140, placeholder="Type or paste text here…", label_visibility="collapsed", key="text_input")
            else:
                st.caption("Record your voice below")
                audio_value = st.audio_input(" ", key="mic")
                if audio_value is not None:
                    with st.spinner("Recognizing speech…"):
                        input_text = recognize_speech_from_mic(audio_value, source_lang)
                        if input_text.startswith("Error"):
                            st.error(input_text); input_text = ""
                        else:
                            st.success(f"Recognized: {input_text}")
            label = "Translate →" if mode == "Text to Text" else "Translate & speak →"
            translate_clicked = st.button(label, type="primary", use_container_width=True, key="go_translate")

        with col_out:
            st.markdown('<div class="translator-label">Output</div>', unsafe_allow_html=True)
            if translate_clicked:
                if not input_text.strip():
                    st.warning("Please provide input.")
                else:
                    with st.spinner("Translating…"):
                        translated = translate_text(input_text, source_lang, target_lang)
                        st.session_state.translated_text = translated
                        if not (translated.startswith("⚠️") or translated.startswith("Translation Error")):
                            save_translation(st.session_state.user, mode, source_lang, target_lang, input_text, translated)
                            st.session_state.toast = ("Translation saved", "✅")
                            if mode != "Text to Text":
                                st.session_state.audio_bytes = generate_audio(translated, target_lang)
                            st.rerun()
            if st.session_state.translated_text:
                st.markdown(f'<div class="output-box">{html.escape(st.session_state.translated_text)}</div>', unsafe_allow_html=True)
                if mode != "Text to Text" and st.session_state.get('audio_bytes'):
                    st.audio(st.session_state.audio_bytes, format="audio/mp3")
                if st.button("Clear", key="clear_out", use_container_width=True):
                    st.session_state.translated_text = ""
                    st.session_state.audio_bytes = None
                    st.rerun()
            else:
                st.markdown('<div class="output-box"><span class="output-box-placeholder">Translation will appear here…</span></div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1.6, 1], gap="large")

    with col_left:
        st.markdown('<div class="dash-section-heading">📋 Recent activity</div>', unsafe_allow_html=True)
        if total > 0:
            recent = history_df.tail(5).iloc[::-1]
            cards_html = ""
            for _, row in recent.iterrows():
                src = html.escape(str(row['Input_Text'])[:70])
                tgt = html.escape(str(row['Translated_Text'])[:70])
                lang_pair = html.escape(f"{row['Source_Lang']} → {row['Target_Lang']}")
                ts = html.escape(str(row['Timestamp']))
                cards_html += f'<div class="dash-activity-card"><div class="dash-activity-src">{src}</div><div class="dash-activity-arrow">{lang_pair}</div><div class="dash-activity-tgt">{tgt}</div><div class="dash-activity-meta"><span>{html.escape(str(row["Mode"]))}</span><span>{ts}</span></div></div>'
            st.html(f'<div class="dash-activity-grid">{cards_html}</div>')
        else:
            st.html('<div class="dash-empty"><div class="dash-empty-icon">📭</div><div class="dash-empty-title">No translations yet</div><p class="dash-empty-desc">Your recent activity will appear here once you start translating.</p></div>')

    with col_right:
        st.markdown('<div class="dash-section-heading">🌍 Language insights</div>', unsafe_allow_html=True)
        if lang_counts is not None and len(lang_counts) > 0:
            bars = ""
            max_count = int(lang_counts.max())
            for lang, cnt in lang_counts.items():
                pct = int(round(cnt / max_count * 100)) if max_count else 0
                bars += f'<div class="dash-lang-row"><div class="dash-lang-name">{html.escape(str(lang))}</div><div class="dash-lang-track"><div class="dash-lang-fill" style="width:{pct}%"></div></div><div class="dash-lang-count">{int(cnt)}</div></div>'
            st.html(f'<div class="dash-lang-bars">{bars}</div>')
        else:
            st.html('<div class="dash-empty"><div class="dash-empty-icon">📊</div><div class="dash-empty-title">No data yet</div><p class="dash-empty-desc">Translate a few phrases and we\'ll show your language usage here.</p></div>')

    st.markdown('<div class="dash-section-heading">💡 Pro tips</div>', unsafe_allow_html=True)
    st.html("""
    <div class="dash-tips-grid">
      <div class="dash-tip"><div class="dash-tip-icon">🎯</div><div class="dash-tip-title">Speak clearly</div><p class="dash-tip-desc">For best speech recognition results, minimize background noise and speak at a normal pace.</p></div>
      <div class="dash-tip"><div class="dash-tip-icon">💾</div><div class="dash-tip-title">Auto-saved</div><p class="dash-tip-desc">Every translation is saved to your local history — revisit them anytime from the History tab.</p></div>
      <div class="dash-tip"><div class="dash-tip-icon">🔊</div><div class="dash-tip-title">Listen & learn</div><p class="dash-tip-desc">Use the audio output to practice pronunciation in the target language.</p></div>
    </div>
    """)

    render_dash_footer()
# ============================================================
# HISTORY
# ============================================================
# ============================================================
# HISTORY
# ============================================================
# ============================================================
# HISTORY
# ============================================================
def render_history():
    # 👇 RESTORED: History background and layout styling
    st.markdown("""
    <style>
    .stApp { background: var(--bg-elevated) !important; }
    .stApp .block-container {
        padding: 2rem clamp(1.5rem, 2.5vw, 3rem) 3rem !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.html("""
    <div class="section-header">
      <span class="section-eyebrow">History</span><h2 class="section-title">Your translations</h2><p class="section-subtitle">Every translation you've made, stored locally on your device.</p>
    </div>
    """)
    
    history_df = get_history(st.session_state.user)
    
    if history_df.empty:
        st.html('<div class="dash-empty" style="padding:4rem 2rem;"><div class="dash-empty-icon">📭</div><div class="dash-empty-title">No translations yet</div><div class="dash-empty-desc">Head back to the dashboard and translate something — it\'ll appear here.</div></div>')
    else:
        display = history_df[["Timestamp", "Mode", "Source_Lang", "Target_Lang", "Input_Text", "Translated_Text"]].iloc[::-1]
        st.dataframe(display, use_container_width=True, hide_index=True)
        col_a, _, _ = st.columns([1.2, 1, 3])
        with col_a:
            if st.button("Clear all history", type="secondary", use_container_width=True):
                clear_history(st.session_state.user)
                st.session_state.toast = ("History cleared", "🗑️")
                st.rerun()
                
    render_dash_footer()
# ============================================================
# LANDING FOOTER
# ============================================================
def render_footer():
    st.html("""
    <footer class="site-footer">
      <div class="footer-grid">
        <div>
          <div class="footer-logo"><span class="nav-logo-mark">🌐</span>EasyLingo</div>
          <p class="footer-tagline">Break language barriers with AI-powered speech and text translation. Designed for travelers, students, and professionals worldwide.</p>
          <div class="footer-socials"><a href="#">𝕏</a><a href="#">⚡</a><a href="#">in</a><a href="#">✉</a></div>
        </div>
        <div class="footer-column"><h4>Product</h4><a href="#features">Features</a><a href="#how">How it works</a><a href="#reviews">Reviews</a><a href="#">Pricing</a></div>
        <div class="footer-column"><h4>Resources</h4><a href="#">Documentation</a><a href="#">API Reference</a><a href="#">Tutorials</a><a href="#">Changelog</a></div>
        <div class="footer-column"><h4>Company</h4><a href="#">About us</a><a href="#">Careers</a><a href="#">Contact</a><a href="#">Privacy</a></div>
      </div>
      <div class="footer-bottom"><div>© 2026 EasyLingo. All rights reserved.</div><div class="footer-bottom-links"><a href="#">Terms</a><a href="#">Privacy</a><a href="#">Cookies</a></div></div>
    </footer>
    """)

# ============================================================
# ROUTER
# ============================================================
if st.session_state.page == 'history':
    if st.session_state.user:
        render_history()
    else:
        st.session_state.page = 'home'; st.rerun()
elif st.session_state.page == 'home':
    if st.session_state.user:
        render_dashboard()
    else:
        render_landing()
        render_footer()

# Show the unified auth modal
if st.session_state.show_auth:
    auth_modal()