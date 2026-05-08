import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from models import db, Satwa, SatwaGambar, LokasiKonservasi, SatwaLokasi

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

UPLOAD_FOLDER_SATWA = 'static/img/satwa'
UPLOAD_FOLDER_LOKASI = 'static/img/lokasi'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

for folder in [UPLOAD_FOLDER_SATWA, UPLOAD_FOLDER_LOKASI]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# =======================
# DASHBOARD
# =======================
@admin_bp.route("/dashboard")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    total_satwa = Satwa.query.count()
    total_lokasi = LokasiKonservasi.query.count()

    spesies_dilindungi = Satwa.query.filter(Satwa.status_satwa == "Dilindungi").count()
    spesies_tidak = Satwa.query.filter(Satwa.status_satwa == "Tidak Dilindungi").count()

    return render_template("dashboard.html",
                           total_satwa=total_satwa,
                           total_lokasi=total_lokasi,
                           spesies_dilindungi=spesies_dilindungi,
                           spesies_tidak=spesies_tidak)



# =======================
# SATWA CRUD
# =======================
@admin_bp.route('/satwa')
def list_satwa():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    satwa_list = Satwa.query.order_by(Satwa.id.asc()).all()
    return render_template('admin/admin_satwa.html', satwa_list=satwa_list)


@admin_bp.route('/satwa/add', methods=['GET','POST'])
def add_satwa():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    lokasi_list = LokasiKonservasi.query.order_by(LokasiKonservasi.id.asc()).all()

    if request.method == 'POST':
        nama       = request.form.get('nama')
        latin      = request.form.get('nama_latin')
        jenis      = request.form.get('jenis')
        status     = request.form.get('status_satwa')
        deskripsi  = request.form.get('deskripsi')
        lokasi_ids = request.form.getlist('lokasi_id[]')

        # ✅ Validasi kolom wajib
        if not nama or not latin or not jenis or not status or not deskripsi or not lokasi_ids:
            flash("Semua kolom wajib diisi dan minimal satu lokasi harus dipilih!", "danger")
            satwa_temp = Satwa(
                nama_satwa=nama,
                nama_latin=latin,
                jenis_satwa=jenis,
                status_satwa=status,
                deskripsi=deskripsi
            )
            return render_template('admin/admin_satwa_form.html',
                                   lokasi_list=lokasi_list,
                                   satwa=satwa_temp)

        # ✅ Cek duplikat nama satwa
        existing = Satwa.query.filter_by(nama_satwa=nama).first()
        if existing:
            flash("Nama satwa sudah ada, gunakan nama lain!", "danger")
            satwa_temp = Satwa(
                nama_satwa=nama,
                nama_latin=latin,
                jenis_satwa=jenis,
                status_satwa=status,
                deskripsi=deskripsi
            )
            return render_template('admin/admin_satwa_form.html',
                                   lokasi_list=lokasi_list,
                                   satwa=satwa_temp)

        # ✅ Simpan satwa baru
        satwa = Satwa(
            nama_satwa=nama,
            nama_latin=latin,
            jenis_satwa=jenis,
            status_satwa=status,
            deskripsi=deskripsi
        )
        db.session.add(satwa)
        db.session.commit()   # commit dulu supaya satwa.id terbentuk

        # upload banyak gambar
        files = request.files.getlist('gambar')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER_SATWA, filename)
                file.save(path)
                new_gambar = SatwaGambar(satwa_id=satwa.id, filename=filename)
                db.session.add(new_gambar)

        # simpan lokasi relasi
        for lid in lokasi_ids:
            relasi = SatwaLokasi(satwa_id=satwa.id, lokasi_id=int(lid))
            db.session.add(relasi)

        db.session.commit()
        flash("Satwa baru berhasil ditambahkan!", "success")
        return redirect(url_for('admin.list_satwa'))

    return render_template('admin/admin_satwa_form.html', lokasi_list=lokasi_list, satwa=None)


@admin_bp.route('/satwa/edit/<int:satwa_id>', methods=['GET','POST'])
def edit_satwa(satwa_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    satwa = Satwa.query.get_or_404(satwa_id)
    lokasi_list = LokasiKonservasi.query.order_by(LokasiKonservasi.id.asc()).all()

    if request.method == 'POST':
        nama       = request.form.get('nama')
        latin      = request.form.get('nama_latin')
        jenis      = request.form.get('jenis')
        status     = request.form.get('status_satwa')
        deskripsi  = request.form.get('deskripsi')
        lokasi_ids = request.form.getlist('lokasi_id[]')

        # ✅ Validasi kolom wajib
        if not nama or not latin or not jenis or not status or not deskripsi or not lokasi_ids:
            flash("Semua kolom wajib diisi dan minimal satu lokasi dipilih!", "danger")
            return render_template('admin/admin_satwa_form.html',
                                   satwa=satwa,
                                   lokasi_list=lokasi_list)

        # ✅ Cek duplikat nama satwa
        existing = Satwa.query.filter_by(nama_satwa=nama).first()
        if existing and existing.id != satwa.id:
            flash("Nama satwa sudah dipakai, gunakan nama lain!", "danger")
            return render_template('admin/admin_satwa_form.html',
                                   satwa=satwa,
                                   lokasi_list=lokasi_list)

        # update data satwa
        satwa.nama_satwa   = nama
        satwa.nama_latin   = latin
        satwa.jenis_satwa  = jenis
        satwa.status_satwa = status
        satwa.deskripsi    = deskripsi

        # ✅ update lokasi relasi (clear dulu)
        SatwaLokasi.query.filter_by(satwa_id=satwa.id).delete()
        for lid in lokasi_ids:
            relasi = SatwaLokasi(satwa_id=satwa.id, lokasi_id=int(lid))
            db.session.add(relasi)

        # upload banyak gambar
        files = request.files.getlist('gambar')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER_SATWA, filename)
                file.save(path)
                new_gambar = SatwaGambar(satwa_id=satwa.id, filename=filename)
                db.session.add(new_gambar)

        # hapus gambar lama jika ada request
        hapus_ids = request.form.get('hapus_gambar_ids')
        if hapus_ids:
            ids = hapus_ids.split(',')
            for gid in ids:
                gambar = SatwaGambar.query.get(int(gid))
                if gambar:
                    db.session.delete(gambar)

        db.session.commit()
        flash("Data satwa berhasil diperbarui!", "success")
        return redirect(url_for('admin.list_satwa'))

    return render_template('admin/admin_satwa_form.html', satwa=satwa, lokasi_list=lokasi_list)


