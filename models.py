from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Satwa(db.Model):
    __tablename__ = 'satwa'

    id = db.Column(db.Integer, primary_key=True)
    nama_satwa = db.Column(db.String(100), nullable=False, unique=True)
    nama_latin = db.Column(db.String(255)) 
    jenis_satwa = db.Column(db.String(100))
    status_satwa = db.Column(db.String(50))
    deskripsi = db.Column(db.Text)

    # relasi ke SatwaLokasi (many-to-many, cascade delete)
    lokasi_relasi = db.relationship(
        'SatwaLokasi',
        back_populates='satwa',
        cascade="all, delete-orphan"
    )

    # relasi ke SatwaGambar (cascade delete)
    gambar_relasi = db.relationship(
        'SatwaGambar',
        back_populates='satwa',
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Satwa {self.nama_satwa}>"


class SatwaGambar(db.Model):
    __tablename__ = 'satwa_gambar'
    id = db.Column(db.Integer, primary_key=True)
    satwa_id = db.Column(db.Integer, db.ForeignKey('satwa.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)

    satwa = db.relationship("Satwa", back_populates="gambar_relasi")

    def __repr__(self):
        return f"<SatwaGambar {self.filename}>"


class LokasiKonservasi(db.Model):
    __tablename__ = 'lokasi_konservasi'
    id = db.Column(db.Integer, primary_key=True)
    nama_lokasi = db.Column(db.String(100), nullable=False, unique=True)
    deskripsi = db.Column(db.Text)
    gambar = db.Column(db.String(200))
    kategori = db.Column(db.String(50))

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    geom = db.Column(Geometry(geometry_type="POINT", srid=4326))

    # relasi ke SatwaLokasi (cascade delete)
    satwa_relasi = db.relationship(
        'SatwaLokasi',
        back_populates='lokasi',
        cascade="all, delete-orphan"
    )
    
    gambar_relasi = db.relationship(
        'LokasiGambar',
        back_populates='lokasi',
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LokasiKonservasi {self.nama_lokasi}>"
    
    
    class LokasiGambar(db.Model):
        __tablename__ = 'lokasi_gambar'

        id = db.Column(db.Integer, primary_key=True)
        lokasi_id = db.Column(db.Integer, db.ForeignKey('lokasi_konservasi.id'), nullable=False)
        filename = db.Column(db.String(200), nullable=False)

        lokasi = db.relationship("LokasiKonservasi", back_populates="gambar_relasi")

        def __repr__(self):
            return f"<LokasiGambar {self.filename}>"



class SatwaLokasi(db.Model):
    __tablename__ = 'satwa_lokasi'
    id = db.Column(db.Integer, primary_key=True)
    satwa_id = db.Column(db.Integer, db.ForeignKey('satwa.id'), nullable=False)
    lokasi_id = db.Column(db.Integer, db.ForeignKey('lokasi_konservasi.id'), nullable=False)

    satwa = db.relationship('Satwa', back_populates='lokasi_relasi')
    lokasi = db.relationship('LokasiKonservasi', back_populates='satwa_relasi')

    def __repr__(self):
        return f"<SatwaLokasi satwa_id={self.satwa_id} lokasi_id={self.lokasi_id}>"
