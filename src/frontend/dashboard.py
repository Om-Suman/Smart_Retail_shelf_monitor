"""
Smart Retail Shelf Monitoring Dashboard

Features
--------
- Upload shelf image
- Call FastAPI backend
- Display original image
- Display annotated image
- Display inference metrics
"""

from __future__ import annotations

import base64
from io import BytesIO

import httpx
import pandas as pd
import streamlit as st
from PIL import Image
import plotly.express as px
import os

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------

st.set_page_config(
    page_title="Smart Retail Shelf Monitoring",
    page_icon="🛒",
    layout="wide",
)

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------

st.sidebar.title("Configuration")



API_URL = st.sidebar.text_input(
    "FastAPI URL",
    value=os.getenv(
        "API_URL",
        "http://127.0.0.1:8000/api/v1/detect",
    ),
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
Upload a shelf image.

The dashboard will:

- Detect products
- Count inventory
- Display annotated image
- Show analytics
"""
)

# -------------------------------------------------------
# Title
# -------------------------------------------------------

st.title("🛒 Smart Retail Shelf Monitoring")

st.markdown(
    """
Computer Vision powered inventory monitoring using

- YOLOv11
- FastAPI
- PyTorch
- OpenCV
"""
)

st.divider()

# -------------------------------------------------------
# Upload
# -------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Shelf Image",
    type=["jpg", "jpeg", "png"],
)

# -------------------------------------------------------
# Utility
# -------------------------------------------------------

def decode_base64_image(
    encoded: str,
) -> Image.Image:
    """
    Convert Base64 string to PIL Image.
    """

    image_bytes = base64.b64decode(encoded)

    return Image.open(
        BytesIO(image_bytes)
    )

# -------------------------------------------------------
# Detection
# -------------------------------------------------------

if uploaded_file is not None:

    original = Image.open(uploaded_file)

    left, right = st.columns(2)

    with left:

        st.subheader("Original Image")

        st.image(
            original,
            use_container_width=True,
        )

    if st.button(
        "🚀 Detect Products",
        use_container_width=True,
    ):

        with st.spinner(
            "Running YOLO inference..."
        ):

            uploaded_file.seek(0)

            files = {

                "image": (

                    uploaded_file.name,

                    uploaded_file,

                    uploaded_file.type,

                )

            }

            try:

                response = httpx.post(
                    API_URL,
                    files=files,
                    timeout=120,
                )

            except Exception as e:

                st.error(
                    f"Unable to connect.\n\n{e}"
                )

                st.stop()

            if response.status_code != 200:

                st.error(
                    response.text
                )

                st.stop()

            data = response.json()

            annotated = decode_base64_image(
                data["annotated_image"]
            )

            with right:

                st.subheader(
                    "Detection Result"
                )

                st.image(
                    annotated,
                    use_container_width=True,
                )

            st.success(
                "Detection completed successfully."
            )

            st.session_state["response"] = data

        # -------------------------------------------------------
# Analytics Dashboard
# -------------------------------------------------------

if "response" in st.session_state:

    data = st.session_state["response"]

    inventory = data["inventory"]

    metadata = data["metadata"]

    detections = data["detections"]

    st.divider()

    st.subheader("📈 Detection Metrics")

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Objects Detected",
        inventory["total_objects"],
    )

    metric2.metric(
        "Inference Time",
        f'{metadata["inference_time_ms"]:.2f} ms',
    )

    metric3.metric(
        "Model",
        metadata["model_name"],
    )

    st.divider()

    # -------------------------------------------------------
    # Inventory Summary
    # -------------------------------------------------------

    st.subheader("📦 Inventory Summary")

    inventory_df = pd.DataFrame(
        inventory["products"]
    )

    inventory_df.columns = [
        "Product",
        "Quantity",
    ]

    left, right = st.columns([1, 1])

    with left:

        st.dataframe(
            inventory_df,
            use_container_width=True,
            hide_index=True,
        )

    with right:

        st.bar_chart(
            inventory_df.set_index("Product")
        )

    st.divider()

    # -------------------------------------------------------
    # Detection Details
    # -------------------------------------------------------

    st.subheader("🎯 Detection Details")

    detection_df = pd.DataFrame(detections)

    detection_df = detection_df[
        [
            "class_name",
            "confidence",
            "x_min",
            "y_min",
            "x_max",
            "y_max",
        ]
    ]

    detection_df.columns = [
        "Class",
        "Confidence",
        "X Min",
        "Y Min",
        "X Max",
        "Y Max",
    ]

    detection_df["Confidence"] = (
        detection_df["Confidence"] * 100
    ).round(2)

    detection_df["Confidence"] = (
        detection_df["Confidence"]
        .astype(str)
        + "%"
    )

    st.dataframe(
        detection_df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # -------------------------------------------------------
    # Confidence Statistics
    # -------------------------------------------------------

    st.subheader("📊 Confidence Statistics")

    confidence_values = [
        detection["confidence"]
        for detection in detections
    ]

    avg_confidence = (
        sum(confidence_values)
        / len(confidence_values)
        if confidence_values
        else 0
    )

    min_confidence = (
        min(confidence_values)
        if confidence_values
        else 0
    )

    max_confidence = (
        max(confidence_values)
        if confidence_values
        else 0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Average",
        f"{avg_confidence:.2%}",
    )

    c2.metric(
        "Highest",
        f"{max_confidence:.2%}",
    )

    c3.metric(
        "Lowest",
        f"{min_confidence:.2%}",
    )

    # -------------------------------------------------------
# Download Annotated Image
# -------------------------------------------------------
if "response" not in st.session_state:
    st.stop()

data = st.session_state["response"]

inventory = data["inventory"]

metadata = data["metadata"]

detections = data["detections"]

st.divider()

st.subheader("📥 Export Results")

annotated_b64 = data["annotated_image"]

annotated_bytes = base64.b64decode(
    annotated_b64
)

st.download_button(
    label="⬇️ Download Annotated Image",
    data=annotated_bytes,
    file_name="annotated_detection.jpg",
    mime="image/jpeg",
    use_container_width=True,
)

# -------------------------------------------------------
# Plotly Charts
# -------------------------------------------------------

import plotly.express as px

st.divider()

st.subheader("📈 Interactive Analytics")

inventory_chart = px.bar(
    inventory_df,
    x="Product",
    y="Quantity",
    text="Quantity",
    title="Inventory Distribution",
)

inventory_chart.update_layout(
    xaxis_title="Product",
    yaxis_title="Count",
)

st.plotly_chart(
    inventory_chart,
    use_container_width=True,
)

# -------------------------------------------------------
# Confidence Distribution
# -------------------------------------------------------

confidence_df = pd.DataFrame(
    {
        "Confidence": confidence_values
    }
)

histogram = px.histogram(
    confidence_df,
    x="Confidence",
    nbins=10,
    title="Confidence Distribution",
)

st.plotly_chart(
    histogram,
    use_container_width=True,
)

# -------------------------------------------------------
# Detection Summary
# -------------------------------------------------------

st.divider()

st.subheader("📋 Detection Summary")

summary = f"""
### Session Summary

- Objects Detected : **{inventory['total_objects']}**
- Model : **{metadata['model_name']}**
- Inference Time : **{metadata['inference_time_ms']:.2f} ms**
- Image Size : **{metadata['image_width']} × {metadata['image_height']}**
"""

st.markdown(summary)

# -------------------------------------------------------
# API Status
# -------------------------------------------------------

st.sidebar.divider()

st.sidebar.subheader("Backend")

from urllib.parse import urlparse

parsed = urlparse(API_URL)

health_url = f"{parsed.scheme}://{parsed.netloc}/health"

try:
    health = httpx.get(
        health_url,
        timeout=5,
    )

    if health.status_code == 200:
        st.sidebar.success("Backend Connected")
    else:
        st.sidebar.warning("Backend Error")

except Exception:
    st.sidebar.error("Backend Offline")

# -------------------------------------------------------
# Reset Session
# -------------------------------------------------------

st.sidebar.divider()

if st.sidebar.button(
    "Reset Dashboard",
    use_container_width=True,
):

    st.session_state.clear()

    st.rerun()

# -------------------------------------------------------
# Footer
# -------------------------------------------------------

st.divider()

st.caption(
    "Smart Retail Shelf Monitoring System | "
    "Built with FastAPI • YOLOv11 • OpenCV • PyTorch • Streamlit"
)