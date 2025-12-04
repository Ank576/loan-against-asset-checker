import streamlit as st
st.set_page_config(page_title="LAA Checker", page_icon="🏠", layout="wide")
from datetime import datetime
import os
from openai import OpenAI

# --- Add global CSS for fonts and section spacing ---
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 15px;
    }
    h1 { font-size: 32px; font-weight: 700; }
    h2 { font-size: 24px; font-weight: 600; }
    h3 { font-size: 18px; font-weight: 600; }
    .small-text { font-size: 13px; color: #6b7280; }
    .custom-footer {
        position: fixed;
        left: 0; bottom: 0; width: 100%; text-align: center;
        padding: 8px 0; font-size: 13px; color: #6b7280;
        background: rgba(255,255,255,0.85); backdrop-filter: blur(6px);
        z-index: 1000;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY", ""),
    base_url="https://api.perplexity.ai"
)

# === RBI RULES & VALIDATION FUNCTIONS ===

RBI_RULES = {
    "gold_loan": {
        "max_ltv_urban": 0.75,
        "max_ltv_rural": 0.70,
        "purity_min": 18,
        "max_loan_amount": 10000000,
    },
    "property_mortgage": {
        "max_ltv": 0.80,
        "circle_rate_tolerance": 0.10,
        "max_loan_amount": 50000000,
    },
    "share_pledge": {
        "max_ltv_nifty50": 0.50,
        "max_ltv_nifty100": 0.45,
        "max_ltv_other": 0.40,
        "max_loan_amount": 5000000,
    },
}

def validate_gold(asset_value, loan_amount, location, purity):
    """Validate gold loan against RBI norms."""
    errors = []
    rules = RBI_RULES["gold_loan"]
    
    # Check purity
    if purity < rules["purity_min"]:
        errors.append(f"Gold purity {purity} carats below RBI minimum of {rules['purity_min']} carats")
    
    # Check LTV
    ltv_limit = rules["max_ltv_urban"] if location == "Urban" else rules["max_ltv_rural"]
    ltv_used = (loan_amount / asset_value * 100) if asset_value > 0 else 0
    max_eligible = asset_value * ltv_limit
    
    if loan_amount > max_eligible:
        errors.append(f"Loan amount exceeds LTV limit of {ltv_limit*100:.0f}%")
    
    # Check max loan amount
    if loan_amount > rules["max_loan_amount"]:
        errors.append(f"Loan amount exceeds RBI maximum of ₹{rules['max_loan_amount']:,}")
    
    approved = len(errors) == 0
    ltv_limit_str = f"{ltv_limit*100:.0f}%"
    
    return approved, max_eligible, ltv_used, errors, ltv_limit_str

def validate_property(asset_value, loan_amount, circle_rate):
    """Validate property mortgage against RBI norms."""
    errors = []
    rules = RBI_RULES["property_mortgage"]
    
    # Check circle rate variance
    if asset_value > 0:
        variance = abs(asset_value - circle_rate) / circle_rate
        if variance > rules["circle_rate_tolerance"]:
            errors.append(f"Property value variance from circle rate exceeds {rules['circle_rate_tolerance']*100:.0f}%")
    
    # Check LTV
    ltv_limit = rules["max_ltv"]
    ltv_used = (loan_amount / asset_value * 100) if asset_value > 0 else 0
    max_eligible = asset_value * ltv_limit
    
    if loan_amount > max_eligible:
        errors.append(f"Loan amount exceeds LTV limit of {ltv_limit*100:.0f}%")
    
    # Check max loan amount
    if loan_amount > rules["max_loan_amount"]:
        errors.append(f"Loan amount exceeds RBI maximum of ₹{rules['max_loan_amount']:,}")
    
    approved = len(errors) == 0
    ltv_limit_str = f"{ltv_limit*100:.0f}%"
    
    return approved, max_eligible, ltv_used, errors, ltv_limit_str

def validate_shares(asset_value, loan_amount, share_index):
    """Validate share pledge against RBI norms."""
    errors = []
    rules = RBI_RULES["share_pledge"]
    
    # Get LTV limit based on index
    if share_index == "NIFTY50":
        ltv_limit = rules["max_ltv_nifty50"]
    elif share_index == "NIFTY100":
        ltv_limit = rules["max_ltv_nifty100"]
    else:
        ltv_limit = rules["max_ltv_other"]
    
    ltv_used = (loan_amount / asset_value * 100) if asset_value > 0 else 0
    max_eligible = asset_value * ltv_limit
    
    if loan_amount > max_eligible:
        errors.append(f"Loan amount exceeds LTV limit of {ltv_limit*100:.0f}% for {share_index}")
    
    # Check max loan amount
    if loan_amount > rules["max_loan_amount"]:
        errors.append(f"Loan amount exceeds RBI maximum of ₹{rules['max_loan_amount']:,}")
    
    approved = len(errors) == 0
    ltv_limit_str = f"{ltv_limit*100:.0f}%"
    
    return approved, max_eligible, ltv_used, errors, ltv_limit_str

def get_llm_analysis(asset_type, params):
    """Get AI-powered RBI compliance analysis from Perplexity API."""
    try:
        prompt = f"""
Analyze this {asset_type} against RBI regulations:
- Asset Value: ₹{params.get('asset_value', 0):,}
- Loan Amount: ₹{params.get('loan_amount', 0):,}
- LTV Used: {params.get('ltv_used', 0):.1f}%

Provide key RBI guidelines, compliance status, and recommendations.
        """
        
response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error fetching LLM analysis: {str(e)}. Please ensure PERPLEXITY_API_KEY is set."

st.markdown("# 🏦 Loan Against Asset Checker")
st.markdown("#### RBI-compliant asset-backed lending with AI-powered RBI guidance")
st.markdown("---")

if "results_tab" not in st.session_state:
    st.session_state.results_tab = False

with st.sidebar:
    asset_type = st.selectbox("Asset Type", ["Gold Loan", "Property Mortgage", "Share Pledge"])

# Input columns:
if not st.session_state.results_tab:
    col1, col2 = st.columns(2)

    if asset_type == "Gold Loan":
        with col1:
            st.markdown("### 📋 Enter Details")
            asset_value = st.number_input("Asset Value (₹)", min_value=0, step=10000, value=100000)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=10000, value=75000)
            location = st.radio("Location", ["Urban", "Rural"])
            purity = st.slider("Gold Purity (Carats)", 14, 24, 22)

        # --- Interactive progress/status block ---
        if st.button("🔍 Submit for Validation & AI Analysis", key="gold_submit", use_container_width=True):
            with st.status("Validating gold asset and running LLM analysis ...", expanded=True) as status:
                approved, max_eligible, ltv_used, errors, ltv_limit = validate_gold(asset_value, loan_amount, location, purity)
                st.session_state.asset_type = asset_type
                st.session_state.approved = approved
                st.session_state.max_eligible = max_eligible
                st.session_state.ltv_used = ltv_used
                st.session_state.errors = errors
                st.session_state.ltv_limit = ltv_limit
                st.session_state.params = {'asset_value': asset_value, 'loan_amount': loan_amount, 'location': location, 'purity': purity, 'ltv_used': ltv_used}
                st.session_state.results_tab = True
                status.update(label="Gathering latest RBI rules...", state="running")
            st.rerun()

    elif asset_type == "Property Mortgage":
        with col1:
            st.markdown("### 📋 Enter Details")
            asset_value = st.number_input("Property Value (₹)", min_value=0, step=100000, value=5000000)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=100000, value=3000000)
            circle_rate = st.number_input("Circle Rate (₹)", min_value=0, step=100000, value=4500000)

        if st.button("🔍 Submit for Validation & AI Analysis", key="prop_submit", use_container_width=True):
            with st.status("Validating property and running LLM analysis ...", expanded=True) as status:
                approved, max_eligible, ltv_used, errors, ltv_limit = validate_property(asset_value, loan_amount, circle_rate)
                st.session_state.asset_type = asset_type
                st.session_state.approved = approved
                st.session_state.max_eligible = max_eligible
                st.session_state.ltv_used = ltv_used
                st.session_state.errors = errors
                st.session_state.ltv_limit = ltv_limit
                st.session_state.params = {'asset_value': asset_value, 'loan_amount': loan_amount, 'circle_rate': circle_rate, 'ltv_used': ltv_used}
                st.session_state.results_tab = True
                status.update(label="Gathering latest RBI rules...", state="running")
            st.rerun()

    else: # Share Pledge
        with col1:
            st.markdown("### 📋 Enter Details")
            asset_value = st.number_input("Portfolio Value (₹)", min_value=0, step=10000, value=100000)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=10000, value=50000)
            share_index = st.selectbox("Share Index", ["NIFTY50", "NIFTY100", "Other"])

        if st.button("🔍 Submit for Validation & AI Analysis", key="shares_submit", use_container_width=True):
            with st.status("Validating pledged shares and running LLM analysis ...", expanded=True) as status:
                approved, max_eligible, ltv_used, errors, ltv_limit = validate_shares(asset_value, loan_amount, share_index)
                st.session_state.asset_type = asset_type
                st.session_state.approved = approved
                st.session_state.max_eligible = max_eligible
                st.session_state.ltv_used = ltv_used
                st.session_state.errors = errors
                st.session_state.ltv_limit = ltv_limit
                st.session_state.params = {'asset_value': asset_value, 'loan_amount': loan_amount, 'share_index': share_index, 'ltv_used': ltv_used}
                st.session_state.results_tab = True
                status.update(label="Gathering latest RBI rules...", state="running")
            st.rerun()
