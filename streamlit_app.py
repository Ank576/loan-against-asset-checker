import streamlit as st
import os
from datetime import datetime
from openai import OpenAI

# Page config
st.set_page_config(page_title="LAA Checker", page_icon="🏠", layout="wide")

# Styling
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 15px;
}
h1 { font-size: 32px; font-weight: 700; }
h2 { font-size: 24px; font-weight: 600; }
h3 { font-size: 18px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Initialize Perplexity client
client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY", ""),
    base_url="https://api.perplexity.ai"
)

# RBI Compliance Rules
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

# Validation Functions
def validate_gold(asset_value, loan_amount, location, purity):
    errors = []
    rules = RBI_RULES["gold_loan"]
    
    if purity < rules["purity_min"]:
        errors.append(f"Gold purity {purity}C below RBI minimum of {rules['purity_min']}C")
    
    ltv_limit = rules["max_ltv_urban"] if location == "Urban" else rules["max_ltv_rural"]
    ltv_used = (loan_amount / asset_value * 100) if asset_value > 0 else 0
    max_eligible = asset_value * ltv_limit
    
    if loan_amount > max_eligible:
        errors.append(f"Loan exceeds LTV limit of {ltv_limit*100:.0f}%")
    
    if loan_amount > rules["max_loan_amount"]:
        errors.append(f"Exceeds RBI maximum of ₹{rules['max_loan_amount']:,}")
    
    approved = len(errors) == 0
    ltv_limit_str = f"{ltv_limit*100:.0f}%"
    
    return approved, max_eligible, ltv_used, errors, ltv_limit_str

def validate_property(asset_value, loan_amount, circle_rate):
    errors = []
    rules = RBI_RULES["property_mortgage"]
    
    if asset_value > 0:
        variance = abs(asset_value - circle_rate) / circle_rate
        if variance > rules["circle_rate_tolerance"]:
            errors.append(f"Property variance exceeds {rules['circle_rate_tolerance']*100:.0f}%")
    
    ltv_limit = rules["max_ltv"]
    ltv_used = (loan_amount / asset_value * 100) if asset_value > 0 else 0
    max_eligible = asset_value * ltv_limit
    
    if loan_amount > max_eligible:
        errors.append(f"Loan exceeds LTV limit of {ltv_limit*100:.0f}%")
    
    if loan_amount > rules["max_loan_amount"]:
        errors.append(f"Exceeds RBI maximum of ₹{rules['max_loan_amount']:,}")
    
    approved = len(errors) == 0
    ltv_limit_str = f"{ltv_limit*100:.0f}%"
    
    return approved, max_eligible, ltv_used, errors, ltv_limit_str

def validate_shares(asset_value, loan_amount, share_index):
    errors = []
    rules = RBI_RULES["share_pledge"]
    
    if share_index == "NIFTY50":
        ltv_limit = rules["max_ltv_nifty50"]
    elif share_index == "NIFTY100":
        ltv_limit = rules["max_ltv_nifty100"]
    else:
        ltv_limit = rules["max_ltv_other"]
    
    ltv_used = (loan_amount / asset_value * 100) if asset_value > 0 else 0
    max_eligible = asset_value * ltv_limit
    
    if loan_amount > max_eligible:
        errors.append(f"Loan exceeds {share_index} LTV limit of {ltv_limit*100:.0f}%")
    
    if loan_amount > rules["max_loan_amount"]:
        errors.append(f"Exceeds RBI maximum of ₹{rules['max_loan_amount']:,}")
    
    approved = len(errors) == 0
    ltv_limit_str = f"{ltv_limit*100:.0f}%"
    
    return approved, max_eligible, ltv_used, errors, ltv_limit_str

def get_llm_analysis(asset_type, params):
    try:
        prompt = f"""Analyze this {asset_type} against RBI regulations:
- Asset Value: ₹{params.get('asset_value', 0):,}
- Loan Amount: ₹{params.get('loan_amount', 0):,}
- LTV Used: {params.get('ltv_used', 0):.1f}%

Provide RBI guidelines, compliance status, and recommendations."""
        
        response = client.chat.completions.create(
            model="sonar",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}. Ensure PERPLEXITY_API_KEY is set."

# UI
st.markdown("# 🏦 Loan Against Asset Checker")
st.markdown("#### RBI-compliant asset-backed lending with AI-powered guidance")
st.markdown("---")

if "results_tab" not in st.session_state:
    st.session_state.results_tab = False

with st.sidebar:
    asset_type = st.selectbox("Asset Type", ["Gold Loan", "Property Mortgage", "Share Pledge"])

