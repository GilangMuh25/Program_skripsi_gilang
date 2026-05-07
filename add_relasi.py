from app import app, db
from models import SatwaLokasi

with app.app_context():
    lokasi_id = 18
    satwa_ids = [15, 26, 35, 66, 69]
    for sid in satwa_ids:
        relasi = SatwaLokasi(satwa_id=sid, lokasi_id=lokasi_id)
        db.session.add(relasi)
    db.session.commit()
    print("Relasi berhasil ditambahkan!")