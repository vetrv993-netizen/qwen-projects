# Wafir V15 — Operations & Reporting

V15 extends the existing Wafir core without changing the stable POS/CRUD/theme architecture.

## Added
- Customer statements and supplier statements.
- Statement export to CSV.
- Expiring-lot report with configurable horizon.
- Low-stock report.
- Audit/activity report.
- Reports workspace organized as tabs.

## Design rule
No business transaction is duplicated in reports. Reports query the authoritative operational tables and the existing accounting ledger.
