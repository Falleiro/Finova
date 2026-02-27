"""
Sets dummy environment variables before any test module is imported,
so that src.config.Settings() doesn't raise RuntimeError during collection.
"""

import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-bot-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "123456789")
os.environ.setdefault("OPEN_FINANCE_CLIENT_ID", "test-client-id")
os.environ.setdefault("OPEN_FINANCE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("OPEN_FINANCE_BASE_URL", "https://api.pluggy.ai")
os.environ.setdefault("PLUGGY_ITEM_ID_MEU_PLUGGY", "test-item-id")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_finova.db")
