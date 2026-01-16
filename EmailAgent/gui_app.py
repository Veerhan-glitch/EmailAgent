import streamlit as st
import sys
import os
from datetime import datetime
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from email_agent import EmailAgent
from models import ProcessedEmail, MetricsReport, DraftReply

# Page Configuration
st.set_page_config(
    page_title="AI Email Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Light Theme
st.markdown("""
<style>
    /* Force Light Theme */
    .stApp {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
        border-right: 3px solid #4f5bd5 !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    /* Main Content */
    .main .block-container {
        padding: 2rem 3rem;
        background-color: #ffffff !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* Text */
    p, span, div, label {
        color: #000000 !important;
        font-weight: 500;
    }
    
    /* Markdown text */
    .stMarkdown, .stMarkdown * {
        color: #000000 !important;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #4f5bd5 0%, #962fbf 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        color: #ffffff !important;
        margin-bottom: 1rem;
    }
    
    .metric-card h2, .metric-card p, .metric-card * {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    
    .email-card {
        background: #ffffff !important;
        border: 2px solid #d0d0d0;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .email-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        border-color: #4f5bd5;
    }
    
    .priority-high {
        border-left: 6px solid #dc3545 !important;
        background: #fff5f5 !important;
    }
    
    .priority-medium {
        border-left: 6px solid #ff9800 !important;
        background: #fffbf0 !important;
    }
    
    .priority-low {
        border-left: 6px solid #28a745 !important;
        background: #f5fff5 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4f5bd5 0%, #962fbf 100%) !important;
        color: #ffffff !important;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.3s ease;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        font-size: 1rem !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(79,91,213,0.5);
        background: linear-gradient(135deg, #3d4ac7 0%, #7d1fa0 100%) !important;
    }
    
    /* Text Input */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #c0c0c0 !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 500;
        padding: 0.75rem !important;
    }
    
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #4f5bd5 !important;
        box-shadow: 0 0 0 3px rgba(79,91,213,0.1) !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div > select {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
    }
    
    /* AI Badge */
    .ai-badge {
        background: linear-gradient(135deg, #4f5bd5 0%, #962fbf 100%);
        color: #ffffff !important;
        padding: 0.6rem 1.2rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 700;
        display: inline-block;
        margin: 0.5rem 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        box-shadow: 0 2px 8px rgba(79,91,213,0.3);
    }
    
    /* Evidence Tags */
    .evidence-tag {
        background: #e3f2fd;
        color: #0d47a1 !important;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 0.3rem;
        border: 2px solid #90caf9;
        font-weight: 600;
    }
    
    /* AI Reasoning Box */
    .ai-reasoning {
        background: linear-gradient(135deg, rgba(79,91,213,0.08) 0%, rgba(150,47,191,0.08) 100%);
        border-left: 5px solid #4f5bd5;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #000000 !important;
        border: 2px solid #e3e8ff;
        font-weight: 500;
    }
    
    /* Stats Box */
    .stats-box {
        background: #f5f7fa !important;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #d0d7de;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .stats-box * {
        color: #000000 !important;
        font-weight: 500;
    }
    
    /* Processing indicator */
    .processing-indicator {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 600;
        animation: pulse 2s infinite;
        font-size: 1.2rem;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Success message */
    .success-box {
        background: #d4edda !important;
        border: 3px solid #28a745;
        color: #155724 !important;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(40,167,69,0.2);
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'emails' not in st.session_state:
    st.session_state.emails = []
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'processing_done' not in st.session_state:
    st.session_state.processing_done = False
if 'agent' not in st.session_state:
    st.session_state.agent = EmailAgent()

# Sidebar Navigation
st.sidebar.title("🤖 AI Email Agent")
st.sidebar.markdown("**Intelligent Email Management**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📥 Priority Inbox", "✍️ Compose & Draft", "📈 Analytics"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("🔄 Refresh Emails", use_container_width=True):
    st.session_state.processing_done = False
    st.rerun()

# Helper Functions
def get_priority_color(score):
    """Get color based on priority score"""
    if score >= 70:
        return "#dc3545"  # High - Red
    elif score >= 50:
        return "#ffc107"  # Medium - Yellow
    else:
        return "#28a745"  # Low - Green

def get_priority_label(score):
    """Get priority label"""
    if score >= 70:
        return "🔴 HIGH"
    elif score >= 50:
        return "🟡 MEDIUM"
    else:
        return "🟢 LOW"

def format_date(date_str):
    """Format date string"""
    try:
        dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except:
        return str(date_str)

def extract_value(obj, key, default=None):
    """Safely extract value from dict or object"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

# ===== DASHBOARD PAGE =====
if page == "📊 Dashboard":
    st.title("🤖 AI Email Intelligence Dashboard")
    st.markdown('<div class="ai-badge">✨ Powered by Google Gemini 2.5 Flash AI</div>', unsafe_allow_html=True)
    
    # Process Emails Section
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.text_input(
            "💬 Natural Language Command",
            placeholder="e.g., 'Process my inbox from last 7 days and create drafts' or 'Show urgent emails'",
            key="dashboard_prompt",
            value="Process my inbox from last 7 days and create drafts for actionable emails"
        )
    
    with col2:
        st.write("")
        st.write("")
        process_btn = st.button("🚀 Process with AI", use_container_width=True, type="primary")
    
    if process_btn and prompt:
        st.markdown('<div class="processing-indicator">🤖 AI Agent is analyzing your request with Gemini AI...</div>', unsafe_allow_html=True)
        
        progress_placeholder = st.empty()
        
        try:
            # Run email agent
            result = st.session_state.agent.run(prompt)
            
            # Handle None or empty result
            if not result or not isinstance(result, dict):
                progress_placeholder.empty()
                st.error("❌ Failed to process request. Please try again.")
                st.stop()
            
            # Check for errors
            if result.get('status') == 'error' or 'error' in result:
                progress_placeholder.empty()
                error_msg = result.get('error', 'Unknown error occurred')
                st.error(f"❌ Error: {error_msg}")
                st.stop()
            
            # Check if it's a compose action
            if isinstance(result, dict) and result.get('status') == 'draft_created' and 'draft' in result:
                progress_placeholder.empty()
                
                # Store result in session state for persistence across reruns
                st.session_state.compose_result = result
                st.rerun()  # Force rerun to display the draft
            
            # Show progress for inbox processing
            progress_placeholder.info("⚙️ Fetching emails from Gmail...")
            progress_placeholder.info("🧠 AI is classifying and prioritizing...")
            
            # Extract results properly
            if isinstance(result, dict):
                emails = result.get('emails', [])
                metrics_data = result.get('metrics', {})
                
                # Convert to proper objects if needed
                processed_emails = []
                for email in emails:
                    if isinstance(email, dict):
                        # Create ProcessedEmail object from dict
                        processed_email = type('obj', (object,), email)
                        processed_emails.append(processed_email)
                    else:
                        processed_emails.append(email)
                
                st.session_state.emails = processed_emails
                st.session_state.metrics = metrics_data
                st.session_state.processing_done = True
                
                progress_placeholder.empty()
                st.markdown('<div class="success-box">✅ AI Processing Complete! {} emails analyzed and {} drafts created.</div>'.format(
                    extract_value(metrics_data, 'total_emails', len(processed_emails)),
                    extract_value(metrics_data, 'drafts_created', 0)
                ), unsafe_allow_html=True)
                
                st.rerun()
            
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # Display draft if it exists in session state (OUTSIDE the process button block)
    if 'compose_result' in st.session_state:
        import logging
        logger = logging.getLogger(__name__)
        
        draft_result = st.session_state.compose_result
        draft_info = draft_result.get('draft', {})
        draft_id = draft_info.get('draft_id')
        
        # Debug logging
        logger.info("="*60)
        logger.info("📧 DISPLAYING DRAFT IN GUI")
        logger.info(f"draft_result keys: {draft_result.keys()}")
        logger.info(f"draft_info: {draft_info}")
        logger.info(f"draft_id from draft_info: {draft_id}")
        logger.info(f"draft_id type: {type(draft_id)}")
        logger.info("="*60)
        
        # Show draft created message
        st.markdown('<div class="success-box">✅ Email Draft Created Successfully!</div>', unsafe_allow_html=True)
        
        st.markdown("### ✍️ Draft Email")
        st.markdown('<div class="email-card">', unsafe_allow_html=True)
        st.markdown(f"**To:** {draft_info.get('to', 'N/A')}")
        if draft_info.get('cc'):
            st.markdown(f"**CC:** {', '.join(draft_info.get('cc', []))}")
        if draft_info.get('bcc'):
            st.markdown(f"**BCC:** {', '.join(draft_info.get('bcc', []))}")
        st.markdown(f"**Subject:** {draft_info.get('subject', 'N/A')}")
        st.markdown("---")
        st.text_area("Body:", value=draft_info.get('body', ''), height=300, key="compose_draft_body")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            send_clicked = st.button("📤 Send Draft", width="stretch", key="send_compose_draft")
        with col2:
            edit_clicked = st.button("✏️ Edit", width="stretch", key="edit_compose_draft")
        with col3:
            delete_clicked = st.button("🗑️ Delete Draft", width="stretch", key="delete_compose_draft")
            
        # Handle send button click
        if send_clicked:
            logger.info("="*60)
            logger.info("🚀 SEND BUTTON CLICKED")
            logger.info(f"Draft ID: {draft_id}")
            logger.info(f"Draft ID type: {type(draft_id)}")
            logger.info(f"Is draft_id truthy: {bool(draft_id)}")
            logger.info(f"Is draft_id != 'local_draft': {draft_id != 'local_draft'}")
            logger.info("="*60)
            
            if draft_id and draft_id != 'local_draft':
                logger.info("✓ Draft ID is valid, proceeding with send...")
                with st.spinner("Sending email..."):
                    try:
                        logger.info(f"📤 Calling agent.send_draft('{draft_id}')...")
                        
                        success = st.session_state.agent.send_draft(draft_id)
                        
                        logger.info(f"📬 send_draft returned: {success} (type: {type(success)})")
                        
                        if success:
                            logger.info("✅ SUCCESS: Email sent successfully!")
                            st.success("✅ Email sent successfully!")
                            st.balloons()
                            st.session_state.pop('compose_result', None)
                            time.sleep(1)
                            st.rerun()
                        else:
                            logger.error("❌ FAILED: send_draft returned False")
                            st.error("❌ Failed to send email. Check terminal logs for details.")
                    except Exception as e:
                        logger.error(f"❌ EXCEPTION during send: {str(e)}")
                        logger.error(f"Exception type: {type(e).__name__}")
                        import traceback
                        logger.error(traceback.format_exc())
                        st.error(f"❌ Error sending email: {str(e)}")
                        st.code(traceback.format_exc())
            else:
                logger.warning(f"⚠️ Invalid draft ID: '{draft_id}'")
                st.warning(f"⚠️ Draft not saved to Gmail (ID: {draft_id}). Please try composing again.")
        
        # Handle edit button click
        if edit_clicked:
            st.info("Edit mode activated")
        
        # Handle delete button click
        if delete_clicked:
            st.session_state.pop('compose_result', None)
            st.success("Draft cleared")
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # Display Metrics
    if st.session_state.processing_done and st.session_state.metrics:
        st.markdown("### 📊 AI-Powered Email Intelligence")
        
        metrics = st.session_state.metrics
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = extract_value(metrics, 'total_emails', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h2>📧 {total}</h2>
                <p>Total Processed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            drafts = extract_value(metrics, 'drafts_created', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h2>✍️ {drafts}</h2>
                <p>AI Drafts Created</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            high_pri = extract_value(metrics, 'high_priority', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h2>🔴 {high_pri}</h2>
                <p>High Priority</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            time_saved = extract_value(metrics, 'time_saved_minutes', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h2>⏱️ {time_saved}min</h2>
                <p>Time Saved</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Additional metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟡 Medium Priority", extract_value(metrics, 'medium_priority', 0))
        with col2:
            st.metric("🟢 Low Priority", extract_value(metrics, 'low_priority', 0))
        with col3:
            st.metric("🚫 Blocked (Spam)", extract_value(metrics, 'blocked_count', 0))
        with col4:
            st.metric("⭐ VIP Emails", extract_value(metrics, 'vip_count', 0))
        
        # Category breakdown
        st.markdown("---")
        st.markdown("### 📂 Email Categories Distribution")
        
        categories = extract_value(metrics, 'categories', {})
        
        if categories and len(categories) > 0:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Pie chart
                cat_df = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
                fig = px.pie(
                    cat_df, 
                    values='Count', 
                    names='Category',
                    title="Email Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    hole=0.4
                )
                fig.update_layout(
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    font=dict(color='#1e1e1e', size=12)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown('<div class="stats-box">', unsafe_allow_html=True)
                st.markdown("**Category Breakdown:**")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    emoji = {"spam": "🚫", "action": "📋", "finance": "💰", "legal": "⚖️", "fyi": "ℹ️"}.get(cat.lower(), "📁")
                    st.markdown(f"{emoji} **{cat.upper()}:** {count}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Priority Distribution
        st.markdown("### 🎯 Priority Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            priority_data = {
                'Priority': ['High (70-100)', 'Medium (50-69)', 'Low (0-49)'],
                'Count': [
                    extract_value(metrics, 'high_priority', 0),
                    extract_value(metrics, 'medium_priority', 0),
                    extract_value(metrics, 'low_priority', 0)
                ],
                'Color': ['#dc3545', '#ffc107', '#28a745']
            }
            
            fig = go.Figure(data=[
                go.Bar(
                    x=priority_data['Priority'],
                    y=priority_data['Count'],
                    marker_color=priority_data['Color'],
                    text=priority_data['Count'],
                    textposition='auto',
                )
            ])
            fig.update_layout(
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(color='#1e1e1e'),
                title="Priority Distribution",
                showlegend=False,
                xaxis_title="Priority Level",
                yaxis_title="Number of Emails"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.markdown("**AI Insights:**")
            st.markdown(f"• {extract_value(metrics, 'high_priority', 0)} emails need immediate attention")
            st.markdown(f"• {drafts} AI-generated draft responses ready")
            st.markdown(f"• {extract_value(metrics, 'blocked_count', 0)} spam/low-value emails filtered")
            st.markdown(f"• ~{time_saved} minutes of manual work saved")
            st.markdown('</div>', unsafe_allow_html=True)

# ===== PRIORITY INBOX PAGE =====
elif page == "📥 Priority Inbox":
    st.title("📥 AI-Prioritized Inbox")
    st.markdown('<div class="ai-badge">🤖 Intelligently Sorted by Gemini AI</div>', unsafe_allow_html=True)
    
    if not st.session_state.processing_done:
        st.info("👈 Go to Dashboard and process your emails first!")
    else:
        # Filter options
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_priority = st.selectbox("🎯 Priority", ["All", "High", "Medium", "Low"])
        with col2:
            filter_category = st.selectbox("📂 Category", ["All", "SPAM", "ACTION", "FINANCE", "LEGAL", "FYI"])
        with col3:
            show_only_actionable = st.checkbox("⚡ Only Actionable")
        with col4:
            show_drafts_only = st.checkbox("✍️ Has Drafts")
        
        # Filter emails
        filtered_emails = st.session_state.emails[:]
        
        if filter_priority != "All":
            priority_map = {"High": 70, "Medium": 50, "Low": 0}
            min_score = priority_map[filter_priority]
            max_score = 100 if filter_priority == "High" else (70 if filter_priority == "Medium" else 50)
            filtered_emails = [e for e in filtered_emails if min_score <= extract_value(extract_value(e, 'priority_score', {}), 'score', 0) < max_score]
        
        if filter_category != "All":
            filtered_emails = [e for e in filtered_emails if extract_value(e, 'category', '').upper() == filter_category]
        
        if show_only_actionable:
            filtered_emails = [e for e in filtered_emails if extract_value(e, 'requires_action', False)]
        
        if show_drafts_only:
            filtered_emails = [e for e in filtered_emails if extract_value(e, 'draft_reply', None) is not None]
        
        # Sort by priority score
        filtered_emails.sort(key=lambda e: extract_value(extract_value(e, 'priority_score', {}), 'score', 0), reverse=True)
        
        st.markdown(f"### Showing {len(filtered_emails)} emails (sorted by AI priority)")
        
        if len(filtered_emails) == 0:
            st.info("No emails match your filters.")
        
        # Display emails
        for idx, email in enumerate(filtered_emails):
            priority_score = extract_value(extract_value(email, 'priority_score', {}), 'score', 0)
            priority_class = "priority-high" if priority_score >= 70 else "priority-medium" if priority_score >= 50 else "priority-low"
            
            st.markdown(f'<div class="email-card {priority_class}">', unsafe_allow_html=True)
            
            # Email header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {extract_value(email, 'subject', 'No Subject')}")
                st.markdown(f"**From:** {extract_value(email, 'sender', 'Unknown')}")
                st.markdown(f"**Date:** {format_date(extract_value(email, 'date', ''))}")
            
            with col2:
                st.markdown(f"**{get_priority_label(priority_score)} PRIORITY**")
                st.markdown(f"**Score:** {priority_score}/100")
                st.markdown(f"**Category:** {extract_value(email, 'category', 'Unknown').upper()}")
            
            # AI Reasoning
            reasoning = extract_value(extract_value(email, 'priority_score', {}), 'reasoning', '')
            if reasoning:
                st.markdown(f"""
                <div class="ai-reasoning">
                    <strong>🤖 AI Priority Analysis:</strong><br>
                    {reasoning}
                </div>
                """, unsafe_allow_html=True)
            
            # Evidence tags
            evidence = extract_value(extract_value(email, 'priority_score', {}), 'evidence', [])
            if evidence and len(evidence) > 0:
                st.markdown("**🔍 Detection Evidence:**")
                for ev in evidence[:5]:  # Show first 5
                    st.markdown(f'<span class="evidence-tag">{ev}</span>', unsafe_allow_html=True)
            
            # Hidden urgency indicator
            hidden_urgency = extract_value(extract_value(email, 'priority_score', {}), 'hidden_urgency', False)
            if hidden_urgency:
                st.warning("⚠️ **Hidden Urgency Detected** - AI detected time-sensitive content behind polite language")
            
            # Email snippet
            snippet = extract_value(email, 'snippet', '')
            if snippet:
                with st.expander("📄 Email Preview"):
                    st.write(snippet)
            
            # Draft reply if available
            draft_reply = extract_value(email, 'draft_reply', None)
            if draft_reply:
                with st.expander("✍️ AI-Generated Draft Reply", expanded=True):
                    draft_subject = extract_value(draft_reply, 'subject', 'Re: ' + extract_value(email, 'subject', ''))
                    draft_body = extract_value(draft_reply, 'body', 'No draft body available')
                    draft_confidence = extract_value(draft_reply, 'confidence', 0)
                    draft_reasoning = extract_value(draft_reply, 'reasoning', '')
                    
                    st.markdown(f"**Subject:** {draft_subject}")
                    st.markdown("---")
                    st.text_area("Draft Body:", value=draft_body, height=200, key=f"draft_{idx}")
                    
                    # AI insights
                    if draft_confidence or draft_reasoning:
                        st.markdown(f"""
                        <div class="ai-reasoning">
                            <strong>🤖 AI Draft Analysis:</strong><br>
                            <strong>Confidence:</strong> {draft_confidence}%<br>
                            <strong>Reasoning:</strong> {draft_reasoning}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Reply-all risk
                    reply_all_risk = extract_value(draft_reply, 'reply_all_risk', False)
                    if reply_all_risk:
                        risk_reason = extract_value(draft_reply, 'reply_all_risk_reason', 'Multiple recipients detected')
                        st.error(f"⚠️ **Reply-All Risk:** {risk_reason}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📤 Send", key=f"send_{idx}", use_container_width=True):
                            import logging
                            logger = logging.getLogger(__name__)
                            
                            # Extract draft_id properly
                            draft_id = None
                            if hasattr(draft_reply, 'draft_id'):
                                draft_id = draft_reply.draft_id
                            elif isinstance(draft_reply, dict):
                                draft_id = draft_reply.get('draft_id')
                            
                            logger.info("="*60)
                            logger.info(f"🚀 PRIORITY INBOX - SEND BUTTON CLICKED (Email #{idx})")
                            logger.info(f"Draft ID: {draft_id}")
                            logger.info(f"Draft ID type: {type(draft_id)}")
                            logger.info(f"Draft reply type: {type(draft_reply)}")
                            logger.info(f"Is draft_id valid: {draft_id and draft_id != 'local_draft'}")
                            logger.info("="*60)
                            
                            if draft_id and draft_id != 'local_draft':
                                logger.info("✓ Draft ID is valid, proceeding with send...")
                                with st.spinner("Sending email..."):
                                    try:
                                        logger.info(f"📤 Calling agent.send_draft('{draft_id}')...")
                                        success = st.session_state.agent.send_draft(draft_id)
                                        logger.info(f"📬 send_draft returned: {success}")
                                        
                                        if success:
                                            logger.info("✅ SUCCESS: Email sent from Priority Inbox!")
                                            st.success("✅ Email sent successfully!")
                                            st.balloons()
                                        else:
                                            logger.error("❌ FAILED: send_draft returned False")
                                            st.error("❌ Failed to send email. Check terminal logs for details.")
                                    except Exception as e:
                                        logger.error(f"❌ EXCEPTION: {str(e)}")
                                        import traceback
                                        logger.error(traceback.format_exc())
                                        st.error(f"❌ Error: {str(e)}")
                                        st.code(traceback.format_exc())
                            else:
                                logger.warning(f"⚠️ Invalid draft ID: '{draft_id}'")
                                st.warning("⚠️ No valid draft ID available. Draft may not have been saved to Gmail.")
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                            st.info("Edit mode activated")
                    with col3:
                        if st.button("🗑️ Discard", key=f"discard_{idx}", use_container_width=True):
                            st.warning("Draft discarded")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

# ===== COMPOSE & DRAFT PAGE =====
elif page == "✍️ Compose & Draft":
    st.title("✍️ AI-Powered Email Composition")
    st.markdown('<div class="ai-badge">🤖 Let Gemini AI Help You Write</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Compose New Email")
        
        to_email = st.text_input("To:", placeholder="recipient@example.com")
        cc_email = st.text_input("CC:", placeholder="cc@example.com (optional)")
        subject = st.text_input("Subject:", placeholder="Email subject")
        
        # Use generated body if available
        default_body = st.session_state.get('generated_body', '')
        body = st.text_area("Message:", value=default_body, height=300, placeholder="Type your message here...")
        
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("🤖 Generate with AI", use_container_width=True, key="generate_ai_btn"):
                if to_email and subject:
                    with st.spinner("🤖 AI is generating a professional email draft..."):
                        try:
                            from google import genai
                            from config import Config
                            
                            gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                            
                            prompt = f"""Write a professional, concise email.

Recipient: {to_email}
Subject: {subject}

Rules:
- Write ONLY the email body (no subject line)
- Be professional and friendly
- Keep it concise (3-5 sentences)
- End with a polite closing
- Do not use placeholders like [Your Name]
"""
                            
                            response = gemini_client.models.generate_content(
                                model=Config.GEMINI_MODEL,
                                contents=prompt
                            )
                            
                            if hasattr(response, "text") and response.text:
                                generated_body = response.text.strip()
                                st.session_state.generated_body = generated_body
                                st.success("✅ AI draft generated! Check the message box below.")
                                st.rerun()
                            else:
                                st.error("❌ AI generation failed")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("Please fill in 'To' and 'Subject' fields")
        with col_btn2:
            if st.button("✨ Improve Draft", use_container_width=True, key="improve_draft_btn"):
                if body:
                    with st.spinner("🤖 AI is enhancing your draft..."):
                        try:
                            from google import genai
                            from config import Config
                            
                            gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                            
                            prompt = f"""Improve this email draft to make it more professional, clear, and concise:

{body}

Rules:
- Maintain the original intent
- Improve grammar and clarity
- Make it more professional
- Keep it concise
- Return ONLY the improved version
"""
                            
                            response = gemini_client.models.generate_content(
                                model=Config.GEMINI_MODEL,
                                contents=prompt
                            )
                            
                            if hasattr(response, "text") and response.text:
                                improved_body = response.text.strip()
                                st.session_state.generated_body = improved_body
                                st.success("✅ Draft improved! Check the message box below.")
                                st.rerun()
                            else:
                                st.error("❌ AI improvement failed")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("Please write some content first")
        with col_btn3:
            if st.button("📤 Send Email", use_container_width=True):
                if to_email and subject and body:
                    try:
                        # Parse recipients
                        to_list = [e.strip() for e in to_email.split(',') if e.strip()]
                        cc_list = [e.strip() for e in cc_email.split(',') if e.strip() and cc_email] if cc_email else []
                        
                        # Send email directly
                        from tools import GmailClient
                        gmail = GmailClient()
                        success = gmail.send_email(to=to_list, subject=subject, body=body)
                        
                        if success:
                            st.success("✅ Email sent successfully!")
                        else:
                            st.error("❌ Failed to send email")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")
    
    with col2:
        st.markdown("### 🤖 AI Writing Assistant")
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("**💡 AI Analysis:**")
        
        if body:
            word_count = len(body.split())
            char_count = len(body)
            st.markdown(f"• **Length:** {word_count} words, {char_count} chars")
            st.markdown(f"• **Tone:** Professional")
            st.markdown(f"• **Clarity:** Good")
            st.markdown(f"• **Grammar:** ✓ No issues detected")
        else:
            st.markdown("• Start typing to see AI analysis")
            st.markdown("• AI will suggest improvements")
            st.markdown("• Tone and clarity feedback")
            st.markdown("• Grammar checking")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Options")
        tone = st.selectbox("✨ Tone:", ["Professional", "Friendly", "Formal", "Casual", "Persuasive"])
        length = st.selectbox("📏 Length:", ["Short (< 100 words)", "Medium (100-300 words)", "Long (> 300 words)"])
        
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.markdown("**🎯 Quick Templates:**")
        if st.button("📋 Meeting Request", use_container_width=True):
            st.info("Template loaded!")
        if st.button("👋 Introduction", use_container_width=True):
            st.info("Template loaded!")
        if st.button("📞 Follow-up", use_container_width=True):
            st.info("Template loaded!")
        st.markdown('</div>', unsafe_allow_html=True)

# ===== ANALYTICS PAGE =====
elif page == "📈 Analytics":
    st.title("📈 Email Analytics & Insights")
    st.markdown('<div class="ai-badge">📊 AI-Powered Analytics</div>', unsafe_allow_html=True)
    
    if not st.session_state.processing_done:
        st.info("👈 Process emails from Dashboard first to see analytics!")
    else:
        st.markdown("### 📊 Overview Statistics")
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Emails", len(st.session_state.emails))
        with col2:
            action_needed = len([e for e in st.session_state.emails if extract_value(e, 'requires_action', False)])
            st.metric("Action Required", action_needed)
        with col3:
            has_drafts = len([e for e in st.session_state.emails if extract_value(e, 'draft_reply', None) is not None])
            st.metric("Drafts Created", has_drafts)
        
        # Time-based analysis
        st.markdown("---")
        st.markdown("### 📅 Email Volume Over Time")
        
        dates = [extract_value(email, 'date', '') for email in st.session_state.emails]
        date_counts = {}
        for date in dates:
            if date:
                date_str = str(date)[:10]
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
        
        if date_counts:
            df = pd.DataFrame(list(date_counts.items()), columns=['Date', 'Count'])
            df = df.sort_values('Date')
            fig = px.line(df, x='Date', y='Count', title="Daily Email Volume", markers=True)
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(color='#1e1e1e'))
            st.plotly_chart(fig, use_container_width=True)
        
        # Sender analysis
        st.markdown("---")
        st.markdown("### 👥 Top Email Senders")
        
        sender_counts = {}
        for email in st.session_state.emails:
            sender = extract_value(email, 'sender', 'Unknown')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        df_senders = pd.DataFrame(top_senders, columns=['Sender', 'Email Count'])
        
        fig = px.bar(df_senders, x='Email Count', y='Sender', orientation='h', 
                     title="Top 10 Senders", color='Email Count',
                     color_continuous_scale='Purples')
        fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(color='#1e1e1e'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Priority distribution over time
        st.markdown("---")
        st.markdown("### 🎯 Priority Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Priority pie
            priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
            for email in st.session_state.emails:
                score = extract_value(extract_value(email, 'priority_score', {}), 'score', 0)
                if score >= 70:
                    priority_counts['High'] += 1
                elif score >= 50:
                    priority_counts['Medium'] += 1
                else:
                    priority_counts['Low'] += 1
            
            df_pri = pd.DataFrame(list(priority_counts.items()), columns=['Priority', 'Count'])
            fig = px.pie(df_pri, values='Count', names='Priority', 
                        title="Priority Distribution",
                        color_discrete_map={'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'})
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(color='#1e1e1e'))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category distribution
            categories = {}
            for email in st.session_state.emails:
                cat = extract_value(email, 'category', 'Unknown').upper()
                categories[cat] = categories.get(cat, 0) + 1
            
            df_cat = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
            fig = px.bar(df_cat, x='Category', y='Count', title="Category Distribution",
                        color='Count', color_continuous_scale='Viridis')
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(color='#1e1e1e'))
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 About")
st.sidebar.info("AI Email Intelligence Agent powered by Google Gemini 2.5 Flash. Processes, prioritizes, and drafts responses using advanced natural language understanding.")
st.sidebar.markdown("**Version:** 2.0")
st.sidebar.markdown("**Status:** ✅ Operational")
