---
description: Run an immediate check on all investment positions. Fires Telegram alerts for any asset currently at ±3% or more from its opening price today.
---

# Investment Alert Command

Perform an on-demand investment swing check for FINOVA.

## Pipeline

Execute the following steps in order:

1. **Use the `data-fetcher` subagent** to:
   - Fetch all investment assets in the portfolio
   - Get `current_price`, `open_price`, and calculate `daily_change_pct` for each
   - Flag assets where `abs(daily_change_pct) >= 3.0`

2. **Use the `alert-engine` subagent** to:
   - For each flagged asset, check deduplication (has this threshold been alerted today?)
   - For new alerts: produce formatted investment alert messages
   - Update the `alerts_sent` DB table for each alert produced

3. **Use the `telegram-sender` subagent** to:
   - Send each alert message individually
   - If no alerts to send → do NOT send any message (silent run)

## Deduplication

- Only alert once per threshold crossing per asset per day
- Thresholds: ±3%, ±5%, ±7%
- Reset daily at market open (09:00 Brasília)

## Expected Output

- 0 to N Telegram messages, one per triggered asset
- If no assets triggered: no messages sent, log `"Investment check: no alerts triggered"`