import streamlit as st
from datetime import datetime

st.set_page_config(page_title="LAA Checker", page_icon="🏠", layout="wide")

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

st.markdown("# 🏠 LAA Eligibility Checker")
st.markdown("### RBI-Compliant Asset Valuation")
st.markdown("---")

with st.sidebar:
    asset_type = st.selectbox("Asset Type", ["Gold Loan", "Property Mortgage", "Share Pledge"])

col1, col2 = st.columns(2)

if asset_type == "Gold Loan":
    with col1:
        asset_value = st.number_input("Asset Value (₹)", min_value=0, step=10000, value=100000)
        loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=10000, value=75000)
        location = st.radio("Location", ["Urban", "Rural"])
        purity = st.slider("Gold Purity (Carats)", 14, 24, 22)
        approved, max_eligible, ltv_used, errors, ltv_limit = validate_gold(asset_value, loan_amount, location, purity)
    with col2:
        st.subheader("Result")
        if approved:
            st.success("✅ APPROVED")
        else:
            st.error("❌ REJECTED")
        st.metric("Max Eligible", f"₹{int(max_eligible):,}")
        st.metric("LTV Used", f"{ltv_used:.1f}%")
        for error in errors:
            st.warning(error)

elif asset_type == "Property Mortgage":
    with col1:
        asset_value = st.number_input("Property Value (₹)", min_value=0, step=100000, value=5000000)
        loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=100000, value=3000000)
        circle_rate = st.number_input("Circle Rate (₹)", min_value=0, step=100000, value=4500000)
        approved, max_eligible, ltv_used, errors, ltv_limit = validate_property(asset_value, loan_amount, circle_rate)
    with col2:
        st.subheader("Result")
        if approved:
            st.success("✅ APPROVED")
        else:
            st.error("❌ REJECTED")
        st.metric("Max Eligible", f"₹{int(max_eligible):,}")
        st.metric("LTV Used", f"{ltv_used:.1f}%")
        for error in errors:
            st.warning(error)

else:
    with col1:
        asset_value = st.number_input("Portfolio Value (₹)", min_value=0, step=10000, value=100000)
        loan_amount = st.number_input("Loan Amount (₹)", min_value=0, step=10000, value=50000)
        share_index = st.selectbox("Share Index", ["NIFTY50", "NIFTY100", "Other"])
        approved, max_eligible, ltv_used, errors, ltv_limit = validate_shares(asset_value, loan_amount, share_index)
    with col2:
        st.subheader("Result")
        if approved:
            st.success("✅ APPROVED")
        else:
            st.error("❌ REJECTED")
        st.metric("Max Eligible", f"₹{int(max_eligible):,}")
        st.metric("LTV Used", f"{ltv_used:.1f}%")
        for error in errors:
            st.warning(error)

st.markdown("---")
st.markdown("Built with Streamlit | RBI Compliant | Made by Ank576")