if not st.session_state.results_tab:
    col1, col2 = st.columns(2)
    
    if asset_type == "Gold Loan":
        with col1:
            st.markdown("### 📋 Enter Details")
            asset_value = st.number_input("Asset Value (₹)", 0, step=10000, value=100000)
            loan_amount = st.number_input("Loan Amount (₹)", 0, step=10000, value=75000)
            location = st.radio("Location", ["Urban", "Rural"])
            purity = st.slider("Gold Purity (Carats)", 14, 24, 22)
            
            if st.button("🔍 Submit for Validation", use_container_width=True):
                approved, max_eligible, ltv_used, errors, ltv_limit = validate_gold(asset_value, loan_amount, location, purity)
                st.session_state.asset_type = asset_type
                st.session_state.approved = approved
                st.session_state.max_eligible = max_eligible
                st.session_state.ltv_used = ltv_used
                st.session_state.errors = errors
                st.session_state.ltv_limit = ltv_limit
                st.session_state.params = {'asset_value': asset_value, 'loan_amount': loan_amount, 'location': location, 'purity': purity, 'ltv_used': ltv_used}
                st.session_state.results_tab = True
                st.rerun()
    
    elif asset_type == "Property Mortgage":
        with col1:
            st.markdown("### 📋 Enter Details")
            asset_value = st.number_input("Property Value (₹)", 0, step=100000, value=5000000)
            loan_amount = st.number_input("Loan Amount (₹)", 0, step=100000, value=3000000)
            circle_rate = st.number_input("Circle Rate (₹)", 0, step=100000, value=4500000)
            
            if st.button("🔍 Submit for Validation", use_container_width=True):
                approved, max_eligible, ltv_used, errors, ltv_limit = validate_property(asset_value, loan_amount, circle_rate)
                st.session_state.asset_type = asset_type
                st.session_state.approved = approved
                st.session_state.max_eligible = max_eligible
                st.session_state.ltv_used = ltv_used
                st.session_state.errors = errors
                st.session_state.ltv_limit = ltv_limit
                st.session_state.params = {'asset_value': asset_value, 'loan_amount': loan_amount, 'circle_rate': circle_rate, 'ltv_used': ltv_used}
                st.session_state.results_tab = True
                st.rerun()
    
    else:
        with col1:
            st.markdown("### 📋 Enter Details")
            asset_value = st.number_input("Portfolio Value (₹)", 0, step=10000, value=100000)
            loan_amount = st.number_input("Loan Amount (₹)", 0, step=10000, value=50000)
            share_index = st.selectbox("Share Index", ["NIFTY50", "NIFTY100", "Other"])
            
            if st.button("🔍 Submit for Validation", use_container_width=True):
                approved, max_eligible, ltv_used, errors, ltv_limit = validate_shares(asset_value, loan_amount, share_index)
                st.session_state.asset_type = asset_type
                st.session_state.approved = approved
                st.session_state.max_eligible = max_eligible
                st.session_state.ltv_used = ltv_used
                st.session_state.errors = errors
                st.session_state.ltv_limit = ltv_limit
                st.session_state.params = {'asset_value': asset_value, 'loan_amount': loan_amount, 'share_index': share_index, 'ltv_used': ltv_used}
                st.session_state.results_tab = True
                st.rerun()

else:
    st.markdown("### ✅ Validation Results")
    st.markdown("---")
    
    if st.button("← Back", use_container_width=True):
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
        
        ltv_val = float(st.session_state.ltv_used)
        ltv_limit_num = float(st.session_state.ltv_limit.strip('%'))
        ltv_ratio = min(ltv_val / ltv_limit_num, 1.0)
        st.progress(ltv_ratio, text=f"LTV: {st.session_state.ltv_used:.1f}% of {st.session_state.ltv_limit}")
        
        if st.session_state.errors:
            with st.expander("⚠️ RBI Violations", expanded=True):
                for error in st.session_state.errors:
                    st.warning(f"• {error}")
    
    with col2:
        st.markdown("#### Input Parameters")
        for key, value in st.session_state.params.items():
            if key != 'ltv_used':
                st.info(f"**{key.replace('_', ' ').title()}**: {value}")
    
    st.markdown("---")
    st.markdown("#### 🤖 AI Analysis")
    with st.spinner("Analyzing..."):
        llm_response = get_llm_analysis(st.session_state.asset_type, st.session_state.params)
    with st.expander("📜 Full Analysis", expanded=True):
        st.markdown(llm_response)

st.markdown(f"---")
st.markdown(f"Built with 🧡 by Ankit Saxena · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
