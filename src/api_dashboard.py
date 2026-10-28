import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="A/L Cutoff AI — API Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-safe { color: #155724; background-color: #d4edda; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-possible { color: #004085; background-color: #cce5ff; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-competitive { color: #856404; background-color: #fff3cd; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-unlikely { color: #721c24; background-color: #f8d7da; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Configuration & Telemetry
# ---------------------------------------------------------
st.sidebar.title("🎓 A/L Trends AI")
st.sidebar.caption("Sri Lanka University Admissions Forecaster")

api_url = st.sidebar.text_input("FastAPI Base URL", value="http://127.0.0.1:8000").rstrip("/")

# Session state for rate limit telemetry
if "rate_limit_info" not in st.session_state:
    st.session_state.rate_limit_info = {"limit": "N/A", "remaining": "N/A"}


def make_api_request(method: str, endpoint: str, **kwargs):
    """Helper to communicate with FastAPI backend and capture rate-limiting telemetry."""
    url = f"{api_url}{endpoint}"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.request(method, url, **kwargs)
            
            # Capture telemetry headers if present
            if "x-ratelimit-remaining" in resp.headers:
                st.session_state.rate_limit_info = {
                    "limit": resp.headers.get("x-ratelimit-limit", "N/A"),
                    "remaining": resp.headers.get("x-ratelimit-remaining", "N/A")
                }
                
            if resp.status_code == 429:
                err_data = resp.json()
                st.error(f"⚠️ **Rate Limit Exceeded (HTTP 429)**: {err_data.get('detail', 'Too many requests. Please wait a minute.')}")
                return None
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        st.error(f"🚨 **Cannot connect to API at `{api_url}`**.\nPlease make sure the FastAPI server is running:\n`uv run uvicorn src.api.main:app --port 8000 --reload`")
        return None
    except Exception as e:
        st.error(f"❌ **API Error**: {e}")
        return None


# Live Health Check Indicator
health_data = make_api_request("GET", "/health")

if health_data and health_data.get("status") == "healthy":
    st.sidebar.success("🟢 API Connected & Ready")
    with st.sidebar.expander("System Telemetry", expanded=False):
        st.write(f"**Version:** {health_data.get('version')}")
        st.write(f"**Supported Courses:** {health_data.get('supported_courses')}")
        st.write(f"**Supported Universities:** {health_data.get('supported_universities')}")
        st.write(f"**Supported Districts:** {health_data.get('supported_districts')}")
        st.write(f"**Rate Limit:** {st.session_state.rate_limit_info['remaining']} / {st.session_state.rate_limit_info['limit']} calls left")
else:
    st.sidebar.warning("🔴 API Offline")
    st.sidebar.code("uv run uvicorn src.api.main:app --reload", language="bash")
    if st.sidebar.button("🔄 Retry Connection"):
        st.rerun()

# ---------------------------------------------------------
# Load Metadata Catalogues
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_metadata(base_url: str):
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{base_url}/metadata/options")
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass
    return None

metadata = fetch_metadata(api_url)

# Fallback empty structures if metadata not loaded
courses_list = metadata.get("courses", ["MEDICINE", "ENGINEERING", "COMPUTER SCIENCE", "LAW"]) if metadata else []
unis_list = metadata.get("universities", ["University of Colombo", "University of Moratuwa", "University of Peradeniya"]) if metadata else []
districts_list = metadata.get("districts", ["COLOMBO", "GAMPAHA", "KANDY", "GALLE"]) if metadata else []
subjects_list = metadata.get("subjects", ["Combined Mathematics", "Physics", "Chemistry", "Biology"]) if metadata else []

# Navigation
page = st.sidebar.radio("Navigation", [
    "🔮 Single Cutoff Predictor",
    "🎓 Student Admission Analyzer",
    "⚖️ UGC Combination Validator",
    "📊 Batch University Comparison",
    "📖 API Documentation"
])

