---
description: Generate and send the full monthly financial report including spending breakdown, charts, investment performance, and personalized insights.
---

# Monthly Report Command

Run the full monthly financial report pipeline for FINOVA.

## Pipeline

Execute the following steps in order:

1. **Use the `data-fetcher` subagent** to:
   - Fetch all transactions from the previous calendar month
   - Fetch investment portfolio performance for the previous month
   - Fetch income records for the previous month
   - Compare with the month before that (for trend analysis)

2. **Use the `report-builder` subagent** to:
   - Generate the monthly report text (income vs spending, top 5 expenses, category comparison, investment summary, personalized insight)
   - Generate the **pie chart** (spending by category) → save as PNG
   - Generate the **line chart** (daily spending trend) → save as PNG

3. **Use the `telegram-sender` subagent** to:
   - Send the formatted report text
   - Send the pie chart image with caption: `"📊 Spending breakdown — [Month Year]"`
   - Send the line chart image with caption: `"📅 Daily spending trend — [Month Year]"`
   - Confirm all 3 messages delivered
   - Trigger deletion of PNG files after confirmation

## Error Handling

- If charts fail to generate → send report text only, with note: `"⚠️ Charts couldn't be generated this time."`
- If any send fails → retry up to 3 times
- Log all outcomes

## Expected Output

3 Telegram messages: 1 text report + 2 chart images.