# Wafir Core V14

This release advances the Wafir core without replacing the stable UI baseline.

- Branch registry with a current-branch setting.
- Inventory lots with expiry-aware FEFO allocation.
- Expired lots are excluded from sale; when lot tracking exists and no valid lot remains, sale is blocked.
- Sales store the exact lot consumption in `sale_item_lots`.
- Returns/cancellations restore the exact consumed lot quantities.
- COGS uses recorded lot unit costs when available.
- Purchases create traceable inventory lots.
- Operational audit helper is available for cross-module events.

The existing login, theme system, POS layout, invoice preview, action icons, and accounting migrations are preserved as the baseline.
