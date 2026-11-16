"""Shared presentation helpers for the Streamlit UI."""

import streamlit as st


def apply_theme() -> None:
    """Apply the shared visual style used by every page."""
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #f7f9fc; }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: none; width: 100%; padding: 2rem 3rem 3rem 3rem; }
        .hero { background: linear-gradient(135deg, #12355b, #1f6f8b); color: white;
                padding: 2.2rem 2.4rem; border-radius: 18px; margin-bottom: 1.4rem; }
        .hero h1 { margin: 0 0 .4rem 0; font-size: 2.35rem; }
        .hero p { margin: 0; color: #e5f4fa; font-size: 1.05rem; }
        .section-card { background: white; border: 1px solid #e4eaf1; border-radius: 14px;
                        padding: 1.1rem 1.25rem; height: 100%; }
        .section-card h3 { margin-top: 0; color: #12355b; }
        .muted { color: #607080; font-size: .92rem; }
        div[data-testid="stMetric"] { background: white; border: 1px solid #e4eaf1;
                                        padding: .8rem 1rem; border-radius: 12px; }
        .status-card { background: white; border: 1px solid #e4eaf1; border-left: 6px solid;
                       border-radius: 12px; padding: 1rem 1.2rem; margin: 1rem 0; }
        .status-label { color: #607080; font-size: .82rem; text-transform: uppercase;
                        letter-spacing: .06em; }
        .status-value { font-size: 1.55rem; font-weight: 700; margin: .15rem 0 .25rem; }
        @media (max-width: 700px) {
          .block-container { padding: 1rem 1rem 2rem 1rem; }
          .hero { padding: 1.5rem; }
          .hero h1 { font-size: 1.8rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_intro(title: str, description: str) -> None:
    """Render a consistent page heading."""
    st.title(title)
    st.caption(description)

