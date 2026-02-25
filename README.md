# 🏠 PocketRent

🚀 <a href="https://pocketrent.streamlit.app/" target="_blank" rel="noopener noreferrer">Live App</a>

👉 https://pocketrent.streamlit.app/

**Your pocket guide to UK rent prices**

Ask questions about UK rent in plain English. Compare areas, find the cheapest spots, search by budget.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![Data](https://img.shields.io/badge/Data-ONS%20Official-green)

---

## ✨ What You Can Ask

```
"Compare Manchester vs Liverpool vs Leeds"
→ Side-by-side rent comparison with rankings

"Cheapest 2-bed in North West"
→ Top 5 most affordable areas in the region

"Areas under £700/month"
→ All areas within your budget

"How much is rent in Oxford?"
→ Full breakdown (1-4 bed) with UK average comparison
```

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

Open http://localhost:8501

**No API keys. No setup. Just works.**

---

## 💬 Example Queries

| Query | What You Get |
|-------|--------------|
| `Manchester vs Liverpool` | Comparison table, ranked by price |
| `Cheapest 1-bed in UK` | Top 10 most affordable areas |
| `2-bed under £1000 in South East` | Areas matching your budget + region |
| `Most expensive areas` | Top 10 priciest locations |
| `Rent in Birmingham` | Full price breakdown for area |

---

## 📊 Data

- **Source:** ONS Private Rental Market Statistics
- **Coverage:** 348 UK areas
- **Includes:** All major cities, London boroughs, regions
- **Updated:** Monthly by ONS

### To Update Data

1. Download latest from [ONS](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics)
2. Replace `data/rent_data.xlsx`
3. Restart app

---

## 🗺️ Regions Covered

| Region | Examples |
|--------|----------|
| **London** | All 33 boroughs |
| **North West** | Manchester, Liverpool, Preston |
| **North East** | Newcastle, Sunderland, Durham |
| **Yorkshire** | Leeds, Sheffield, York, Hull |
| **West Midlands** | Birmingham, Coventry, Wolverhampton |
| **East Midlands** | Nottingham, Derby, Leicester |
| **South West** | Bristol, Bath, Exeter, Plymouth |
| **South East** | Oxford, Brighton, Reading, Southampton |
| **East of England** | Cambridge, Norwich, Ipswich |
| **Wales** | Cardiff, Swansea, Newport |
| **Scotland** | Edinburgh, Glasgow, Aberdeen |

---

## 📁 Project Structure

```
pocketrent/
├── app.py              # Streamlit chat interface
├── rent_data.py        # Data loading & queries
├── query_handler.py    # Natural language parsing
├── requirements.txt
├── README.md
└── data/
    └── rent_data.xlsx  # ONS rent data (update monthly)
```

---

## 🔧 Technical Highlights

- **Zero external APIs** - All data local, no network dependencies
- **Natural language parsing** - Regex-based, fast and reliable
- **348 areas** - Comprehensive UK coverage
- **Official data** - ONS government statistics

---

## 📜 License

MIT License - Free to use and modify

---

**Built by Ojey** • [Portfolio](https://github.com/ojey) • AI Developer
