import streamlit as st
from datetime import datetime
import os
from openai import OpenAI

st.set_page_config(page_title="LAA Checker", page_icon="🏠", layout="wide")

# Initialize OpenAI client for Perplexity API
client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY", ""),
    base_url="https://api.perplexity.ai"
)

RBI_RULES = {
    'gold': {'urban_ltv': 0.75, 'rural_ltv': 0.90, 'min_purity': 18, 'max_amount': 2000000},
    'property': {'standard_ltv': 0.60, 'max_ltv': 0.70, 'circle_rate_threshold': 0.90},
    'shares': {'ltv': 0.50, 'eligible_indices': ['NIFTY50']}
}

def validate_gold(value, loan_amount, location, purity):
    rules = RBI_RULES['gold']
    errors = []
    if purity < rules['min_purity']:
        errors.append(f"Purity < {rules['min_purity']}k")
    ltv_limit = rules['urban_ltv'] if location == 'Urban' else rules['rural_ltv']
    if value > 0:
        if loan_amount / value > ltv_limit:
            errors.append(f"LTV exceeds {ltv_limit*100:.0f}%")
        if loan_amount > rules['max_amount']:
            errors.append(f"Loan exceeds max")
    approved = len(errors) == 0
    max_eligible = value * ltv_limit if value > 0 else 0
    ltv_used = (loan_amount / value * 100) if value > 0 else 0
    return approved, max_eligible, ltv_used, errors, f"{ltv_limit*100:.0f}%"

def validate_property(value, loan_amount, circle_rate):
    rules = RBI_RULES['property']
    errors = []
    if circle_rate > 0 and circle_rate < (value * rules['circle_rate_threshold']):
        errors.append("Circle rate < 90% of property")
    if value > 0 and loan_amount / value > rules['max_ltv']:
        errors.append("LTV exceeds 70%")
    approved = len(errors) == 0
    max_eligible = value * rules['standard_ltv'] if value > 0 else 0
    ltv_used = (loan_amount / value * 100) if value > 0 else 0
    return approved, max_eligible, ltv_used, errors, "60%"

def validate_shares(value, loan_amount, share_index):
    rules = RBI_RULES['shares']
    errors = []
    if share_index not in rules['eligible_indices']:
        errors.append(f"Only {rules['eligible_indices']} eligible")
    if value > 0 and loan_amount / value > rules['ltv']:
        errors.append("LTV exceeds 50%")
    approved = len(errors) == 0
    max_eligible = value * rules['ltv'] if value > 0 else 0
    ltv_used = (loan_amount / value * 100) if value > 0 else 0
    return approved, max_eligible, ltv_used, errors, "50%"

def get_llm_analysis(asset_type, params):
    """Get comprehensive RBI analysis from Perplexity API"""
    try:
        if asset_type == "Gold Loan":
            prompt = f"""As an RBI banking compliance expert, analyze this Gold Loan LAA request:
- Asset Value: {params['asset_value']}
- Loan Amount: {params['loan_amount']}
- Location: {params['location']}
- Gold Purity: {params['purity']} carats
- LTV Ratio: {params['ltv_used']:.1f}%

Provide comprehensive analysis:
1. **RBI Rules & Citations**: Reference specific RBI guidelines and circular numbers
2. **Eligibility Assessment**: Approved/Rejected with detailed reasoning
3. **Compliance Warnings**: Risk factors and non-compliance issues
4. **Recommendations**: Actionable steps for applicant
5. **Latest Updates**: Recent RBI circulars 2024-2025"""
        
        elif asset_type == "Property Mortgage":
            prompt = f"""As an RBI banking compliance expert, analyze this Property Mortgage LAA request:
- Property Value: {params['asset_value']}
- Loan Amount: {params['loan_amount']}
- Circle Rate: {params['circle_rate']}
- Circle Rate % of Value: {(params['circle_rate']/params['asset_value']*100):.1f}%
- LTV Ratio: {params['ltv_used']:.1f}%

Provide comprehensive analysis:
1. **RBI Rules & Citations**: Reference specific RBI guidelines and circular numbers
2. **Eligibility Assessment**: Approved/Rejected with detailed reasoning
3. **Compliance Warnings**: Documentation and valuation risk factors
4. **Recommendations**: Actionable steps for applicant
5. **Latest Updates**: Recent RBI circulars 2024-2025"""
        
        else:  # Share Pledge
            prompt = f"""As an RBI banking compliance expert, analyze this Share Pledge LAA request:
- Portfolio Value: {params['asset_value']}
- Loan Amount: {params['loan_amount']}
- Share Index: {params['share_index']}
- LTV Ratio: {params['ltv_used']:.1f}%

Provide comprehensive analysis:
1. **RBI Rules & Citations**: Reference specific RBI guidelines and circular numbers
2. **Eligibility Assessment**: Approved/Rejected with detailed reasoning
3. **Compliance Warnings**: Market and concentration risk factors
4. **Recommendations**: Actionable steps for applicant
5. **Latest Updates**: Recent RBI circulars 2024-2025"""
        
        response = client.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are an expert RBI banking compliance advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ API Error: {str(e)}\n\nNote: Set PERPLEXITY_API_KEY for LLM analysis."

