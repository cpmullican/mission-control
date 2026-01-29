#!/usr/bin/env python3
"""
Alfred Mission Control Dashboard
Real-time visibility into agent operations
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import streamlit as st

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Alfred Mission Control",
    page_icon="🎩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Configuration
WORKSPACE_PATH = os.environ.get("WORKSPACE_PATH", "")
DATA_SUBDIR = "memory/dashboard"
LOCAL_DATA_PATH = Path(__file__).parent / "data"
REFRESH_INTERVAL = 30  # seconds


def get_data_path(filename: str) -> Optional[Path]:
    """Get path to data file, checking workspace first then local."""
    if WORKSPACE_PATH:
        workspace_file = Path(WORKSPACE_PATH) / DATA_SUBDIR / filename
        if workspace_file.exists():
            return workspace_file
    
    local_file = LOCAL_DATA_PATH / filename
    if local_file.exists():
        return local_file
    
    return None


def load_json_file(filename: str) -> Optional[dict]:
    """Load JSON file, return None if not found."""
    try:
        full_path = get_data_path(filename)
        if full_path and full_path.exists():
            with open(full_path) as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
    return None


def load_jsonl_file(filename: str, limit: int = 100) -> list:
    """Load JSONL file, return last N entries."""
    try:
        full_path = get_data_path(filename)
        if full_path and full_path.exists():
            with open(full_path) as f:
                lines = f.readlines()
                recent = lines[-limit:] if len(lines) > limit else lines
                return [json.loads(line) for line in recent if line.strip()]
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
    return []


def get_agent_status() -> dict:
    """Get current agent status."""
    status_file = load_json_file("status.json")
    if status_file:
        return status_file
    return {
        "online": True,
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "active_sessions": 0,
        "running_subagents": 0,
    }


def get_sessions() -> list:
    """Get session list."""
    sessions_file = load_json_file("sessions.json")
    if sessions_file:
        return sessions_file.get("sessions", [])
    return []


def get_session_history(session_key: str) -> list:
    """Get message history for a session."""
    history_file = load_json_file(f"history_{session_key}.json")
    if history_file:
        return history_file.get("messages", [])
    return []


def get_subagent_tasks() -> list:
    """Get sub-agent task log."""
    return load_jsonl_file("subagent-log.jsonl", limit=50)


def get_activity_feed() -> list:
    """Get activity event feed."""
    return load_jsonl_file("activity-feed.jsonl", limit=100)


def format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp for display."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%I:%M %p").lstrip("0")
    except:
        return iso_str


def format_time_ago(iso_str: str) -> str:
    """Format as 'X min ago'."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() / 60)
            return f"{mins} min ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days}d ago"
    except:
        return iso_str


# =============================================================================
# UI Components
# =============================================================================

