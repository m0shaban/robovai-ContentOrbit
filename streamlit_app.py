"""
ContentOrbit Enterprise - Streamlit Community Dashboard
========================================================
Lightweight landing dashboard for Streamlit Community Cloud
"""

import streamlit as st
import os

# Page configuration
st.set_page_config(
    page_title="ContentOrbit Enterprise",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Get password from secrets or environment
def get_secret(key: str, default: str = ""):
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except:
        return os.environ.get(key, default)

DASHBOARD_PASSWORD = get_secret("DASHBOARD_PASSWORD", "admin123")

# Simple authentication
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if st.session_state["authenticated"]:
        return True
    
    # Login form
    st.markdown("""
    <div style="max-width: 400px; margin: 50px auto; text-align: center;">
        <h1 style="color: #6366f1;">🚀 ContentOrbit</h1>
        <p style="color: #718096;">Enterprise Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("🔐 Password", type="password", key="pwd_input")
        if st.button("Login", use_container_width=True):
            if password == DASHBOARD_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
    return False

if not check_password():
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #e2e8f0 !important;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    .feature-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 1rem;
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .feature-title {
        color: #a5b4fc !important;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #94a3b8 !important;
        font-size: 0.9rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        border-radius: 999px;
        color: #10b981 !important;
        font-weight: 600;
    }
    .cta-button {
        display: inline-block;
        padding: 1rem 2rem;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 12px;
        font-weight: 600;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HERO SECTION
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align: center; padding: 3rem 0;">
    <div style="font-size: 5rem; margin-bottom: 1rem;">🚀</div>
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">ContentOrbit Enterprise</h1>
    <p style="font-size: 1.3rem; color: #a5b4fc;">نظام النشر الذكي المتعدد المنصات</p>
    <div class="status-badge" style="margin-top: 1.5rem;">✅ النظام يعمل بكفاءة</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🎯 المميزات الرئيسية")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <div class="feature-title">نشر تلقائي ذكي</div>
        <div class="feature-desc">توليد محتوى باستخدام AI ونشره على Telegram، Blogger، Dev.to، وFacebook</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Dashboard متقدم</div>
        <div class="feature-desc">لوحة تحكم شاملة لإدارة المحتوى والإحصائيات</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎨</div>
        <div class="feature-title">توليد صور احترافي</div>
        <div class="feature-desc">إنشاء صور جذابة مع دعم كامل للعربية RTL</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">استراتيجية CTA</div>
        <div class="feature-desc">نظام Hub & Spoke للتسويق الذكي</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">💬</div>
        <div class="feature-title">Chatbot تفاعلي</div>
        <div class="feature-desc">بوت تيليجرام ذكي للرد على الأسئلة</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🛡️</div>
        <div class="feature-title">آمن ومستقر</div>
        <div class="feature-desc">معمارية enterprise-grade مع حماية البيانات</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="font-size: 2.5rem; font-weight: 800; color: #6366f1;">4+</div>
        <div style="color: #94a3b8;">منصات نشر</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="font-size: 2.5rem; font-weight: 800; color: #ec4899;">24/7</div>
        <div style="color: #94a3b8;">تشغيل مستمر</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="font-size: 2.5rem; font-weight: 800; color: #10b981;">100%</div>
        <div style="color: #94a3b8;">آلي بالكامل</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="font-size: 2.5rem; font-weight: 800; color: #f59e0b;">∞</div>
        <div style="color: #94a3b8;">قابل للتوسع</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CTA SECTION
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.markdown("""
<div style="text-align: center; padding: 2rem; background: rgba(99, 102, 241, 0.1); border-radius: 16px; margin: 2rem 0;">
    <h2 style="margin-bottom: 1.5rem;">جاهز للبدء؟</h2>
    <a href="https://t.me/robovai_hub_bot" target="_blank" class="cta-button">💬 جرّب البوت</a>
    <a href="https://robovai-contentorbit.onrender.com/health" target="_blank" class="cta-button">🔧 حالة السيرفر</a>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TECH STACK
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <span style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 0.25rem; display: inline-block;">Python</span>
    <span style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 0.25rem; display: inline-block;">Streamlit</span>
    <span style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 0.25rem; display: inline-block;">Aiogram</span>
    <span style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 0.25rem; display: inline-block;">Groq AI</span>
    <span style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 0.25rem; display: inline-block;">Render</span>
    <span style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 0.25rem; display: inline-block;">SQLite</span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem 0;">
    <p><strong>ContentOrbit Enterprise</strong> - Powered by RoboVAI Solutions</p>
    <p style="font-size: 0.85rem;">Built with ❤️ using cutting-edge AI technology</p>
</div>
""", unsafe_allow_html=True)

# Logout button
if st.button("🚪 Logout"):
    st.session_state["authenticated"] = False
    st.rerun()
