"""
ContentOrbit Enterprise - Landing Page
Streamlit-based professional landing page
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="ContentOrbit Enterprise",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional business/tech design
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global styles */
    .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Hero section */
    .hero {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        border-radius: 24px;
        margin-bottom: 3rem;
        color: white;
    }
    
    .hero-emoji {
        font-size: 5rem;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .hero h1 {
        font-size: 3rem;
        font-weight: 800;
        margin: 1rem 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .hero-tagline {
        font-size: 1.5rem;
        opacity: 0.95;
        margin-bottom: 2rem;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: rgba(16, 185, 129, 0.2);
        border: 2px solid #10b981;
        border-radius: 999px;
        color: white;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .status-dot {
        width: 12px;
        height: 12px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%);
        padding: 2rem;
        border-radius: 16px;
        border: 2px solid #e5e7eb;
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border-color: #6366f1;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        color: #6366f1;
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #6b7280;
        font-size: 0.95rem;
    }
    
    /* Stats section */
    .stats-container {
        background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        margin: 3rem 0;
    }
    
    .stat-box {
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* CTA section */
    .cta-section {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #6366f110 0%, #ec489910 100%);
        border-radius: 16px;
        margin: 3rem 0;
    }
    
    /* Tech badges */
    .tech-stack {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 2rem;
    }
    
    .tech-badge {
        padding: 0.5rem 1rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        font-size: 0.85rem;
        color: #6b7280;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero">
    <div class="hero-emoji">🚀</div>
    <h1>ContentOrbit Enterprise</h1>
    <p class="hero-tagline">نظام النشر الذكي المتعدد المنصات</p>
    <div class="status-badge">
        <span class="status-dot"></span>
        النظام يعمل بكفاءة عالية
    </div>
</div>
""", unsafe_allow_html=True)

# Features Section
st.markdown("## 🎯 المميزات الرئيسية")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <div class="feature-title">نشر تلقائي ذكي</div>
        <div class="feature-desc">توليد محتوى باستخدام AI ونشره تلقائياً على Telegram، Blogger، Dev.to، وFacebook</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Dashboard متقدم</div>
        <div class="feature-desc">لوحة تحكم شاملة لإدارة المحتوى، متابعة الإحصائيات، والتحكم الكامل</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎨</div>
        <div class="feature-title">توليد صور احترافي</div>
        <div class="feature-desc">إنشاء صور جذابة تلقائياً مع دعم كامل للعربية RTL واستضافة فورية</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">استراتيجية CTA</div>
        <div class="feature-desc">نظام Hub & Spoke للتسويق الذكي وتوجيه الزوار بين المنصات</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">💬</div>
        <div class="feature-title">Chatbot تفاعلي</div>
        <div class="feature-desc">بوت تيليجرام ذكي للرد على الأسئلة وإدارة الجروبات مع نظام حصص يومية</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🛡️</div>
        <div class="feature-title">آمن ومستقر</div>
        <div class="feature-desc">معمارية enterprise-grade مع حماية البيانات وإدارة متقدمة للأخطاء</div>
    </div>
    """, unsafe_allow_html=True)

# Stats Section
st.markdown("""
<div class="stats-container">
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem;">
        <div class="stat-box">
            <div class="stat-number">4+</div>
            <div class="stat-label">منصات نشر</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">24/7</div>
            <div class="stat-label">تشغيل مستمر</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">100%</div>
            <div class="stat-label">آلي بالكامل</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">∞</div>
            <div class="stat-label">قابل للتوسع</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# CTA Section
st.markdown("""
<div class="cta-section">
    <h2 style="margin-bottom: 1.5rem; color: #1f2937;">جاهز للبدء؟</h2>
</div>
""", unsafe_allow_html=True)

col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])

with col_cta2:
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🎯 افتح Dashboard", use_container_width=True):
            st.markdown('<meta http-equiv="refresh" content="0; url=https://robovai-contentorbit.streamlit.app">', unsafe_allow_html=True)
    
    with col_btn2:
        if st.button("💬 جرّب الـ Bot", use_container_width=True):
            st.markdown('<meta http-equiv="refresh" content="0; url=https://t.me/robovai_hub_bot">', unsafe_allow_html=True)

# Tech Stack
st.markdown("""
<div class="tech-stack">
    <span class="tech-badge">Python</span>
    <span class="tech-badge">Streamlit</span>
    <span class="tech-badge">Aiogram</span>
    <span class="tech-badge">Groq AI</span>
    <span class="tech-badge">Render</span>
    <span class="tech-badge">SQLite</span>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p><strong>ContentOrbit Enterprise</strong> - Powered by RoboVAI Solutions</p>
    <p style="margin-top: 0.5rem; font-size: 0.85rem;">Built with ❤️ using cutting-edge AI technology</p>
</div>
""", unsafe_allow_html=True)
