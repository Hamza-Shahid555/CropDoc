import pandas as pd
import streamlit as st

from streamlit_app.config import BASE_DIR
from streamlit_app.core import db, ui

ui.page_header("Dashboard", "Model evaluation and live usage stats.", "📊")

stats = db.get_dashboard_stats()

c1, c2, c3, c4 = st.columns(4)
c1.markdown(ui.metric_tile("Total diagnoses", str(stats["total_predictions"]), "🔍"), unsafe_allow_html=True)
c2.markdown(ui.metric_tile("Healthy plants", str(stats["healthy_count"]), "🌱"), unsafe_allow_html=True)
c3.markdown(ui.metric_tile("Diseased plants", str(stats["diseased_count"]), "🦠"), unsafe_allow_html=True)
avg_conf = f"{stats['avg_confidence']:.0f}%" if stats["avg_confidence"] is not None else "—"
c4.markdown(ui.metric_tile("Avg. confidence", avg_conf, "📈"), unsafe_allow_html=True)

st.write("")
col_left, col_right = st.columns(2)
with col_left:
    ui.card_open()
    st.markdown("**Most common diseases**")
    if stats["top_classes"]:
        for row in stats["top_classes"]:
            st.markdown(f"- {row['disease_name']} — {row['c']}")
    else:
        st.caption("No predictions logged yet — try Disease Detection.")
    ui.card_close()

with col_right:
    ui.card_open()
    st.markdown("**Diagnoses per day**")
    trend = db.get_prediction_trend()
    if trend:
        df = pd.DataFrame(trend).set_index("day")
        st.bar_chart(df["c"], height=200)
    else:
        st.caption("Trend appears once a few diagnoses are logged.")
    ui.card_close()

recent = db.get_recent_predictions(8)
if recent:
    ui.card_open()
    st.markdown("**Recent analyses**")
    df = pd.DataFrame(recent)[["created_at", "disease_name", "confidence", "is_healthy"]]
    df.columns = ["When", "Diagnosis", "Confidence %", "Healthy"]
    df["Confidence %"] = df["Confidence %"].round(1)
    df["Healthy"] = df["Healthy"].map({1: "✅", 0: "⚠️"})
    st.dataframe(df, width="stretch", hide_index=True)
    ui.card_close()

st.write("")
st.markdown("### Model evaluation (from training)")
st.caption("ResNet9, 38 classes, trained on the PlantVillage-style dataset — see CropDoc_Training.ipynb.")

figures = [
    ("training_history.png", "Training accuracy / loss curves"),
    ("confusion_matrix.png", "Confusion matrix"),
    ("per_class_accuracy.png", "Per-class accuracy"),
    ("class_distribution.png", "Class distribution (EDA)"),
    ("gradcam_samples.png", "Grad-CAM samples"),
    ("sample_images.png", "Sample images grid"),
]

cols = st.columns(2)
for i, (filename, caption) in enumerate(figures):
    path = BASE_DIR / filename
    if path.is_file():
        with cols[i % 2]:
            ui.card_open()
            st.image(str(path), caption=caption, width="stretch")
            ui.card_close()

report_path = BASE_DIR / "classification_report.txt"
if report_path.is_file():
    with st.expander("Full classification report (validation set)"):
        st.code(report_path.read_text(encoding="utf-8"), language=None)
