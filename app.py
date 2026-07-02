from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps

app = Flask(__name__)
app.secret_key = "proyek_sda_secret"

# ==========================================
# 1. STRUKTUR DATA (Multi-Tenant In-Memory Storage)
# ==========================================
# Menyimpan data setiap user secara terpisah
# Format: { "email@gmail.com": { "password": "...", "inventory": {}, "activity_stack": [] } }
users_db = {
    "dhiyanailahrizqya@gmail.com": {
        "password": "123",
        "inventory": {
            "KOP001": {"nama": "Buku Tulis Sidu 38L", "kategori": "ATK", "stok": 100, "harga": 4000},
            "KOP002": {"nama": "Pulpen Faster Hitam", "kategori": "ATK", "stok": 150, "harga": 3000},
            "KOP003": {"nama": "Pensil 2B Faber Castell", "kategori": "ATK", "stok": 120, "harga": 3500},
            "KOP004": {"nama": "Penghapus Joyko", "kategori": "ATK", "stok": 80, "harga": 2000},
            "KOP005": {"nama": "Tipe-X Kertas", "kategori": "ATK", "stok": 50, "harga": 6000},
            "KOP006": {"nama": "Penggaris Besi 30cm", "kategori": "ATK", "stok": 40, "harga": 5000},
            "KOP007": {"nama": "Indomie Goreng", "kategori": "Makanan", "stok": 200, "harga": 3500},
            "KOP008": {"nama": "Aqua Botol 600ml", "kategori": "Minuman", "stok": 100, "harga": 3500},
            "KOP009": {"nama": "Roti Aoka Coklat", "kategori": "Makanan", "stok": 60, "harga": 2500},
            "KOP010": {"nama": "Dasi SMA", "kategori": "Seragam", "stok": 30, "harga": 15000},
            "KOP011": {"nama": "Topi SMA", "kategori": "Seragam", "stok": 25, "harga": 20000},
            "KOP012": {"nama": "Sabuk Sekolah", "kategori": "Seragam", "stok": 35, "harga": 18000}
        },
        "activity_stack": []
    }
}

def get_user_data():
    email = session.get('username')
    if email and email in users_db:
        return users_db[email]
    return None

# ==========================================
# 2. ALGORITMA SEARCHING & SORTING
# ==========================================
def search_items(inventory_dict, query):
    result = {}
    for sku, detail in inventory_dict.items():
        if query.lower() in detail['nama'].lower() or query.lower() in detail['kategori'].lower():
            result[sku] = detail
    return result

def sort_inventory_by_stok(inventory_dict):
    items_list = list(inventory_dict.items())
    n = len(items_list)
    for i in range(n):
        for j in range(0, n-i-1):
            if items_list[j][1]['stok'] > items_list[j+1][1]['stok']:
                items_list[j], items_list[j+1] = items_list[j+1], items_list[j]
    return items_list

def sort_inventory_by_nama(inventory_dict):
    items_list = list(inventory_dict.items())
    n = len(items_list)
    for i in range(n):
        for j in range(0, n-i-1):
            if items_list[j][1]['nama'].lower() > items_list[j+1][1]['nama'].lower():
                items_list[j], items_list[j+1] = items_list[j+1], items_list[j]
    return items_list

def sort_inventory_by_sku(inventory_dict):
    items_list = list(inventory_dict.items())
    n = len(items_list)
    for i in range(n):
        for j in range(0, n-i-1):
            if items_list[j][0].lower() > items_list[j+1][0].lower():
                items_list[j], items_list[j+1] = items_list[j+1], items_list[j]
    return items_list

