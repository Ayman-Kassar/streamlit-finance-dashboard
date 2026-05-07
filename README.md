# AI-Powered Finance Dashboard

A full-stack finance dashboard built with Streamlit and Claude API.
Live demo: https://heroic-taffy-e975b1.netlify.app

## 🎯 Business Problem
Finance teams spend hours manually writing variance commentary and switching 
between tools. This dashboard puts AI analysis one click away — inside 
a live data application.

## ✨ Features
- 10,000 rows of car sales data — real-time filtering by market and channel
- Scenario analysis — Normal, Optimistic (+20%), Pessimistic (-20%)
- 3 AI commentary styles — Executive, Detailed, Action-focused
- Multi-turn chat — ask follow-up questions about the data
- PDF export — one-click professional report download
- Powered by Claude Sonnet API

## 🛠️ Tools
- Streamlit — web application framework
- Claude API (Anthropic) — AI commentary and chat
- Pandas — data processing
- Plotly — interactive charts
- fpdf2 — PDF generation
- Python 3.12

## 🚀 How to Run
```bash
git clone https://github.com/Ayman-Kassar/streamlit-finance-dashboard
cd streamlit-finance-dashboard
pip install streamlit anthropic pandas plotly openpyxl fpdf2 python-dotenv
cp .env.example .env  # add your ANTHROPIC_API_KEY
streamlit run app.py
```

## 💼 Portfolio Context
Demonstrates full-stack AI application development for finance — 
from data processing to AI integration to user interface to PDF export.
