from app import app, db
from models import LokasiKonservasi

gambar_data = {
    "CA Besowo Gadungan": "ca_besowo_gadungan.png",
    "CA Ceding": "ca_ceding.png",
    "CA CMS": "ca_cms.png",
    "SM Bawean": "sm_bawean.png",
    "SM Dt Yang": "sm_dt_yang.png",
    "SM Nusa Barong": "sm_nusa_barong.png",
    "TWA Gunung Baung": "twa_gunung_baung.png",
    "TWA Ijen": "twa_ijen.png",
    "TWA Tretes": "twa_tretes.png",
    "CA Noko dan Nusa": "ca_noko_nusa.png",
    "CA Goa Nglirip": "ca_goa_nglirip.png",
    "CA Kawah Ijen Merapi Ungup-Ungup": "ca_ijen.png",
    "CA Manggis Gadungan": "ca_manggis_gadungan.png",
    "CA Picis": "ca_picis.png",
    "CA Sempu": "ca_sempu.png",
    "CA Bawean": "ca_bawean.png",
    "CA Sigogor": "ca_sigogor.png",
    "CA Saobi": "ca_saobi.png",
    "CA Abang": "ca_abang.png",
    "CA Sungai Kolbu": "ca_sungai_kolbu.png",
    "CA Watangan Puger": "ca_watangan_puger.png",
    "CA Janggangan Rogojampi": "ca_janggangan_rogojampi.png",
    "CA Pancur Ijen I-II": "ca_pancur_ijen_I-II.png"

}

with app.app_context():

    for nama_lokasi, nama_file in gambar_data.items():
        lokasi = LokasiKonservasi.query.filter_by(nama_lokasi=nama_lokasi).first()
        if lokasi:
            lokasi.gambar = nama_file
            print(f"✔ Gambar ditambahkan untuk: {nama_lokasi}")
        else:
            print(f"⚠ Lokasi tidak ditemukan: {nama_lokasi}")

    db.session.commit()
    print("✅ Semua gambar berhasil dimasukkan.")