def render_status_indicator(online: bool, last_activity: str):
    """Render online/offline status."""
    if online:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #22c55e; font-size: 24px;">●</span>
                <span style="color: #22c55e; font-weight: 600;">Online</span>
                <span style="color: #6b7280; font-size: 14px;">• {format_time_ago(last_activity)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #ef4444; font-size: 24px;">●</span>
                <span style="color: #ef4444; font-weight: 600;">Offline</span>
                <span style="color: #6b7280; font-size: 14px;">• last seen {format_time_ago(last_activity)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_card(label: str, value: str, subtitle: str = ""):
    """Render a metric card."""
    subtitle_html = f'<div style="color: #6b7280; font-size: 12px;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; text-align: center;">
            <div style="color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
            <div style="color: #ffffff; font-size: 32px; font-weight: 700; margin: 4px 0;">{value}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_session_card(session: dict, show_button: bool = True):
    """Render a session card."""
    status_colors = {"active": "#22c55e", "idle": "#eab308", "closed": "#6b7280"}
    status = session.get("status", "active")
    color = status_colors.get(status, "#6b7280")
    kind = session.get("kind", "main")
    key = session.get("key", "unknown")
    last_msg = session.get("last_message_preview", "")[:80]
    timestamp = format_timestamp(session.get("last_activity", ""))
    kind_emoji = {"main": "💬", "subagent": "🤖", "cron": "⏰"}.get(kind, "📋")
    
    st.markdown(
        f"""
        <div style="background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: {color}; font-size: 16px;">●</span>
                    <span style="color: #ffffff; font-weight: 600;">{kind_emoji} {key}</span>
                </div>
                <span style="color: #6b7280; font-size: 14px;">{timestamp}</span>
            </div>
            <div style="color: #9ca3af; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {last_msg if last_msg else "<em>No messages</em>"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if show_button:
        if st.button(f"View History →", key=f"btn_{key}"):
            st.session_state.selected_session = key
            st.session_state.page = "session_detail"
            st.rerun()


def render_activity_item(event: dict):
    """Render an activity feed item."""
    type_config = {
        "session_started": ("💬", "#22c55e"),
        "session_ended": ("⏹️", "#6b7280"),
        "task_started": ("◐", "#eab308"),
        "task_completed": ("✓", "#22c55e"),
        "task_failed": ("✗", "#ef4444"),
        "deliverable_created": ("📄", "#3b82f6"),
        "cron_executed": ("⏰", "#8b5cf6"),
        "error_occurred": ("⚠️", "#ef4444"),
    }
    
    event_type = event.get("type", "unknown")
    icon, color = type_config.get(event_type, ("•", "#6b7280"))
    summary = event.get("summary", "Unknown event")
    timestamp = format_timestamp(event.get("timestamp", ""))
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; border-bottom: 1px solid #1f2937;">
            <span style="color: {color}; font-size: 16px; width: 24px;">{icon}</span>
            <div style="flex: 1;">
                <div style="color: #e5e7eb; font-size: 14px;">{summary}</div>
                <div style="color: #6b7280; font-size: 12px;">{timestamp}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message(msg: dict):
    """Render a chat message."""
    role = msg.get("role", "unknown")
    content = msg.get("content", "")
    timestamp = format_timestamp(msg.get("timestamp", ""))
    
    if role == "user":
        bg_color = "#1e3a5f"
        label = "👤 User"
    elif role == "assistant":
        bg_color = "#1f2937"
        label = "🎩 Alfred"
    else:
        bg_color = "#374151"
        label = role.title()
    
    # Truncate very long messages
    display_content = content[:2000] + "..." if len(content) > 2000 else content
    
    st.markdown(
        f"""
        <div style="background: {bg_color}; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: #9ca3af; font-size: 12px; font-weight: 600;">{label}</span>
                <span style="color: #6b7280; font-size: 12px;">{timestamp}</span>
            </div>
            <div style="color: #e5e7eb; font-size: 14px; white-space: pre-wrap; word-wrap: break-word;">{display_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Pages
# =============================================================================

def page_home():
    """Home/Overview page."""
    st.markdown("# 🎩 Alfred Mission Control")
    
    status = get_agent_status()
    sessions = get_sessions()
    activity = get_activity_feed()
    
    render_status_indicator(
        status.get("online", False),
        status.get("last_activity", datetime.now(timezone.utc).isoformat())
    )
    
    st.markdown("---")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        active_count = len([s for s in sessions if s.get("status") == "active"])
        render_metric_card("Sessions", str(active_count), "active")
    
    with col2:
        subagent_count = status.get("running_subagents", 0)
        render_metric_card("Sub-Agents", str(subagent_count), "running")
    
    with col3:
        next_task = status.get("next_scheduled_task", {})
        next_name = next_task.get("name", "—")
        render_metric_card("Next Task", next_name[:12], "scheduled")
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### Recent Activity")
    
    if activity:
        for event in reversed(activity[-10:]):
            render_activity_item(event)
        
        if len(activity) > 10:
            st.markdown(f"*... and {len(activity) - 10} more events*")
    else:
        st.info("No recent activity recorded. Activity will appear here as Alfred works.")
    
    # Footer with refresh info
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f'<div style="color: #6b7280; font-size: 12px;">Last updated: {datetime.now().strftime("%I:%M:%S %p")}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()


def page_sessions():
    """Sessions list page."""
    st.markdown("# Sessions")
    
    sessions = get_sessions()
    
    # Filter
    filter_option = st.selectbox(
        "Filter by type",
        ["All", "Main", "Sub-Agent", "Cron"],
    )
    
    if filter_option != "All":
        kind_map = {"Main": "main", "Sub-Agent": "subagent", "Cron": "cron"}
        sessions = [s for s in sessions if s.get("kind") == kind_map.get(filter_option)]
    
    st.markdown(f"**{len(sessions)} sessions**")
    st.markdown("---")
    
    if sessions:
        for session in sessions:
            render_session_card(session)
    else:
        st.info("No sessions found.")


def page_session_detail():
    """Session detail page."""
    session_key = st.session_state.get("selected_session", "")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state.page = "sessions"
            st.rerun()
    
    st.markdown(f"# Session: `{session_key}`")
    
    # Get session info
    sessions = get_sessions()
    session = next((s for s in sessions if s.get("key") == session_key), None)
    
    if session:
        status = session.get("status", "unknown")
        kind = session.get("kind", "unknown")
        source = session.get("metadata", {}).get("source", "unknown")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Status", status.title())
        col2.metric("Type", kind.title())
        col3.metric("Source", source.title())
        
        st.markdown("---")
    
    # Get message history
    messages = get_session_history(session_key)
    
    st.markdown(f"### Message History ({len(messages)} messages)")
    
    if messages:
        for msg in messages:
            render_message(msg)
    else:
        st.info(
            "No message history available for this session.\n\n"
            "History is populated when Alfred syncs dashboard data."
        )


def page_subagents():
    """Sub-agents page."""
    st.markdown("# Sub-Agents")
    
    tasks = get_subagent_tasks()
    
    # Separate running vs completed
    spawned_keys = {t.get("session_key") for t in tasks if t.get("event") == "spawned"}
    completed_keys = {t.get("session_key") for t in tasks if t.get("event") == "completed"}
    running_keys = spawned_keys - completed_keys
    
    running = [t for t in tasks if t.get("event") == "spawned" and t.get("session_key") in running_keys]
    completed = [t for t in tasks if t.get("event") == "completed"]
    
    st.markdown(f"### 🔄 Running ({len(running)})")
    
    if running:
        for task in running:
            st.markdown(
                f"""
                <div style="background: #111827; border: 1px solid #eab308; border-radius: 12px; padding: 16px; margin-bottom: 8px;">
                    <div style="color: #eab308; font-weight: 600;">⏳ {task.get('task', 'Unknown task')}</div>
                    <div style="color: #6b7280; font-size: 14px; margin-top: 4px;">
                        Session: {task.get('session_key', 'unknown')} • Started: {format_time_ago(task.get('timestamp', ''))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown("*No sub-agents currently running*")
    
    st.markdown(f"### ✓ Recently Completed ({len(completed)})")
    
    if completed:
        for task in reversed(completed[-10:]):
            status = task.get("status", "unknown")
            status_color = "#22c55e" if status == "success" else "#ef4444"
            status_icon = "✓" if status == "success" else "✗"
            summary = task.get("summary", "")[:100]
            
            st.markdown(
                f"""
                <div style="background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #e5e7eb; font-weight: 600;">{status_icon} {task.get('session_key', 'Unknown')}</span>
                        <span style="color: {status_color}; font-size: 14px;">{status}</span>
                    </div>
                    <div style="color: #9ca3af; font-size: 14px; margin-top: 4px;">{summary}</div>
                    <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">{format_time_ago(task.get('timestamp', ''))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown("*No completed sub-agents recorded*")


def page_activity():
    """Activity feed page."""
    st.markdown("# Activity Feed")
    
    activity = get_activity_feed()
    
    filter_option = st.selectbox(
        "Filter by type",
        ["All", "Sessions", "Tasks", "Deliverables", "Errors"],
    )
    
    if filter_option != "All":
        type_map = {
            "Sessions": ["session_started", "session_ended"],
            "Tasks": ["task_started", "task_completed", "task_failed"],
            "Deliverables": ["deliverable_created"],
            "Errors": ["error_occurred", "task_failed"],
        }
        allowed_types = type_map.get(filter_option, [])
        activity = [e for e in activity if e.get("type") in allowed_types]
    
    st.markdown(f"**{len(activity)} events**")
    st.markdown("---")
    
    if activity:
        for event in reversed(activity):
            render_activity_item(event)
    else:
        st.info("No activity recorded yet.")
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh", key="activity_refresh"):
        st.rerun()


# =============================================================================
# Main App
# =============================================================================

def main():
    """Main app entry point."""
    
    # Custom CSS
    st.markdown(
        """
        <style>
            .stApp { background-color: #030712; }
            .stMarkdown { color: #e5e7eb; }
            section[data-testid="stSidebar"] { background-color: #111827; }
            .stButton > button {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
            }
            .stButton > button:hover {
                background-color: #374151;
                border-color: #4b5563;
            }
            .stSelectbox > div > div { background-color: #1f2937; color: #e5e7eb; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] {
                background-color: #1f2937;
                border-radius: 8px;
                padding: 8px 16px;
                color: #9ca3af;
            }
            .stTabs [aria-selected="true"] {
                background-color: #374151;
                color: #ffffff;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Navigation tabs
    tabs = st.tabs(["🏠 Home", "💬 Sessions", "🤖 Sub-Agents", "📋 Activity"])
    
    with tabs[0]:
        page_home()
    
    with tabs[1]:
        if st.session_state.page == "session_detail":
            page_session_detail()
        else:
            page_sessions()
    
    with tabs[2]:
        page_subagents()
    
    with tabs[3]:
        page_activity()


if __name__ == "__main__":
    main()
