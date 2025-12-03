# 🏠 Loan Against Asset (LAA) Eligibility Checker

[![Vercel](https://img.shields.io/badge/Deploy-Vercel-blue?logo=vercel)](https://vercel.com/new/clone?repository-url=https://github.com/Ank576/loan-against-asset-checker)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)

RBI-compliant **Loan Against Asset (LAA) Eligibility Checker** web app. Evaluates gold, property & share collateral with LTV ratios, Perplexity API for real-time RBI citations, and rule-based approval logic.

## 🚀 Live Demo

**[https://laa-checker-ank576.vercel.app](https://laa-checker-ank576.vercel.app)** _(Deploy coming soon)_

## 📋 Features

✅ **Multi-Asset Support**
- Gold Loan (Urban/Rural LTV: 75%/90%)
- Property Mortgage (LTV: 50-70% via circle rate)
- Share Pledge (LTV: 50% for Nifty 50)

✅ **RBI Compliance**
- Gold Loan Directions 2023 (Para 7.2)
- Property Mortgage Registry Act
- Nifty 50 liquid share validation

✅ **Real-time Regulations**
- Perplexity API for latest RBI circulars (₹0.20/query)
- Auto-updated rate limits & LTV thresholds
- Direct citations to RBI Master Directions

✅ **LLM-Powered**
- Dynamic rule engine based on RBI norms
- Real-time eligibility scoring
- PDF report generation

✅ **Full Stack**
- Next.js 15 (frontend + backend)
- Chart.js for LTV visualization
- Deployed on Vercel

## 🛠️ Tech Stack

```
Frontend:  React 19 + TypeScript + Tailwind CSS
Backend:   Next.js API Routes + Node.js
LLM:       Perplexity API (OpenAI-compatible)
Database:  Stateless (localStorage for UI)
Deploy:    Vercel + GitHub Actions
```

## 📦 Installation

### Clone Repository

```bash
git clone https://github.com/Ank576/loan-against-asset-checker.git
cd loan-against-asset-checker
```

### Setup Environment

```bash
npm install

# Create .env.local
echo 'NEXT_PUBLIC_PERPLEXITY_API_KEY=your_key_here' > .env.local
```

### Get Perplexity API Key

1. Sign up: [https://www.perplexity.ai/](https://www.perplexity.ai/)
2. Go to Settings → API → Generate Key
3. Add billing ($5+ initial credit)
4. Copy key to `.env.local`

## 🚀 Quick Start

```bash
# Development
npm run dev
open http://localhost:3000

# Production Build
npm run build
npm start

# Deploy to Vercel
vercel --prod
```

# Streamlit Web App (Alternative UI)

```bash
# Install Streamlit
pip install -r requirements.txt

# Run locally
streamlit run streamlit_app.py

# Open in browser
# http://localhost:8501
```

**Deploy to Streamlit Cloud:**
1. Push code to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Click "New app" → Select your repository
4. Choose branch: `main` → File path: `streamlit_app.py`
5. App will deploy automatically

## 📁 Project Structure

```
loan-against-asset-checker/
├── app/
│   ├── page.tsx           # Main LAA form UI
│   ├── layout.tsx         # App shell
│   └── api/
│       └── laa-check.ts   # Rule engine + Perplexity
├── components/
│   ├── AssetForm.tsx      # Gold/Property/Share selector
│   ├── ResultsCard.tsx    # Approve/Reject display
│   └── LTVChart.tsx       # Chart.js visualization
├── utils/
│   ├── rbi-rules.ts       # RBI LTV tables
│   ├── validator.ts       # Eligibility logic
│   └── perplexity.ts      # API wrapper
├── public/
│   └── rbi-circulars/     # PDF backups (2023-2025)
└── package.json
```

## 💻 Core API Endpoint

### POST `/api/laa-check`

```json
{
  "assetType": "gold",
  "value": 1000000,
  "loanAmount": 750000,
  "location": "urban",
  "purity": 22,
  "circleRate": 900000
}
```

**Response:**

```json
{
  "approved": true,
  "maxEligible": "₹7,50,000",
  "ltvUsed": "75.0%",
  "ltvLimit": "75%",
  "rbiRefs": ["RBI Gold Loan Directions 2023 - Para 7.2"],
  "perplexityUpdate": {
    "query": "Latest RBI gold loan LTV limits Dec 2025",
    "costUSD": 0.0015
  }
}
```

## 🎯 RBI Eligibility Rules

### Gold Loan

| Parameter | Rule | Source |
|-----------|------|--------|
| Urban LTV | 75% | RBI Gold Loan 2023 |
| Rural LTV | 90% | RBI Gold Loan 2023 |
| Purity | ≥18k | BIS Standards |
| Max Amount | ₹20L | RBI Master Direction |

### Property Mortgage

| Parameter | Rule | Source |
|-----------|------|--------|
| Standard LTV | 60% | RBI Lending Norms |
| Min LTV | 50% | Conservative banks |
| Circle Rate Check | ≥90% of property value | RERA Rules |

### Share Pledge

| Parameter | Rule | Source |
|-----------|------|--------|
| Eligible Stocks | Nifty 50 only | SEBI P2P |
| LTV | 50% | Margin Trading Rules |
| Liquidity | >₹1Cr daily volume | NSE Standards |

## 📊 Usage Example

```typescript
// Frontend
const response = await fetch('/api/laa-check', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    assetType: 'gold',
    value: 1000000,
    loanAmount: 750000,
    location: 'urban',
    purity: 22
  })
});

const { approved, maxEligible } = await response.json();
```

## 💰 Pricing

- **Perplexity API**: ₹0.15-0.20/query
- **Vercel Free Tier**: 100k serverless function invocations/month
- **Monthly Cost**: ~₹300-500 (10k queries)

## 🧪 Testing

```bash
# Run unit tests
npm run test

# Test API endpoint
curl -X POST http://localhost:3000/api/laa-check \
  -H "Content-Type: application/json" \
  -d '{"assetType":"gold","value":1000000,"loanAmount":750000}'
```

## 🌐 Deployment

### Option 1: Vercel (Recommended)

```bash
vercel --prod
# Follow prompts to link GitHub repo
```

### Option 2: Docker

```bash
docker build -t laa-checker .
docker run -p 3000:3000 -e NEXT_PUBLIC_PERPLEXITY_API_KEY=xxx laa-checker
```

## 📚 RBI References

- [RBI Gold Loan Directions 2023](https://rbi.org.in/Scripts/NotificationUser.aspx?Id=12345)
- [RBI Master Direction on Lending](https://rbi.org.in/Scripts/)
- [Mortgage Registry Act 2022](https://www.toppr.com/bytes/mortgage-registry-act/)
- [SEBI P2P Lending Rules](https://www.sebi.gov.in/regulations/peer-to-peer-lending.html)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork this repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file

## 👤 Author

**Ankit** | Product Manager | FinTech Enthusiast
- GitHub: [@Ank576](https://github.com/Ank576)
- Portfolio: [ank576.dev](https://ank576.dev)

## ⭐ Show Your Support

Give a ⭐ if this project helped you! Share your feedback via issues.

---

**Portfolio Project** | Built for fintech PM portfolio | LLM + RBI Compliance Showcase
