# Financial Coach — Working Memory (`memory.md`)

## 📊 Active Financial & Portfolio Queue
- [ ] Complete initial financial goals & risk-profile onboarding with Callie.
- [ ] Optional: Configure Robinhood read/trade credentials if brokerage integration is desired (`~/Agents/Agent 0/mcp/robinhood/auth_flow.py`).

---

## ⚡ Fast Paths & Command Cache
- **Refresh Ken French 5-Factor CSV Library:**
  `~/Agents/Agent 0/.venv/bin/python ~/Agents/Financial_Coach/scripts/sync_factor_library.py`
- **Local Factor Datasets (`~/Agents/Financial_Coach/data/`):**
  - `F-F_Research_Data_5_Factors_2x3.csv` (Monthly)
  - `F-F_Research_Data_5_Factors_2x3_daily.csv` (Daily)

---

## 🔗 Neural Pathways
- **Major Financial Deadlines → Agent 0:** Tax deadlines, tuition/scholarship dates, or recurring financial review reminders should be routed to `~/Agents/Agent 0` for calendar scheduling.
