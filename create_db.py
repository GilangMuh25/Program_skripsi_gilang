from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # 1. Aktifkan ekstensi PostGIS
        print("Sedang mengaktifkan PostGIS...")
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        db.session.commit()
        
        # 2. Buat tabel-tabel database
        print("Sedang membuat tabel...")
        db.create_all()
        
        print("Berhasil! PostGIS aktif dan semua tabel telah dibuat.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")