# ---------------------------------------------------------
# Page 1: Single Cutoff Predictor
# ---------------------------------------------------------
if page == "🔮 Single Cutoff Predictor":
    st.title("🔮 University Cutoff Z-Score Predictor")
    st.markdown("Forecast minimum qualifying cutoff marks for any degree program, university, and administrative district using the serialized `RandomForestRegressor` via the REST API.")

    col1, col2 = st.columns([1, 1])

    with col1:
        selected_course = st.selectbox(
            "Target Course of Study",
            options=courses_list,
            index=courses_list.index("MEDICINE") if "MEDICINE" in courses_list else 0
        )
        selected_uni = st.selectbox(
            "Target University",
            options=unis_list,
            index=unis_list.index("University of Colombo") if "University of Colombo" in unis_list else 0
        )

    with col2:
        selected_district = st.selectbox(
            "Candidate District",
            options=districts_list,
            index=districts_list.index("COLOMBO") if "COLOMBO" in districts_list else 0
        )
        selected_year = st.number_input("Forecast Exam Year", min_value=2024, max_value=2030, value=2026, step=1)

    predict_btn = st.button("🚀 Predict Cutoff Z-Score", type="primary", use_container_width=True)

    if predict_btn:
        with st.spinner("Calling ML Model Prediction API..."):
            payload = {
                "course_name": selected_course,
                "university_name": selected_uni,
                "district_name": selected_district,
                "exam_year": int(selected_year)
            }
            res = make_api_request("POST", "/predict", json=payload)

            if res:
                st.markdown("---")
                pred_z = res["predicted_cutoff_z"]
                band = res["competitiveness_band"]
                hist = res.get("historical_stats")

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    hist_mean = hist["mean"] if hist else None
                    delta_str = f"{pred_z - hist_mean:+.4f} vs Hist Mean" if hist_mean else None
                    st.metric("Predicted Cutoff Z", f"{pred_z:.4f}", delta=delta_str)

                with m2:
                    st.metric("Competitiveness Tier", band)

                with m3:
                    if hist and hist["mean"]:
                        st.metric("Historical Mean Z", f"{hist['mean']:.4f}", f"± {hist['std']:.4f} SD")
                    else:
                        st.metric("Historical Mean Z", "N/A")

                with m4:
                    if hist and hist["min"] is not None:
                        st.metric("Historical Range", f"{hist['min']:.4f} - {hist['max']:.4f}", f"{hist['sample_count']} cycles")
                    else:
                        st.metric("Historical Range", "N/A")

                # Visual Plotly Gauge
                if hist and hist["min"] is not None:
                    fig = go.Figure()
                    fig.add_trace(go.Indicator(
                        mode="gauge+number+delta",
                        value=pred_z,
                        delta={'reference': hist['mean'], 'relative': False},
                        title={'text': f"{selected_course} Cutoff Forecast ({selected_year})"},
                        gauge={
                            'axis': {'range': [max(0.0, hist['min'] - 0.3), hist['max'] + 0.3]},
                            'bar': {'color': "royalblue"},
                            'steps': [
                                {'range': [hist['min'] - 0.3, hist['mean']], 'color': "#e8f4f8"},
                                {'range': [hist['mean'], hist['max'] + 0.3], 'color': "#ffebee"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': pred_z
                            }
                        }
                    ))
                    fig.update_layout(height=350, margin=dict(t=50, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Page 2: Student Admission Analyzer
# ---------------------------------------------------------
elif page == "🎓 Student Admission Analyzer":
    st.title("🎓 Student Eligibility & Admission Analyzer")
    st.markdown("Input your expected or actual A/L Z-Score to evaluate your admission margin across degree programs in your district.")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        student_z = st.number_input("Your Expected / Actual Z-Score", min_value=-1.0, max_value=3.5, value=1.85, step=0.01, format="%.4f")
    with col2:
        student_dist = st.selectbox("Your District", options=districts_list, index=districts_list.index("COLOMBO") if "COLOMBO" in districts_list else 0)
    with col3:
        course_keyword = st.text_input("Filter by Course Keyword (Optional)", value="", placeholder="e.g. ENGINEERING, MEDICINE")

    eval_btn = st.button("🔍 Evaluate My Admission Chances", type="primary", use_container_width=True)

    if eval_btn:
        with st.spinner("Analyzing candidate performance against forecasted admission thresholds..."):
            payload = {
                "student_z_score": float(student_z),
                "district_name": student_dist,
                "course_name": course_keyword.strip() if course_keyword.strip() else None,
                "exam_year": 2026
            }
            res = make_api_request("POST", "/evaluate/student", json=payload)

            if res:
                st.markdown("---")
                total = res["total_evaluated"]
                eligible = res["eligible_count"]

                k1, k2, k3 = st.columns(3)
                with k1:
                    st.metric("Total Programs Evaluated", total)
                with k2:
                    st.metric("Eligible Programs (Safe / Possible)", eligible, f"{eligible/total:.1%}" if total > 0 else "")
                with k3:
                    evals = res["evaluations"]
                    safe_count = sum(1 for e in evals if e["status"] == "Safe")
                    st.metric("High Confidence ('Safe') Options", safe_count)

                if evals:
                    df_eval = pd.DataFrame(evals)

                    # Plotly Margin Chart for top 20 options
                    plot_df = df_eval.head(20).copy()
                    color_map = {
                        "Safe": "#28a745",
                        "Possible": "#17a2b8",
                        "Competitive": "#ffc107",
                        "Unlikely": "#dc3545"
                    }

                    fig = px.bar(
                        plot_df,
                        x="margin",
                        y="university_name",
                        color="status",
                        color_discrete_map=color_map,
                        orientation="h",
                        hover_data=["course_name", "predicted_cutoff_z"],
                        labels={"margin": "Z-Score Margin (Student Z - Forecast Cutoff)", "university_name": "University"},
                        title=f"Top 20 Programs Ranked by Admission Margin ({student_dist} District)"
                    )
                    fig.add_vline(x=0, line_dash="dash", line_color="black")
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=550)
                    st.plotly_chart(fig, use_container_width=True)

                    # Interactive Data Table
                    st.subheader("📋 Comprehensive Program Evaluation Table")
                    st.dataframe(
                        df_eval.style.apply(
                            lambda row: [
                                'background-color: #d4edda' if row['status'] == 'Safe'
                                else 'background-color: #cce5ff' if row['status'] == 'Possible'
                                else 'background-color: #fff3cd' if row['status'] == 'Competitive'
                                else 'background-color: #f8d7da' for _ in row
                            ], axis=1
                        ),
                        use_container_width=True
                    )

# ---------------------------------------------------------
# Page 3: UGC Subject Combination Validator
# ---------------------------------------------------------
elif page == "⚖️ UGC Combination Validator":
    st.title("⚖️ UGC Subject Combination Rule Engine")
    st.markdown("Validate any 3-subject G.C.E. A/L combination against official University Grants Commission admission circulars.")

    st.info("💡 **UGC Rule Engine Features:** Verifies mathematical validity, blocks disallowed pairings (such as *Biology + Combined Mathematics*), enforces open technology baskets, and suggests single-subject swaps when invalid.")

    # Preset Quick Buttons
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    preset_choice = None
    if col_p1.button("Preset: Bio Science"):
        preset_choice = ["Biology", "Chemistry", "Physics"]
    if col_p2.button("Preset: Physical Science"):
        preset_choice = ["Combined Mathematics", "Physics", "Chemistry"]
    if col_p3.button("Preset: Eng Tech"):
        preset_choice = ["Engineering Technology", "Science for Technology", "ICT"]
    if col_p4.button("Preset: Disallowed Pair ⚠️"):
        preset_choice = ["Biology", "Combined Mathematics", "Chemistry"]

    selected_subjects = st.multiselect(
        "Select exactly 3 A/L Subjects:",
        options=subjects_list,
        default=preset_choice if preset_choice else (["Combined Mathematics", "Physics", "Chemistry"] if "Combined Mathematics" in subjects_list else subjects_list[:3]),
        max_selections=3
    )

    val_btn = st.button("🔎 Validate Subject Combination", type="primary", use_container_width=True)

    if val_btn:
        if len(selected_subjects) != 3:
            st.warning("Please select exactly 3 subjects to run the validation engine.")
        else:
            with st.spinner("Validating combination against UGC declarative rule engine..."):
                payload = {"subjects": selected_subjects}
                res = make_api_request("POST", "/validate/combination", json=payload)

                if res:
                    st.markdown("---")
                    if res["is_valid"]:
                        st.success("✅ **VALID COMBINATION**")
                        st.markdown(f"**Eligible UGC Stream(s):**")
                        for stream in res["matching_streams"]:
                            st.markdown(f"- 🎓 **{stream}**")
                    else:
                        st.error("❌ **INVALID COMBINATION**")
                        st.markdown(f"**Reason for Rejection:**\n> {res['failure_reason']}")

                        swaps = res.get("suggested_swaps", [])
                        if swaps:
                            st.markdown("### 🔄 Recommended Single-Subject Swaps:")
                            for swap in swaps:
                                st.markdown(f"- 💡 {swap}")

# ---------------------------------------------------------
# Page 4: Batch University Comparison
# ---------------------------------------------------------
elif page == "📊 Batch University Comparison":
    st.title("📊 Multi-University Batch Cutoff Forecaster")
    st.markdown("Compare cutoff forecasts across all state universities for a specific degree program in a single API batch call (`POST /predict/batch`).")

    col1, col2 = st.columns(2)
    with col1:
        batch_course = st.selectbox("Degree Program", options=courses_list, index=courses_list.index("ENGINEERING") if "ENGINEERING" in courses_list else 0)
    with col2:
        batch_district = st.selectbox("Student District", options=districts_list, index=districts_list.index("KANDY") if "KANDY" in districts_list else 0)

    batch_btn = st.button("⚡ Run Multi-University Batch Forecast", type="primary", use_container_width=True)

    if batch_btn:
        # Build batch items for all known universities
        batch_items = [
            {
                "course_name": batch_course,
                "university_name": u,
                "district_name": batch_district,
                "exam_year": 2026
            }
            for u in unis_list
        ]

        with st.spinner(f"Sending batch request with {len(batch_items)} comparisons to FastAPI backend..."):
            res = make_api_request("POST", "/predict/batch", json={"items": batch_items})

            if res:
                preds = res["predictions"]
                df_batch = pd.DataFrame([
                    {
                        "University": p["university_name"],
                        "Forecast Cutoff Z": p["predicted_cutoff_z"],
                        "Competitiveness": p["competitiveness_band"],
                        "Historical Mean": p["historical_stats"]["mean"] if p.get("historical_stats") else None
                    }
                    for p in preds
                ]).sort_values("Forecast Cutoff Z", ascending=False)

                st.subheader(f"Forecast Comparison: {batch_course} ({batch_district} District)")

                fig = px.bar(
                    df_batch,
                    x="Forecast Cutoff Z",
                    y="University",
                    color="Forecast Cutoff Z",
                    color_continuous_scale="Blues",
                    orientation="h",
                    title=f"Cutoff Requirements by University ({batch_course})"
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(df_batch, use_container_width=True)

# ---------------------------------------------------------
# Page 5: API Documentation
# ---------------------------------------------------------
elif page == "📖 API Documentation":
    st.title("📖 API Architecture & Integration")
    st.markdown("""
    This dashboard interacts entirely with the **Sri Lanka A/L Cutoff Prediction REST API** built with **FastAPI**, **Pydantic v2**, and **slowapi**.

    ### 🔗 Live Interactive Docs
    - **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    - **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

    ### 🛡️ Built-in Resilience & MLOps Features:
    1. **Strict Rate Limiting**: Powered by `slowapi` and client IP sliding windows to protect compute nodes.
    2. **Star Schema Integration**: Preloads database aggregates from SQLite for instant $O(1)$ response times.
    3. **Automated UGC Combinatorial Validation**: Enforces official circular rules for 168+ valid subject combinations.
    4. **Time-Based ML Splitting**: Model trained without temporal leakage, evaluated with an $R^2 = 0.8364$ on the latest holdout academic year.
    """)
