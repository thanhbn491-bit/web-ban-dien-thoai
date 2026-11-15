import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "bao_mat_gio_hang_phone_store"

ADMIN_USER = "admin"
ADMIN_PASS = "123456"
DB_NAME = "cua_hang.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def khoi_tao_db():
    conn = get_db()
    # Tạo bảng sản phẩm
    conn.execute("""
        CREATE TABLE IF NOT EXISTS san_pham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            gia INTEGER NOT NULL,
            anh TEXT NOT NULL,
            mo_ta TEXT
        )
    """)
    # Tạo bảng đơn hàng
    conn.execute("""
        CREATE TABLE IF NOT EXISTS don_hang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_ten TEXT NOT NULL,
            sdt TEXT NOT NULL,
            dia_chi TEXT NOT NULL,
            san_pham TEXT NOT NULL,
            tong_tien INTEGER NOT NULL
        )
    """)
    # Thêm 4 sản phẩm mẫu nếu bảng đang trống
    dem = conn.execute("SELECT COUNT(*) FROM san_pham").fetchone()[0]
    if dem == 0:
        du_lieu_mau = [
            ("iPhone 16 Pro Max 256GB", 34990000, "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/i/p/iphone-16-pro-max.png", "Màn hình: 6.9 inch Super Retina XDR\nChip: Apple A18 Pro\nRAM: 8GB | Bộ nhớ: 256GB\nCamera chính: 48MP Fusion"),
            ("Samsung Galaxy S24 Ultra", 29990000, "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/s/s/ss-s24-ultra-xam-222.png", "Màn hình: 6.8 inch Dynamic AMOLED 2X\nChip: Snapdragon 8 Gen 3 for Galaxy\nRAM: 12GB | Pin: 5000mAh, sạc 45W"),
            ("Xiaomi 14 Ultra 5G", 24990000, "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/x/i/xiaomi-14-ultra_1_.png", "Màn hình: 6.73 inch LTPO AMOLED 120Hz\nChip: Snapdragon 8 Gen 3\nCamera hợp tác Leica 50MP, RAM 16GB"),
            ("OPPO Find X8 Pro", 27990000, "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product/o/p/oppo-find-x8-pro.png", "Màn hình: 6.78 inch AMOLED 120Hz\nChip: MediaTek Dimensity 9400\nPin: 5910mAh, sạc nhanh SuperVOOC 80W")
        ]
        conn.executemany("INSERT INTO san_pham (ten, gia, anh, mo_ta) VALUES (?, ?, ?, ?)", du_lieu_mau)
    conn.commit()
    conn.close()

# Khởi tạo database ngay khi chạy ứng dụng
khoi_tao_db()

# --- TRANG CHỦ & TÌM KIẾM ---
@app.route("/")
def trang_chu():
    tu_khoa = request.args.get("q", "").strip()
    conn = get_db()
    if tu_khoa:
        ket_qua = conn.execute("SELECT * FROM san_pham WHERE ten LIKE ?", (f"%{tu_khoa}%",)).fetchall()
    else:
        ket_qua = conn.execute("SELECT * FROM san_pham").fetchall()
    conn.close()
    gio_hang = session.get("gio_hang", [])
    return render_template("index.html", danh_sach=ket_qua, tu_khoa=tu_khoa, so_luong=len(gio_hang))

# --- CHI TIẾT SẢN PHẨM ---
@app.route("/san-pham/<int:id_sp>")
def chi_tiet(id_sp):
    conn = get_db()
    sp = conn.execute("SELECT * FROM san_pham WHERE id = ?", (id_sp,)).fetchone()
    conn.close()
    if not sp:
        return redirect(url_for("trang_chu"))
    return render_template("chi_tiet.html", sp=sp)

# --- GIỎ HÀNG & LƯU ĐƠN HÀNG VÀO DATABASE ---
@app.route("/them-gio-hang/<int:id_sp>")
def them_gio_hang(id_sp):
    conn = get_db()
    sp = conn.execute("SELECT * FROM san_pham WHERE id = ?", (id_sp,)).fetchone()
    conn.close()
    if sp:
        gio_hang = session.get("gio_hang", [])
        gio_hang.append({"id": sp["id"], "ten": sp["ten"], "gia": sp["gia"]})
        session["gio_hang"] = gio_hang
    return redirect(url_for("trang_chu"))