else:
    st.markdown("### ✅ Validation Results & RBI Compliance Analysis")
    st.markdown("---")

    if st.button("← Back to Input", use_container_width=True):
        st.session_state.results_tab = False
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Quick Summary")
        if st.session_state.approved:
            st.success("✅ APPROVED")
        else:
            st.error("❌ REJECTED")

        st.metric("Max Eligible", f"₹{int(st.session_state.max_eligible):,}")
        st.metric("LTV Used", f"{st.session_state.ltv_used:.1f}%")
        st.metric("LTV Limit", st.session_state.ltv_limit)

        # --- LTV progress bar ---
        ltv_val = float(st.session_state.ltv_used)
        ltv_limit_num = float(st.session_state.ltv_limit.strip('%'))
        ltv_ratio = min(ltv_val / ltv_limit_num, 1.0)
        st.progress(ltv_ratio, text=f"LTV usage: {st.session_state.ltv_used:.1f}% of {st.session_state.ltv_limit}")

        # --- RBI errors in expander ---
        if st.session_state.errors:
            with st.expander("⚠️ RBI Rule Violations", expanded=True):
                for error in st.session_state.errors:
                    st.warning(f"• {error}")

    with col2:
        st.markdown("#### Input Parameters")
        for key, value in st.session_state.params.items():
            if key != 'ltv_used':
                st.info(f"**{key.replace('_', ' ').title()}**: {value}")

    st.markdown("---")
    st.markdown("#### 🤖 AI-Powered RBI Compliance Analysis")
    st.markdown("*Fetching latest RBI guidelines via Perplexity API*")

    with st.spinner("Analyzing parameters against RBI guidelines..."):
        llm_response = get_llm_analysis(st.session_state.asset_type, st.session_state.params)
        with st.expander("📜 Full RBI LLM Analysis", expanded=True):
            st.markdown(llm_response)

# --- Footer (fixed bar) ---
st.markdown(
    f"""
    <div class="custom-footer">
        Built by <b>Ankit Saxena</b> with 🧡 · Powered by Streamlit &amp; Perplexity · {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
    """,
    unsafe_allow_html=True,
)
