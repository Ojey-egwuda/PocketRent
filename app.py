"""
PocketRent - UK Rent Price Explorer
Ask questions about UK rent prices in natural language
"""
import streamlit as st
from rent_data import get_database
from query_handler import process_query

# Page config
st.set_page_config(
    page_title="PocketRent",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for cleaner look
st.markdown("""
<style>
    /* Clean header */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0;
    }
    .tagline {
        opacity: 0.7;
        font-size: 1.1rem;
        margin-top: 0;
    }
    
    /* Chat styling */
    .stChatMessage {
        background: transparent !important;
    }
    
    /* Quick action buttons - theme aware */
    .stButton > button {
        border-radius: 1rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #4CAF50;
    }
    
    /* Footer styling */
    .footer-container {
        text-align: center;
        padding: 20px 0;
        opacity: 0.9;
    }
    .footer-container a {
        color: #4CAF50;
    }
    .footer-container small {
        opacity: 0.6;
    }
</style>
""", unsafe_allow_html=True)

# Load database
db = get_database()

# Header
st.markdown("""
<div class="main-header">
    <h1>🏠 PocketRent</h1>
    <p class="tagline">Your pocket guide to UK rent prices</p>
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """**Hey! 👋 What would you like to know about UK rent?**

Try asking:
- *"Compare Manchester vs Liverpool"*
- *"Cheapest 2-bed in North West"*
- *"Areas under £700/month"*"""
        }
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about UK rent prices..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display response
    with st.chat_message("assistant"):
        response = process_query(prompt)
        st.markdown(response)
    
    # Add to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Quick actions
if len(st.session_state.messages) <= 2:
    st.markdown("#### 💡 Popular questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏆 Cheapest in UK", use_container_width=True):
            q = "Cheapest 1-bed rent in UK"
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.messages.append({"role": "assistant", "content": process_query(q)})
            st.rerun()
        
        if st.button("🏙️ London vs Manchester", use_container_width=True):
            q = "Compare London vs Manchester on 1-bed rent"
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.messages.append({"role": "assistant", "content": process_query(q)})
            st.rerun()
    
    with col2:
        if st.button("💰 Under £600/month", use_container_width=True):
            q = "Areas under £600 rent"
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.messages.append({"role": "assistant", "content": process_query(q)})
            st.rerun()
        
        if st.button("💎 Most expensive", use_container_width=True):
            q = "Most expensive areas in UK"
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.messages.append({"role": "assistant", "content": process_query(q)})
            st.rerun()

# Show clear button when chat has history
if len(st.session_state.messages) > 1:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Clear searches", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("## 🏠 PocketRent")
    st.caption("Your pocket guide to UK rent prices")
    
    st.markdown("---")
    
    st.markdown("### How to use")
    st.markdown("""
    Just type a question like:
    
    **Compare areas:**
    > Manchester vs Liverpool vs Leeds
    
    **Find cheapest:**
    > Cheapest 2-bed in Yorkshire
    
    **Search by budget:**
    > Areas under £800/month
    
    **Get area info:**
    > Rent in Bristol
    """)
    
    st.markdown("---")
    
    st.markdown("### 🗺️ Regions")
    regions = "London • North West • North East • Yorkshire • West Midlands • East Midlands • South West • South East • East of England • Wales • Scotland"
    st.caption(regions)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear searches", key="sidebar_clear", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()
    
    st.markdown("---")
    
    st.caption(f"""
    **Data:** ONS Private Rental Market Statistics
    
    **Period:** {db.period}
    
    **Coverage:** {len(db.data)} UK areas
    """)

# Footer with contact
st.markdown("""
<div class='footer-container'>
    <h4>🤖 Contact the Developer</h4>
    <p>Connect with <strong>Ojonugwa Egwuda</strong> on 
        <a href="https://www.linkedin.com/in/egwudaojonugwa/" target="_blank">LinkedIn</a>
    </p>
    <small>© 2026 PocketRent | Built with ❤️ using Streamlit & Claude</small>
</div>
""", unsafe_allow_html=True)