st.markdown("# 🏠 LAA Eligibility Checker")
st.markdown("### RBI-Compliant Asset Valuation with AI-Powered Analysis")
st.markdown("---")

if "results_tab" not in st.session_state:
    st.session_state.results_tab = False

with st.sidebar:
    asset_type = st.selectbox("Asset Type", ["Gold Loan", "Property Mortgage", "Share Pledge"])

if not st.session_state.results_tab:
    col1, col2 = st.columns(2)
    
    if asset_type == "Gold Loan":
        with col1:
            st.subheader("📋 Enter Details")
            asset_value = st.number_input("Asset Value (₹)", min_value=0, step=10000, value=100000)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=10000, value=75000)
            location = st.radio("Location", ["Urban", "Rural"])
            purity = st.slider("Gold Purity (Carats)", 14, 24, 22)
            
            if st.button("🔍 Submit for Validation & AI Analysis", key="gold_submit", use_container_width=True):
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
            st.subheader("📋 Enter Details")
            asset_value = st.number_input("Property Value (₹)", min_value=0, step=100000, value=5000000)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=100000, value=3000000)
            circle_rate = st.number_input("Circle Rate (₹)", min_value=0, step=100000, value=4500000)
            
            if st.button("🔍 Submit for Validation & AI Analysis", key="prop_submit", use_container_width=True):
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
            st.subheader("📋 Enter Details")
            asset_value = st.number_input("Portfolio Value (₹)", min_value=0, step=10000, value=100000)
            loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=10000, value=50000)
            share_index = st.selectbox("Share Index", ["NIFTY50", "NIFTY100", "Other"])
            
            if st.button("🔍 Submit for Validation & AI Analysis", key="shares_submit", use_container_width=True):
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
    st.markdown("### ✅ Validation Results & RBI Compliance Analysis")
    st.markdown("---")
    
    if st.button("← Back to Input", use_container_width=True):
        st.session_state.results_tab = False
        st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quick Summary")
        if st.session_state.approved:
            st.success("✅ APPROVED")
        else:
            st.error("❌ REJECTED")
        st.metric("Max Eligible", f"₹{int(st.session_state.max_eligible):,}")
        st.metric("LTV Used", f"{st.session_state.ltv_used:.1f}%")
        st.metric("LTV Limit", st.session_state.ltv_limit)
        
        if st.session_state.errors:
            st.warning("⚠️ Issues Found:")
            for error in st.session_state.errors:
                st.warning(f"• {error}")
    
    with col2:
        st.subheader("Input Parameters")
        for key, value in st.session_state.params.items():
            if key != 'ltv_used':
                st.info(f"**{key.title()}**: {value}")
    
    st.markdown("---")
    st.markdown("### 🤖 AI-Powered RBI Compliance Analysis")
    st.markdown("*Fetching latest RBI guidelines via Perplexity API*")
    
    with st.spinner("Analyzing parameters against RBI guidelines..."):
        llm_response = get_llm_analysis(st.session_state.asset_type, st.session_state.params)
        st.markdown(llm_response)
    
    st.markdown("---")
    st.markdown("Built with Streamlit | RBI Compliant | Made by Ank576 | " + datetime.now().strftime("%Y-%m-%d %H:%M"))
