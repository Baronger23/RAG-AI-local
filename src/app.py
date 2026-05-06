import streamlit as st
import sys
import os
import json
import time
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(__file__))

from agent import agent
from sync_kb import sync_kb
from config import MODE, BEDROCK_KB_ID, BEDROCK_MODEL_ID, S3_BUCKET, S3_KB_PREFIX, AWS_REGION
import boto3

# Page Configuration
st.set_page_config(
    page_title="GeekBrain AI Observability Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .status-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3e4150;
        margin-bottom: 10px;
    }
    .reasoning-step {
        background-color: #262730;
        padding: 15px;
        border-left: 5px solid #ff4b4b;
        border-radius: 5px;
        margin: 10px 0;
        font-family: 'Courier New', Courier, monospace;
    }
    .tool-call {
        color: #00ffcc;
        font-weight: bold;
    }
    .source-tag {
        display: inline-block;
        padding: 2px 8px;
        background-color: #3e4150;
        border-radius: 10px;
        font-size: 0.8rem;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/brain.png", width=100)
    st.title("Settings & Status")
    
    st.info(f"**Mode:** {MODE.upper()}")
    st.info(f"**Model:** `{BEDROCK_MODEL_ID.split('/')[-1]}`")
    st.info(f"**KB ID:** `{BEDROCK_KB_ID}`")
    
    st.divider()
    
    st.subheader("📁 Upload New Knowledge")
    uploaded_file = st.file_uploader("Drag and drop PDF/MD files here", type=["pdf", "md", "txt"])
    
    if uploaded_file is not None:
        if st.button("🚀 Upload & Sync", use_container_width=True):
            try:
                s3 = boto3.client('s3', region_name=AWS_REGION)
                s3_path = f"{S3_KB_PREFIX}{uploaded_file.name}"
                
                with st.spinner(f"Uploading {uploaded_file.name} to S3..."):
                    s3.upload_fileobj(uploaded_file, S3_BUCKET, s3_path)
                    st.success(f"Uploaded to s3://{S3_BUCKET}/{s3_path}")
                
                with st.spinner("Starting Knowledge Base Sync..."):
                    success = sync_kb()
                    if success:
                        st.success("Knowledge Base is now up to date!")
                    else:
                        st.error("Sync failed, but file is on S3.")
            except Exception as e:
                st.error(f"Upload Error: {e}")

    st.divider()
    
    if st.button("🔄 Force Manual Sync", use_container_width=True):
        with st.spinner("Synchronizing with S3..."):
            success = sync_kb()
            if success:
                st.success("KB Synced Successfully!")
            else:
                st.error("Sync Failed. Check logs.")
                
    if st.button("🧹 Clear Conversation", use_container_width=True):
        agent.memory.clear()
        st.session_state.messages = []
        st.rerun()

# Main UI
st.title("🧠 GeekBrain AI: Observability Dashboard")
st.caption("Real-time pipeline monitoring for RAG & Agent Reasoning")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display Observability Data in Expander
        if message["role"] == "assistant" and "obs_data" in message:
            with st.expander("🔍 See Reasoning Pipeline"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📚 Retrieved Context")
                    if message["obs_data"].get("sources"):
                        for src in message["obs_data"]["sources"]:
                            st.markdown(f"• `{src}`")
                    else:
                        st.write("No KB chunks retrieved.")
                
                with col2:
                    st.subheader("🛠️ Tools Called")
                    if message["obs_data"].get("tools"):
                        for tool in message["obs_data"]["tools"]:
                            st.markdown(f"✅ `{tool}`")
                    else:
                        st.write("No tools called.")
                
                st.subheader("🤖 Internal Reasoning Process")
                # Showing the conversation turns from memory
                for msg in message["obs_data"].get("history", []):
                    role = msg["role"]
                    content = msg["content"][0].get("text", "") if isinstance(msg["content"], list) else str(msg["content"])
                    
                    if "toolUse" in str(msg):
                        st.markdown(f"**LLM DECISION:** *Called tools*")
                    elif "toolResult" in str(msg):
                        st.markdown(f"**SYSTEM RESPONSE:** *Tool data received*")
                    else:
                        st.markdown(f"**{role.upper()}**: {content[:200]}...")

# Chat Input
if prompt := st.chat_input("Ask about costs, incidents, or team info..."):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant message
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 *Reasoning and gathering data...*")
        
        # Process query
        start_time = time.time()
        result = agent.process_query(prompt)
        duration = time.time() - start_time
        
        # Extract observability data
        obs_data = {
            "sources": result.get("sources", []),
            "tools": result.get("tools_called", []),
            "duration": duration,
            "history": result.get("messages", []) # Full Converse history
        }
        
        # Update placeholder
        message_placeholder.markdown(result["answer"])
        
        # Save to session state
        st.session_state.messages.append({
            "role": "assistant", 
            "content": result["answer"],
            "obs_data": obs_data
        })
        
        # Show mini metrics
        st.caption(f"Processed in {duration:.2f}s | Level: {result.get('level', 'L3/L4')}")
        st.rerun()
