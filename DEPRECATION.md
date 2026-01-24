Deprecated files removed on 2026-01-24

Backups (kept in repo):
- deprecated/analytics/news_engine.py  — former analytics.news_engine
- deprecated/analytics/signal_scoring.py — former analytics.signal_scoring
- deprecated/notifications/news_notifier.py — former notifications.news_notifier
- deprecated/strategy/structure_filters.py — former strategy.structure_filters (empty)
- deprecated/risk/atr_sl_tp.py — former risk.atr_sl_tp

Notes:
- Originals were replaced with ImportError stubs in their original locations to make failures explicit if code still imports them.
- To restore a backed-up module, move it from `deprecated/` back to its original path and remove the ImportError stub.
- If you want, I can create a Git commit and open a PR with these changes, or permanently delete the original files and remove the stubs. Let me know which you'd prefer.