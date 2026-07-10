"""Reusable UI building blocks shared by every page: CSS injection, cards,
badges, page headers, metric tiles. Keeps pages declarative instead of each
one hand-rolling HTML."""

from pathlib import Path

import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "theme" / "style.css"


def inject_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    st.markdown(
        f"""<div class="page-header">
            <h1>{icon + ' ' if icon else ''}{title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>""",
        unsafe_allow_html=True,
    )


def card_open(extra_class: str = "") -> None:
    st.markdown(f"<div class='cd-card {extra_class}'>", unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def feature_card(icon: str, title: str, body: str) -> str:
    return f"""<div class="cd-card feature-card">
        <div class="feature-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{body}</p>
    </div>"""


def badge(text: str, kind: str = "info") -> str:
    return f"<span class='cd-badge cd-badge-{kind}'>{text}</span>"


def metric_tile(label: str, value: str, icon: str = "") -> str:
    return f"""<div class="cd-metric">
        <div class="cd-metric-icon">{icon}</div>
        <div class="cd-metric-value">{value}</div>
        <div class="cd-metric-label">{label}</div>
    </div>"""


def render_html(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)
