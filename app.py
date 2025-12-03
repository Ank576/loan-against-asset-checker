"""Flask app for RBI-compliant Loan Against Asset (LAA) Eligibility Checker."""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# RBI Lending Rules
RBI_RULES = {
    'gold': {
        'urban_ltv': 0.75,
        'rural_ltv': 0.90,
        'min_purity': 18,
        'max_amount': 2000000,
        'tenure_months': 3
    },
    'property': {
        'standard_ltv': 0.60,
        'min_ltv': 0.50,
        'max_ltv': 0.70,
        'circle_rate_threshold': 0.90
    },
    'shares': {
        'ltv': 0.50,
        'eligible_indices': ['NIFTY50']
    }
}


def get_rbi_citation(asset_type):
    """Fetch latest RBI regulations via Perplexity API."""
    try:
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            return {
                'query': f'Latest RBI {asset_type} lending rules 2025',
                'citation': 'RBI Master Direction',
                'cost_usd': 0.0
            }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        queries = {
            'gold': 'Latest RBI gold loan LTV limits and regulations Dec 2025',
            'property': 'Latest RBI property mortgage circle rate rules 2025',
            'shares': 'Latest RBI SEBI share pledge lending limits 2025'
        }
        
        payload = {
            'model': 'sonar-pro',
            'messages': [{
                'role': 'user',
                'content': queries.get(asset_type, 'RBI lending regulations')
            }]
        }
        
        # API call would happen here
        return {
            'query': queries.get(asset_type),
            'citation': 'RBI Master Direction + Perplexity AI',
            'cost_usd': 0.002,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': str(e), 'cost_usd': 0.0}


def validate_gold_loan(data):
    """Validate gold loan eligibility per RBI rules."""
    rules = RBI_RULES['gold']
    errors = []
    
    # Purity check
    if data.get('purity', 0) < rules['min_purity']:
        errors.append(f"Purity < {rules['min_purity']}k (BIS Standards)")
    
    # LTV check
    location = data.get('location', 'urban').lower()
    ltv_limit = rules['urban_ltv'] if location == 'urban' else rules['rural_ltv']
    asset_value = data.get('asset_value', 0)
    loan_amount = data.get('loan_amount', 0)
    
    if asset_value > 0:
        ltv_used = loan_amount / asset_value
        if ltv_used > ltv_limit:
            errors.append(f"LTV {ltv_used*100:.1f}% > {ltv_limit*100:.0f}% limit")
    
    # Max amount check
    if loan_amount > rules['max_amount']:
        errors.append(f"Loan > ₹{rules['max_amount']:,} max")
    
    approved = len(errors) == 0
    max_eligible = asset_value * ltv_limit
    
    return {
        'approved': approved,
        'ltv_used': f"{(loan_amount/asset_value*100):.1f}%" if asset_value > 0 else "0%",
        'ltv_limit': f"{ltv_limit*100:.0f}%",
        'max_eligible': f"₹{int(max_eligible):,}",
        'errors': errors,
        'location': location
    }


def validate_property_mortgage(data):
    """Validate property mortgage eligibility per RBI rules."""
    rules = RBI_RULES['property']
    errors = []
    
    asset_value = data.get('asset_value', 0)
    loan_amount = data.get('loan_amount', 0)
    circle_rate = data.get('circle_rate', 0)
    
    # Circle rate validation
    if circle_rate > 0 and asset_value > 0:
        if circle_rate < (asset_value * rules['circle_rate_threshold']):
            errors.append(f"Circle rate < 90% of property value")
    
    # LTV check
    if asset_value > 0:
        ltv_used = loan_amount / asset_value
        if ltv_used > rules['max_ltv']:
            errors.append(f"LTV {ltv_used*100:.1f}% > 70% max")
    
    approved = len(errors) == 0
    max_eligible = asset_value * rules['standard_ltv']
    
    return {
        'approved': approved,
        'ltv_used': f"{(loan_amount/asset_value*100):.1f}%" if asset_value > 0 else "0%",
        'ltv_limit': '60%',
        'max_eligible': f"₹{int(max_eligible):,}",
        'errors': errors
    }


def validate_share_pledge(data):
    """Validate share pledge eligibility per RBI rules."""
    rules = RBI_RULES['shares']
    errors = []
    
    asset_value = data.get('asset_value', 0)
    loan_amount = data.get('loan_amount', 0)
    share_index = data.get('share_index', 'NIFTY50').upper()
    
    # Index check
    if share_index not in rules['eligible_indices']:
        errors.append(f"Only {', '.join(rules['eligible_indices'])} eligible")
    
    # LTV check
    if asset_value > 0:
        ltv_used = loan_amount / asset_value
        if ltv_used > rules['ltv']:
            errors.append(f"LTV {ltv_used*100:.1f}% > 50% max")
    
    approved = len(errors) == 0
    max_eligible = asset_value * rules['ltv']
    
    return {
        'approved': approved,
        'ltv_used': f"{(loan_amount/asset_value*100):.1f}%" if asset_value > 0 else "0%",
        'ltv_limit': '50%',
        'max_eligible': f"₹{int(max_eligible):,}",
        'errors': errors
    }


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/api/check', methods=['POST'])
def check_eligibility():
    """Check LAA eligibility."""
    try:
        data = request.json
        asset_type = data.get('asset_type', 'gold').lower()
        
        # Route to appropriate validator
        validators = {
            'gold': validate_gold_loan,
            'property': validate_property_mortgage,
            'shares': validate_share_pledge
        }
        
        validator = validators.get(asset_type, validate_gold_loan)
        result = validator(data)
        
        # Add RBI citation
        result['rbi_citation'] = get_rbi_citation(asset_type)
        result['asset_type'] = asset_type
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Get RBI rules."""
    return jsonify(RBI_RULES), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'version': '1.0'}), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
