from flask import Flask, render_template, request, session, redirect, url_for
import folium
import json
from sqlalchemy import func
from flask_migrate import Migrate
from folium.plugins import MarkerCluster, HeatMap
from models import db, Satwa, LokasiKonservasi, SatwaLokasi, Admin
from admin import admin_bp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
app.secret_key = os.getenv("SECRET_KEY")
app.register_blueprint(admin_bp)


# =======================
# about
# =======================
@app.route('/about')
def about():
    return render_template('about.html')

# =======================
# LOGIN
# =======================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))
        else:
            return render_template("login.html", error="Username atau password salah")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# =======================
# HALAMAN UTAMA
# =======================
@app.route('/')
def index():
    return render_template('index.html')

# =======================
# LIST SATWA
# =======================
@app.route('/satwa')
def satwa():
    q = request.args.get('q', '').strip()
    if q:
        satwa_list = Satwa.query.filter(
            (Satwa.nama_satwa.ilike(f"%{q}%")) |
            (Satwa.jenis_satwa.ilike(f"%{q}%")) |
            (Satwa.status_satwa.ilike(f"%{q}%"))
        ).order_by(Satwa.id.asc()).all()
    else:
        satwa_list = Satwa.query.order_by(Satwa.id.asc()).all()
    return render_template('satwa.html', satwa_list=satwa_list, q=q)


@app.route('/satwa/<int:satwa_id>')
def satwa_detail(satwa_id):
    satwa = Satwa.query.get_or_404(satwa_id)
    return render_template('satwa_detail.html', satwa=satwa)

# =======================
# PETA
# =======================
@app.route('/peta', methods=["GET", "POST"])
def peta():
    return map_view()

@app.route('/lokasi')
def lokasi():
    lokasi_list = LokasiKonservasi.query.order_by(LokasiKonservasi.id.asc()).all()
    return render_template('lokasi.html', lokasi_list=lokasi_list)

@app.route('/lokasi/kategori/<string:kategori>')
def lokasi_kategori(kategori):
    lokasi_list = LokasiKonservasi.query.filter(
        LokasiKonservasi.kategori.ilike(kategori)
    ).order_by(LokasiKonservasi.id.asc()).all()
    return render_template('lokasi.html', lokasi_list=lokasi_list, kategori=kategori)

@app.route('/lokasi/<int:lokasi_id>')
def lokasi_detail(lokasi_id):
    lokasi = LokasiKonservasi.query.get_or_404(lokasi_id)
    return render_template('lokasi_detail.html', lokasi=lokasi)