@admin_bp.route('/satwa/delete/<int:satwa_id>')
def delete_satwa(satwa_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    satwa = Satwa.query.get_or_404(satwa_id)
    db.session.delete(satwa)
    db.session.commit()
    flash("Satwa berhasil dihapus!", "success")
    return redirect(url_for('admin.list_satwa'))


# =======================
# HAPUS GAMBAR SATWA
# =======================
@admin_bp.route('/satwa/<int:satwa_id>/gambar/<int:gambar_id>/delete', methods=['POST'])
def delete_satwa_gambar(satwa_id, gambar_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    gambar = SatwaGambar.query.get_or_404(gambar_id)
    db.session.delete(gambar)
    db.session.commit()

    flash("Gambar berhasil dihapus!", "success")
    # ✅ setelah hapus, tetap kembali ke halaman edit satwa
    return redirect(url_for('admin.edit_satwa', satwa_id=satwa_id))



# =======================
# LOKASI CRUD
# =======================
@admin_bp.route("/lokasi")
def list_lokasi():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    lokasi_list = LokasiKonservasi.query.order_by(LokasiKonservasi.id.asc()).all()
    return render_template("admin/admin_lokasi.html", lokasi_list=lokasi_list)


@admin_bp.route('/lokasi/add', methods=['GET','POST'])
def add_lokasi():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    if request.method == 'POST':
        nama = request.form.get('nama_lokasi')
        kategori = request.form.get('kategori')
        deskripsi = request.form.get('deskripsi')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # ✅ Validasi kolom wajib
        if not nama or not kategori or not deskripsi or not latitude or not longitude:
            flash("Semua kolom wajib diisi!", "danger")
            return render_template('admin/admin_lokasi_form.html', lokasi=None)

        lokasi = LokasiKonservasi(
            nama_lokasi=nama,
            kategori=kategori,
            deskripsi=deskripsi,
            latitude=float(latitude),
            longitude=float(longitude),
            geom=func.ST_SetSRID(func.ST_MakePoint(float(longitude), float(latitude)), 4326)
        )

        # upload gambar baru
        file = request.files.get('gambar_file')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER_LOKASI, filename)
            file.save(path)
            lokasi.gambar = filename

        db.session.add(lokasi)
        db.session.commit()
        flash("Lokasi baru berhasil ditambahkan!", "success")
        return redirect(url_for('admin.list_lokasi'))

    return render_template('admin/admin_lokasi_form.html', lokasi=None)



@admin_bp.route('/lokasi/edit/<int:lokasi_id>', methods=['GET','POST'])
def edit_lokasi(lokasi_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    lokasi = LokasiKonservasi.query.get_or_404(lokasi_id)

    if request.method == 'POST':
        lokasi.nama_lokasi = request.form.get('nama_lokasi')
        lokasi.kategori = request.form.get('kategori')
        lokasi.deskripsi = request.form.get('deskripsi')

        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # ✅ Validasi kolom wajib
        if not lokasi.nama_lokasi or not lokasi.kategori or not lokasi.deskripsi or not latitude or not longitude:
            flash("Semua kolom wajib diisi!", "danger")
            return render_template('admin/admin_lokasi_form.html', lokasi=lokasi)

        lokasi.latitude = float(latitude)
        lokasi.longitude = float(longitude)
        lokasi.geom = func.ST_SetSRID(
            func.ST_MakePoint(lokasi.longitude, lokasi.latitude), 4326
        )

        # upload gambar baru
        file = request.files.get('gambar_file')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER_LOKASI, filename)
            file.save(path)
            lokasi.gambar = filename

        db.session.commit()
        flash("Data lokasi berhasil disimpan!", "success")
        return redirect(url_for('admin.list_lokasi'))

    return render_template('admin/admin_lokasi_form.html', lokasi=lokasi)



# =======================
# HAPUS GAMBAR LOKASI (SINGLE)
# =======================
@admin_bp.route('/lokasi/<int:lokasi_id>/hapus_gambar')
def hapus_gambar_lokasi(lokasi_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    lokasi = LokasiKonservasi.query.get_or_404(lokasi_id)
    lokasi.gambar = None
    db.session.commit()

    flash("Gambar lokasi berhasil dihapus!", "success")
    return redirect(url_for('admin.edit_lokasi', lokasi_id=lokasi_id))


# =======================
# HAPUS LOKASI
# =======================
@admin_bp.route('/lokasi/delete/<int:lokasi_id>')
def delete_lokasi(lokasi_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    lokasi = LokasiKonservasi.query.get_or_404(lokasi_id)
    db.session.delete(lokasi)
    db.session.commit()

    flash("Lokasi berhasil dihapus!", "success")
    return redirect(url_for('admin.list_lokasi'))
