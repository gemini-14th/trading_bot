from db.database import engine

try:
    conn = engine.connect()
    print("✅ PostgreSQL connected")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
