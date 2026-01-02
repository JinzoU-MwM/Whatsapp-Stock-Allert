import streamlit as st
import pandas as pd
import time
import os
import sys
import threading
from dotenv import load_dotenv

# Add stock-intelligence to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock-intelligence'))

# Import Controller Logic
from app_controller import StockAppController

# Page Config
st.set_page_config(
    page_title="Stock Intelligence AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'controller' not in st.session_state:
    st.session_state.controller = StockAppController()
    # Start Backend Service if not running (Local dev mostly, in Docker supervisor handles it)
    if not os.getenv("DOCKER_ENV"):
        st.session_state.controller.start_wa_service()

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🤖 STOCK INTELLIGENCE")
    st.markdown("---")
    
    # Navigation
    page = st.radio("Menu", ["📊 Market Data", "💼 Portfolio", "⚙️ Settings"])
    
    st.markdown("---")
    
    # System Status
    st.subheader("System Status")
    
    # WA Connection Logic
    if st.button("Check WhatsApp Status"):
        with st.spinner("Checking..."):
            qr_data = st.session_state.controller.get_qr_code()
            if qr_data:
                status = qr_data.get('status')
                if status == 'connected':
                    st.success("WhatsApp Connected ✅")
                elif status == 'scanning':
                    st.warning("Scan QR Code Below")
                    if qr_data.get('qr'):
                        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data.get('qr')}")
                else:
                    st.info(f"Status: {status}")
            else:
                st.error("Service Offline ❌")

    if st.button("Disconnect WhatsApp", type="primary"):
        if st.session_state.controller.logout_whatsapp():
            st.success("Disconnected")
            st.experimental_rerun()

# --- MAIN PAGE: MARKET DATA ---
if page == "📊 Market Data":
    st.header("🔎 Market Analysis")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        ticker = st.text_input("Enter Ticker (e.g. BBCA)", value="").upper()
    with col2:
        style = st.selectbox("Trading Style", ["SWING", "SCALPING", "INVESTING"])
    with col3:
        pass # Spacer

    if st.button("🚀 Analyze Stock", type="primary"):
        if not ticker:
            st.warning("Please enter a ticker symbol.")
        else:
            status_container = st.empty()
            progress_bar = st.progress(0)
            
            def progress_callback(p):
                progress_bar.progress(p)
                status_container.info(f"Analyzing {ticker}... {int(p*100)}%")

            try:
                # Run Analysis
                msg, chart_path, score = st.session_state.controller.run_analysis(
                    ticker, style=style, progress_callback=progress_callback
                )
                
                st.session_state.analysis_result = {
                    "msg": msg,
                    "chart": chart_path,
                    "score": score,
                    "ticker": ticker
                }
                status_container.success("Analysis Complete!")
                
            except Exception as e:
                status_container.error(f"Error: {str(e)}")

    # Display Results
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        
        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader(f"Analysis Report: {res['ticker']}")
            st.text_area("Report Output", value=res['msg'], height=500)
            
            target_phone = os.getenv("TARGET_PHONE")
            if st.button(f"📲 Send to WhatsApp ({target_phone})"):
                st.session_state.controller.send_whatsapp_message(target_phone, res['msg'], res['chart'])
                st.toast("Message Sent!", icon="✅")

        with c2:
            st.subheader("Chart")
            if res['chart'] and os.path.exists(res['chart']):
                st.image(res['chart'])
            st.metric("Confidence Score", f"{res['score']}/100")

# --- PAGE: PORTFOLIO ---
elif page == "💼 Portfolio":
    st.header("My Portfolio")
    
    # Reload logic similar to UI
    portfolio = st.session_state.controller.get_portfolio_summary()
    if portfolio:
        df = pd.DataFrame(portfolio)
        st.dataframe(df)
        
        total_val = df['market_value'].sum()
        total_pl = df['pl_value'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Value", f"IDR {total_val:,.0f}")
        c2.metric("Total P/L", f"IDR {total_pl:,.0f}", delta=f"{total_pl:,.0f}")
    else:
        st.info("Portfolio is empty.")

# --- PAGE: SETTINGS ---
elif page == "⚙️ Settings":
    st.header("Configuration")
    
    with st.form("config_form"):
        google_key = st.text_input("Google API Key", value=os.getenv("GOOGLE_API_KEY", ""), type="password")
        serper_key = st.text_input("Serper API Key", value=os.getenv("SERPER_API_KEY", ""), type="password")
        goapi_key = st.text_input("GoAPI Key", value=os.getenv("GOAPI_API_KEY", ""), type="password")
        phone = st.text_input("Target Phone (e.g. 628xxx)", value=os.getenv("TARGET_PHONE", ""))
        
        if st.form_submit_button("Save Configuration"):
            cfg = {
                "GOOGLE_API_KEY": google_key,
                "SERPER_API_KEY": serper_key,
                "GOAPI_API_KEY": goapi_key,
                "TARGET_PHONE": phone
            }
            if st.session_state.controller.save_config(cfg):
                st.success("Settings Saved!")
            else:
                st.error("Failed to save settings.")
