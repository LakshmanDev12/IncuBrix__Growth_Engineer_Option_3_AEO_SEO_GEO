"""Shared UI components, design tokens, Plotly themes, and API communication client for IncuBrix Visibility Intelligence."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001/v1")


def apply_saas_theme() -> None:
    """Inject selective, polished enterprise CSS overrides matching Linear & Vercel aesthetics."""
    custom_css = """
    <style>
    /* Global font & background adjustments */
    body, [data-testid="stAppViewContainer"] {
        background-color: #090d16;
        color: #f9fafb;
    }
    
    /* Subtle 1px borders and rounded corners for containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #1f2937 !important;
        border-radius: 8px !important;
        background-color: #111827;
    }
    
    /* Card headers & caption muted text */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #9ca3af !important;
        font-size: 0.85rem;
    }
    
    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 14px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        color: #f9fafb !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    
    /* Primary buttons with refined violet accent */
    button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
        border: 1px solid #8b5cf6 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
        border-color: #a78bfa !important;
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.35);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #070a10 !important;
        border-right: 1px solid #1f2937 !important;
    }
    
    /* Expander styling */
    [data-testid="stExpander"] {
        border: 1px solid #1f2937 !important;
        border-radius: 8px !important;
        background-color: #111827 !important;
        margin-bottom: 8px;
    }
    
    /* Dataframe tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #1f2937;
        border-radius: 8px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def get_plotly_layout(
    height: int = 300,
    title: Optional[str] = None,
    barmode: Optional[str] = None,
    showlegend: bool = True,
) -> Dict[str, Any]:
    """Return dark-mode enterprise Plotly layout matching deep navy and violet tokens."""
    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#f9fafb", "family": "Inter, -apple-system, sans-serif", "size": 12},
        "colorway": ["#8b5cf6", "#10b981", "#3b82f6", "#f59e0b", "#ec4899", "#06b6d4"],
        "height": height,
        "margin": {"l": 30, "r": 20, "t": 35 if title else 20, "b": 30},
        "xaxis": {
            "gridcolor": "#1f2937",
            "zerolinecolor": "#1f2937",
            "tickfont": {"color": "#9ca3af", "size": 11},
        },
        "yaxis": {
            "gridcolor": "#1f2937",
            "zerolinecolor": "#1f2937",
            "tickfont": {"color": "#9ca3af", "size": 11},
        },
        "showlegend": showlegend,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": "#9ca3af", "size": 11},
        },
    }
    if title:
        layout["title"] = {
            "text": title,
            "font": {"size": 14, "color": "#f9fafb", "weight": 600},
            "x": 0.02,
        }
    if barmode:
        layout["barmode"] = barmode
    return layout


_shared_client: Optional[httpx.Client] = None


def _get_client(timeout: float = 3.0) -> httpx.Client:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.Client(timeout=timeout)
    return _shared_client


def get_api_data(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 2.5,
) -> Optional[Any]:
    """Fetch JSON payload from API backend with timeout resilience."""
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        client = _get_client(timeout=timeout)
        resp = client.get(url, params=clean_params)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def get_api_text(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 2.5,
) -> Optional[str]:
    """Fetch raw text or CSV payload from API backend."""
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        client = _get_client(timeout=timeout)
        resp = client.get(url, params=clean_params)
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None


def post_api_data(
    endpoint: str,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Optional[Any]:
    """Post JSON payload to API backend."""
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=json_data if json_data is not None else {})
            if resp.status_code in (200, 201):
                return resp.json()
            return None
    except Exception:
        return None


def patch_api_data(
    endpoint: str,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 8.0,
) -> Optional[Any]:
    """Patch JSON payload to API backend."""
    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.patch(url, json=json_data if json_data is not None else {})
            if resp.status_code == 200:
                return resp.json()
            return None
    except Exception:
        return None


def render_page_header(
    title: str,
    subtitle: str,
    breadcrumb: Optional[str] = None,
    badge_text: Optional[str] = None,
) -> None:
    """Render a clean, enterprise top header with breadcrumb and badge."""
    apply_saas_theme()
    with st.container():
        if breadcrumb:
            st.caption(f":material/navigate_next: {breadcrumb}")
        
        col_title, col_badge = st.columns([0.85, 0.15])
        with col_title:
            st.title(title)
            st.caption(subtitle)
        with col_badge:
            if badge_text:
                st.markdown(f":violet-badge[{badge_text}]")
        st.space("small")


def render_kpi_card(
    label: str,
    value: Any,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
    explanation: Optional[str] = None,
    icon: Optional[str] = None,
) -> None:
    """Render a bordered metric KPI card with icon, value, delta, and explanation."""
    card_label = f"{icon} {label}" if icon else label
    st.metric(
        label=card_label,
        value=value,
        delta=delta,
        help=help_text,
        border=True,
    )
    if explanation:
        st.caption(explanation)


def get_provenance_badge_markdown(obs: Dict[str, Any]) -> str:
    """Determine provenance and return standard markdown badge string."""
    meta = obs.get("meta") or {}
    raw = obs.get("raw_answer") or ""
    status = obs.get("collection_status", "")
    
    if status in ("unavailable", "failed"):
        return ":gray-badge[UNAVAILABLE]"
    elif meta.get("is_synthetic_test_fixture") or "TEST DATA" in raw:
        return ":orange-badge[MOCKED FIXTURE]"
    elif meta.get("is_manual_evidence") or meta.get("operator_id") or "manual" in obs.get("provider", ""):
        return ":blue-badge[MANUAL IMPORT]"
    else:
        return ":green-badge[REAL LIVE]"


def render_empty_state(
    title: str,
    description: str,
    icon: str = ":material/inbox:",
    action_label: Optional[str] = None,
    action_key: Optional[str] = None,
) -> bool:
    """Render an honest, polished empty state container. Returns True if action clicked."""
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.caption(description)
        if action_label and action_key:
            return st.button(action_label, key=action_key, type="primary")
    return False


def render_sidebar_global() -> Dict[str, Any]:
    """Render global sidebar filters and return selected filter values."""
    with st.sidebar:
        st.subheader("Global Slicing")
        
        market_filter = st.selectbox(
            "Target Market",
            ["All", "US", "UK", "CA", "AU"],
            index=0,
            key="global_market_filter",
            help="Filter search rankings, generative observations, and metrics by geographic market.",
        )
        
        provider_filter = st.selectbox(
            "Observation Provider",
            [
                "All",
                "google_search",
                "google_ai_overview",
                "perplexity",
                "chatgpt",
                "claude",
                "gemini",
                "bing_copilot",
            ],
            index=0,
            key="global_provider_filter",
            help="Filter observations by specific search engine or AI assistant.",
        )
        
        st.space("small")
        st.caption("Active Gateway: `http://127.0.0.1:8001/v1`")
        
        return {
            "market": None if market_filter == "All" else market_filter,
            "provider": None if provider_filter == "All" else provider_filter,
        }