@app.route("/gio-hang")
def xem_gio_hang():
    gio_hang = session.get("gio_hang", [])
    tong_tien = sum(item["gia"] for item in gio_hang)
    return render_template("gio_hang.html", gio_hang=gio_hang, tong_tien=tong_tien)

@app.route("/xoa-gio-hang/<int:index>")
def xoa_gio_hang(index):
    gio_hang = session.get("gio_hang", [])
    if 0 <= index < len(gio_hang):
        gio_hang.pop(index)
        session["gio_hang"] = gio_hang
    return redirect(url_for("xem_gio_hang"))

@app.route("/dat-hang", methods=["POST"])
def dat_hang():
    gio_hang = session.get("gio_hang", [])
    if not gio_hang:
        return redirect(url_for("trang_chu"))
    ho_ten = request.form.get("ho_ten")
    sdt = request.form.get("sdt")
    dia_chi = request.form.get("dia_chi")
    ds_ten_sp = ", ".join([item["ten"] for item in gio_hang])
    tong_tien = sum(item["gia"] for item in gio_hang)

    conn = get_db()
    conn.execute("INSERT INTO don_hang (ho_ten, sdt, dia_chi, san_pham, tong_tien) VALUES (?, ?, ?, ?, ?)",
                 (ho_ten, sdt, dia_chi, ds_ten_sp, tong_tien))
    conn.commit()
    conn.close()

    session["gio_hang"] = []
    return render_template("gio_hang.html", gio_hang=[], tong_tien=0, thong_bao=f"Cảm ơn {ho_ten}! Đơn hàng của bạn đã được lưu vào hệ thống.")

# --- ĐĂNG NHẬP / ĐĂNG XUẤT ADMIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["da_dang_nhap"] = True
            return redirect(url_for("trang_admin"))
        return render_template("login.html", loi="Sai tên đăng nhập hoặc mật khẩu!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("da_dang_nhap", None)
    return redirect(url_for("trang_chu"))

# --- QUẢN TRỊ SẢN PHẨM & XEM ĐƠN HÀNG ---
@app.route("/admin")
def trang_admin():
    if not session.get("da_dang_nhap"):
        return redirect(url_for("login"))
    tu_khoa = request.args.get("q", "").strip()
    conn = get_db()
    if tu_khoa:
        ket_qua = conn.execute("SELECT * FROM san_pham WHERE ten LIKE ?", (f"%{tu_khoa}%",)).fetchall()
    else:
        ket_qua = conn.execute("SELECT * FROM san_pham").fetchall()
    don_hang = conn.execute("SELECT * FROM don_hang ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", danh_sach=ket_qua, tu_khoa=tu_khoa, don_hang=don_hang)

@app.route("/admin/them", methods=["POST"])
def them_san_pham():
    if not session.get("da_dang_nhap"):
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("INSERT INTO san_pham (ten, gia, anh, mo_ta) VALUES (?, ?, ?, ?)",
                 (request.form.get("ten"), int(request.form.get("gia")), request.form.get("anh"), request.form.get("mo_ta")))
    conn.commit()
    conn.close()
    return redirect(url_for("trang_admin"))

@app.route("/admin/sua/<int:id_sp>", methods=["GET", "POST"])
def sua_san_pham(id_sp):
    if not session.get("da_dang_nhap"):
        return redirect(url_for("login"))
    conn = get_db()
    if request.method == "POST":
        conn.execute("UPDATE san_pham SET ten = ?, gia = ?, anh = ?, mo_ta = ? WHERE id = ?",
                     (request.form.get("ten"), int(request.form.get("gia")), request.form.get("anh"), request.form.get("mo_ta"), id_sp))
        conn.commit()
        conn.close()
        return redirect(url_for("trang_admin"))
    sp = conn.execute("SELECT * FROM san_pham WHERE id = ?", (id_sp,)).fetchone()
    conn.close()
    if not sp:
        return redirect(url_for("trang_admin"))
    return render_template("sua_san_pham.html", sp=sp)

@app.route("/admin/xoa/<int:id_sp>")
def xoa_san_pham(id_sp):
    if not session.get("da_dang_nhap"):
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("DELETE FROM san_pham WHERE id = ?", (id_sp,))
    conn.commit()
    conn.close()
    return redirect(url_for("trang_admin"))

if __name__ == "__main__":
    app.run(debug=True)