# =======================
# MAP VIEW
# =======================
def map_view():
    mini = request.args.get("mini")
    nama_satwa = request.args.get("nama_satwa")
    lokasi = request.args.get("lokasi")
    jenis = request.args.get("jenis")
    status = request.args.get("status")

    satwa_list = Satwa.query.all()
    lokasi_list = LokasiKonservasi.query.all()

    # =======================
    # MINI MAP
    # =======================
    if mini and lokasi:
        lokasi_obj = LokasiKonservasi.query.filter(
            LokasiKonservasi.nama_lokasi.ilike(lokasi)
        ).first()

        if lokasi_obj and lokasi_obj.latitude and lokasi_obj.longitude:
            m = folium.Map(
                location=[lokasi_obj.latitude, lokasi_obj.longitude],
                zoom_start=8,
                tiles='OpenStreetMap',
                control_scale=True
            )

            folium.Marker(
                location=[lokasi_obj.latitude, lokasi_obj.longitude],
                popup=lokasi_obj.nama_lokasi
            ).add_to(m)

            return render_template("peta_mini.html", map_html=m._repr_html_(), lokasi=lokasi_obj)

    # =======================
    # FILTER
    # =======================
    query = Satwa.query.join(SatwaLokasi).join(LokasiKonservasi)

    if nama_satwa:
        query = query.filter(Satwa.nama_satwa.ilike(f"%{nama_satwa}%"))
    if jenis:
        query = query.filter(Satwa.jenis_satwa.ilike(f"%{jenis}%"))
    if status:
        query = query.filter(Satwa.status_satwa.ilike(f"%{status}%"))
    if lokasi:
        query = query.filter(LokasiKonservasi.nama_lokasi.ilike(lokasi))

    filtered = query.all()

    # =======================
    # MAP
    # =======================
    m = folium.Map(
        location=[-8.2, 112.5],
        zoom_start=7.3,
        tiles=None,
        control_scale=True
    )

    # =======================
    # BASEMAP
    # =======================
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
    folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)

    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='© OpenTopoMap',
        name='Topo Map'
    ).add_to(m)

    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)

    # =======================
    # CLUSTER
    # =======================
    
    marker_cluster = MarkerCluster(
    icon_create_function="""
    function(cluster) {
        return L.divIcon({
            html: '<div style="background:red;color:white;border-radius:50%;width:35px;height:35px;display:flex;align-items:center;justify-content:center;">' 
                  + cluster.getChildCount() + 
                  '</div>',
            className: 'marker-cluster',
            iconSize: new L.Point(35, 35)
        });
    }
    """
).add_to(m)
    
    
    

    lokasi_terpakai = set()
    heat_data = []

    # =======================
    # LOOP DATA
    # =======================
    for satwa in filtered:
        for relasi in satwa.lokasi_relasi:
            lokasi_obj = relasi.lokasi

            if lokasi and lokasi_obj.nama_lokasi.lower() != lokasi.lower():
                continue

            if lokasi_obj.id in lokasi_terpakai:
                continue

            lokasi_terpakai.add(lokasi_obj.id)

            # 🔥 HEATMAP
            if lokasi_obj.latitude and lokasi_obj.longitude:
                heat_data.append([lokasi_obj.latitude, lokasi_obj.longitude])



            # MARKER POPUP
            if lokasi_obj.latitude and lokasi_obj.longitude:
                html_popup = f"""
                <div style="
                    width:250px;
                    font-family:'Segoe UI', Arial, sans-serif;
                    border-radius:12px;
                    overflow:hidden;
                    box-shadow:0 6px 18px rgba(0,0,0,0.25);
                    background:white;
                ">
                    <!-- FOTO -->
                    <img src='/static/img/lokasi/{lokasi_obj.gambar or "default.png"}'
                        style="width:100%; height:130px; object-fit:cover;">

                    <!-- KONTEN -->
                    <div style="padding:12px;">
                        <!-- NAMA LOKASI -->
                        <h5 style="margin:0 0 6px 0; font-size:15px; font-weight:600; color:#009688;">
                            {lokasi_obj.nama_lokasi}
                        </h5>

                        <!-- KATEGORI -->
                        <p style="margin:0 0 8px 0; font-size:12px; color:#888;">
                            {lokasi_obj.kategori or "Kawasan Konservasi"}
                        </p>

                        <!-- DESKRIPSI -->
                        <p style="margin:0 0 10px 0; font-size:12px; color:#555; line-height:1.4;">
                            {(lokasi_obj.deskripsi[:80] + '...') if lokasi_obj.deskripsi else 'Kawasan konservasi satwa dilindungi.'}
                        </p>

                        <!-- INFO SATWA -->
                        <p style="margin:0 0 12px 0; font-size:12px; color:#333;">
                            Satwa: <strong>{satwa.nama_satwa}</strong>
                        </p>

                        <!-- TOMBOL -->
                        <a href="/lokasi/{lokasi_obj.id}"
                            style="display:block; text-align:center; background:linear-gradient(135deg,#009688,#00796b);
                                color:white; padding:7px; border-radius:8px; text-decoration:none; font-size:12px;
                                font-weight:500; transition:0.2s;">
                            Lihat Detail
                        </a>
                    </div>
                </div>
                """



                folium.Marker(
                    location=[lokasi_obj.latitude, lokasi_obj.longitude],
                    popup=folium.Popup(html_popup, max_width=250),
                    tooltip=lokasi_obj.nama_lokasi,
                    icon=folium.Icon(color="blue")
                ).add_to(marker_cluster)

    # =======================
    # HEATMAP
    # =======================
    if heat_data:
        heat_layer = folium.FeatureGroup(name="Heatmap", show=False)

        HeatMap(heat_data, radius=25).add_to(heat_layer)

        heat_layer.add_to(m)
        
        

    folium.LayerControl(collapsed=False).add_to(m)

    return render_template(
        "peta.html",
        map_html=m._repr_html_(),
        nama_satwa=nama_satwa,
        lokasi=lokasi,
        jenis=jenis,
        status=status,
        satwa_list=satwa_list,
        lokasi_list=lokasi_list,
        mini=mini
    )

# =======================
# RUN
# =======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
