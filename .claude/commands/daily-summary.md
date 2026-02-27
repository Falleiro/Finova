---
description: Generate and send the daily financial summary to Telegram. Fetches yesterday's transactions, current balances, and upcoming bills, then formats and sends the morning briefing.
---

# Daily Summary Command

Run the daily financial summary pipeline for FINOVA.

## Pipeline

Execute the following steps in order:

1. **Use the `data-fetcher` subagent** to:
   - Fetch all account balances (current)
   - Fetch transactions from the last 24 hours
   - Fetch upcoming scheduled payments (next 3 days)
   - Store/update results in the local DB

2. **Use the `report-builder` subagent** to:
   - Generate the daily summary text using the data from step 1
   - Include: yesterday's spending by category, current balances, upcoming bills, budget health status

3. **Use the `telegram-sender` subagent** to:
   - Send the formatted daily summary message
   - Confirm delivery

## Error Handling

- If data-fetcher fails → send a fallback message: `"⚠️ I couldn't fetch your latest data. I'll retry in a few minutes."`
- If report-builder fails → log error and skip sending for this cycle
- If telegram-sender fails → retry up to 3 times with 5s delay

## Expected Output

A single Telegram message delivered to `TELEGRAM_CHAT_ID` before 8:10 AM.