# Middleware untuk memastikan user login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('username') not in users_db:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# 3. ROUTING & CONTROLLER FLASK
# ==========================================

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('logged_in') and session.get('username') in users_db:
        return redirect(url_for('dashboard_manage'))
        
    if request.method == 'POST':
        email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not email.endswith('@gmail.com'):
            flash('Registrasi gagal! Email harus menggunakan @gmail.com', 'error')
        elif email in users_db:
            flash('Email sudah terdaftar. Silakan login.', 'warning')
        elif password:
            # Register user
            users_db[email] = {
                "password": password,
                "inventory": {},
                "activity_stack": []
            }
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in') and session.get('username') in users_db:
        return redirect(url_for('dashboard_manage'))
        
    if request.method == 'POST':
        email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if email in users_db and users_db[email]['password'] == password:
            session['logged_in'] = True
            session['username'] = email
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard_manage'))
        else:
            flash('Login gagal! Email atau password salah.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory_page():
    if not session.get('logged_in'):
        # Mode publik (hanya dummy display)
        return render_template('inventory_public.html')
        
    # Mode admin/logged-in
    user_data = get_user_data()
    if not user_data:
        return redirect(url_for('logout'))
        
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', '')

    if search_query:
        display_data = list(search_items(user_data['inventory'], search_query).items())
    elif sort_by == 'stok':
        display_data = sort_inventory_by_stok(user_data['inventory'])
    elif sort_by == 'nama':
        display_data = sort_inventory_by_nama(user_data['inventory'])
    elif sort_by == 'sku':
        display_data = sort_inventory_by_sku(user_data['inventory'])
    else:
        display_data = list(user_data['inventory'].items())

    log_texts = [log['text'] for log in user_data['activity_stack']]
    return render_template('inventory_manage.html', 
                           products=display_data, 
                           logs=log_texts, 
                           query=search_query,
                           sort_by=sort_by)

@app.route('/dashboard')
@login_required
def dashboard_manage():
    user_data = get_user_data()
    inv = user_data['inventory']
    
    total_barang = len(inv)
    kategori_set = set(item['kategori'] for item in inv.values())
    total_kategori = len(kategori_set)
    total_stok = sum(item['stok'] for item in inv.values())
    hampir_habis = sum(1 for item in inv.values() if item['stok'] <= 5)

    stats = {
        "total_barang": total_barang,
        "total_kategori": total_kategori,
        "total_stok": total_stok,
        "hampir_habis": hampir_habis
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/kategori')
@login_required
def kategori_manage():
    user_data = get_user_data()
    inv = user_data['inventory']
    
    # Menghitung jumlah barang per kategori
    kategori_data = {}
    for item in inv.values():
        kat = item['kategori']
        if kat not in kategori_data:
            kategori_data[kat] = 0
        kategori_data[kat] += 1
        
    return render_template('kategori.html', kategori_data=kategori_data)

@app.route('/laporan')
@login_required
def laporan_manage():
    user_data = get_user_data()
    # Membalik urutan log agar yang terbaru di atas
    logs = list(reversed(user_data['activity_stack']))
    return render_template('laporan.html', logs=logs)


@app.route('/add_page')
@login_required
def add_page():
    return render_template('add_item.html')

@app.route('/add', methods=['POST'])
@login_required
def add_item():
    user_data = get_user_data()
    inv = user_data['inventory']
    
    sku = request.form['sku'].strip().upper()
    nama = request.form['nama']
    kategori = request.form['kategori']
    stok = int(request.form['stok'])
    harga = int(request.form['harga'])

    if sku in inv:
        flash(f"Gagal! SKU {sku} sudah terdaftar.", "error")
    else:
        inv[sku] = {"nama": nama, "kategori": kategori, "stok": stok, "harga": harga}
        
        user_data['activity_stack'].append({
            "tipe": "tambah_baru",
            "sku": sku,
            "text": f"Ditambahkan: {nama} ({sku}) sebanyak {stok} unit."
        })
        flash(f"Produk {nama} berhasil ditambahkan!", "success")
        
    return redirect(url_for('inventory_page'))

@app.route('/edit_page/<sku>')
@login_required
def edit_page(sku):
    user_data = get_user_data()
    if sku not in user_data['inventory']:
        flash("Barang tidak ditemukan.", "error")
        return redirect(url_for('inventory_page'))
    
    item = user_data['inventory'][sku]
    return render_template('edit_item.html', sku=sku, item=item)

@app.route('/edit/<sku>', methods=['POST'])
@login_required
def edit_item(sku):
    user_data = get_user_data()
    inv = user_data['inventory']
    
    if sku in inv:
        inv[sku]['nama'] = request.form['nama']
        inv[sku]['kategori'] = request.form['kategori']
        inv[sku]['harga'] = int(request.form['harga'])
        flash(f"Barang {sku} berhasil diupdate.", "success")
    else:
        flash("Gagal update, barang tidak ditemukan.", "error")
        
    return redirect(url_for('inventory_page'))

@app.route('/delete/<sku>', methods=['POST'])
@login_required
def delete_item(sku):
    user_data = get_user_data()
    inv = user_data['inventory']
    
    if sku in inv:
        nama = inv[sku]['nama']
        del inv[sku]
        flash(f"Barang {nama} ({sku}) berhasil dihapus.", "success")
    else:
        flash("Gagal hapus, barang tidak ditemukan.", "error")
        
    return redirect(url_for('inventory_page'))

@app.route('/update_stok/<sku>', methods=['POST'])
@login_required
def update_stok(sku):
    user_data = get_user_data()
    inv = user_data['inventory']

    tipe = request.form['tipe']
    jumlah = int(request.form['jumlah'])

    if sku in inv:
        nama = inv[sku]['nama']
        if tipe == 'masuk':
            inv[sku]['stok'] += jumlah
            user_data['activity_stack'].append({
                "tipe": "stok_masuk",
                "sku": sku,
                "jumlah": jumlah,
                "text": f"Stok Masuk: {nama} ({sku}) +{jumlah} unit."
            })
            flash(f"Stok {nama} berhasil ditambah.", "success")
        elif tipe == 'keluar':
            if inv[sku]['stok'] >= jumlah:
                inv[sku]['stok'] -= jumlah
                user_data['activity_stack'].append({
                    "tipe": "stok_keluar",
                    "sku": sku,
                    "jumlah": jumlah,
                    "text": f"Stok Keluar: {nama} ({sku}) -{jumlah} unit."
                })
                flash(f"Stok {nama} berhasil dikurangi.", "success")
            else:
                flash(f"Gagal! Stok {nama} tidak mencukupi.", "error")
    return redirect(url_for('inventory_page'))

@app.route('/undo', methods=['POST'])
@login_required
def undo_action():
    user_data = get_user_data()
    inv = user_data['inventory']
    stack = user_data['activity_stack']

    if stack:
        last_action = stack.pop()
        tipe = last_action['tipe']
        sku = last_action['sku']

        if tipe == "tambah_baru":
            if sku in inv:
                deleted_name = inv[sku]['nama']
                del inv[sku]
                flash(f"Undo Berhasil: Barang '{deleted_name} ({sku})' dihapus kembali.", "info")

        elif tipe == "stok_masuk":
            jumlah = last_action['jumlah']
            if sku in inv:
                inv[sku]['stok'] -= jumlah
                flash(f"Undo Berhasil: Mengurangi kembali stok {inv[sku]['nama']} sebanyak {jumlah} unit.", "info")

        elif tipe == "stok_keluar":
            jumlah = last_action['jumlah']
            if sku in inv:
                inv[sku]['stok'] += jumlah
                flash(f"Undo Berhasil: Mengembalikan kembali stok {inv[sku]['nama']} sebanyak {jumlah} unit.", "info")
    else:
        flash("Tidak ada aktivitas yang bisa dibatalkan.", "warning")
        
    return redirect(url_for('inventory_page'))

if __name__ == '__main__':
    app.run(debug=True)