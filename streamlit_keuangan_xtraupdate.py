import streamlit as st
import pandas as pd
from io import BytesIO

# =======================================================================================
# KONFIGURASI APLIKASI
# =======================================================================================
st.set_page_config(page_title="Laporan Keuangan", layout="wide")

USERS = {
    "admin": "123",
    "user1": "abc",
    "keuangan": "finance123",
    "bos": "super123"
}
# =======================================================================================
# INISIALISASI SESSION STATE
# =======================================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(
        columns=["Tanggal", "Deskripsi", "Akun", "Kategori", "Debit", "Kredit"]
    )

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# Chart of Accounts defaults (bisa diubah lewat UI)
if "akun_list" not in st.session_state:
    st.session_state.akun_list = [
        "Kas", "Bank", "Piutang", "Persediaan", "Peralatan",
        "Utang", "Beban", "Modal", "Pendapatan"
    ]

if "kategori_map" not in st.session_state:
    st.session_state.kategori_map = {
        "Kas": "Aset",
        "Bank": "Aset",
        "Piutang": "Aset",
        "Persediaan": "Aset",
        "Peralatan": "Aset",
        "Utang": "Kewajiban",
        "Beban": "Beban",       # treat Beban as its own category (for L/R later)
        "Modal": "Ekuitas",
        "Pendapatan": "Pendapatan"  # treat Pendapatan as its own category
    }

if "kategori_list" not in st.session_state:
    # Derive from kategori_map values (unique) + some sensible defaults
    st.session_state.kategori_list = sorted(list(set(st.session_state.kategori_map.values()) | {"Aset", "Kewajiban", "Ekuitas", "Beban", "Pendapatan", "Lainnya"}))

# =======================================================================================
# FUNGSI CHART OF ACCOUNTS
# =======================================================================================
def add_account(account_name: str, kategori: str):
    account_name = account_name.strip()
    if not account_name:
        st.warning("Nama akun tidak boleh kosong.")
        return False
    if account_name in st.session_state.akun_list:
        st.warning("Akun sudah ada.")
        return False
    st.session_state.akun_list.append(account_name)
    st.session_state.kategori_map[account_name] = kategori
    if kategori not in st.session_state.kategori_list:
        st.session_state.kategori_list.append(kategori)
    st.success(f"Akun '{account_name}' ditambahkan dengan kategori '{kategori}'.")
    return True

def delete_account(account_name: str):
    # Prevent deletion if account is used in transactions
    used = account_name in st.session_state.data["Akun"].values
    if used:
        st.error("Akun tidak dapat dihapus karena sudah digunakan di transaksi.")
        return False
    if account_name in st.session_state.akun_list:
        st.session_state.akun_list.remove(account_name)
    if account_name in st.session_state.kategori_map:
        del st.session_state.kategori_map[account_name]
    st.success(f"Akun '{account_name}' dihapus.")
    return True

def add_category(kategori_name: str):
    kategori_name = kategori_name.strip()
    if not kategori_name:
        st.warning("Nama kategori tidak boleh kosong.")
        return False
    if kategori_name in st.session_state.kategori_list:
        st.warning("Kategori sudah ada.")
        return False
    st.session_state.kategori_list.append(kategori_name)
    st.success(f"Kategori '{kategori_name}' ditambahkan.")
    return True

# =======================================================================================
# FUNGSI DATA (TRANSAKSI)
# =======================================================================================
def add_transaction(tanggal, deskripsi, akun, kategori, debit, kredit):
    new_row = {
        "Tanggal": tanggal,
        "Deskripsi": deskripsi,
        "Akun": akun,
        "Kategori": kategori,
        "Debit": debit,
        "Kredit": kredit,
    }
    st.session_state.data = pd.concat(
        [st.session_state.data, pd.DataFrame([new_row])],
        ignore_index=True
    )

def update_transaction(index, tanggal, deskripsi, akun, kategori, debit, kredit):
    st.session_state.data.loc[index] = [tanggal, deskripsi, akun, kategori, debit, kredit]

def delete_transaction(index):
    st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)

# =======================================================================================
# EXPORT FUNCTION
# =======================================================================================
def export_excel():
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.data.to_excel(writer, index=False)
    return output.getvalue()

def export_csv():
    return st.session_state.data.to_csv(index=False).encode("utf-8")

# =======================================================================================
# HALAMAN LOGIN
# =======================================================================================
def login_page():
    st.title("🔐 Login Aplikasi Keuangan")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and password == USERS[username]:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.rerun()
        else:
            st.error("Username atau Password salah!")

# =======================================================================================
# HALAMAN TRANSAKSI
# =======================================================================================
def transaksi_page():
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📘 Aplikasi Laporan Keuangan (Debit & Kredit)")

    # ===============================
    # Input / Edit Form
    # ===============================
    with st.container():
        st.subheader("Input Transaksi")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        akun_list = st.session_state.akun_list
        kategori_map = st.session_state.kategori_map
        kategori_list = st.session_state.kategori_list

        if st.session_state.edit_index is None:
            # Mode input baru
            tanggal = col1.date_input("Tanggal")
            deskripsi = col2.text_input("Deskripsi")
            akun = col3.selectbox("Akun", akun_list)
            # kategorinya otomatis dari kategori_map; fallback ke 'Lainnya' jika tidak ada
            kategori = kategori_map.get(akun, "Lainnya")
            col4.write(f"Kategori: **{kategori}**")
            debit = col5.number_input("Debit", min_value=0, value=0)
            kredit = col6.number_input("Kredit", min_value=0, value=0)

            if st.button("Tambah Transaksi"):
                add_transaction(tanggal, deskripsi, akun, kategori, debit, kredit)
                st.success("Transaksi berhasil ditambahkan!")

        else:
            # Mode edit data
            row = st.session_state.data.loc[st.session_state.edit_index]

            tanggal = col1.date_input("Tanggal", value=pd.to_datetime(row["Tanggal"]))
            deskripsi = col2.text_input("Deskripsi", value=row["Deskripsi"])
            akun = col3.selectbox("Akun", akun_list, index=akun_list.index(row["Akun"]))
            kategori = kategori_map.get(akun, "Lainnya")
            col4.write(f"Kategori: **{kategori}**")
            debit = col5.number_input("Debit", min_value=0, value=int(row["Debit"]))
            kredit = col6.number_input("Kredit", min_value=0, value=int(row["Kredit"]))

            if st.button("Simpan Perubahan"):
                update_transaction(st.session_state.edit_index, tanggal, deskripsi, akun, kategori, debit, kredit)
                st.session_state.edit_index = None
                st.success("Data berhasil diperbarui!")

            if st.button("Batal/Selesai Edit"):
                st.session_state.edit_index = None

    # ===============================
    # Tabel Data
    # ===============================
    st.subheader("📄 Daftar Transaksi")

    if not st.session_state.data.empty:
        for idx, row in st.session_state.data.iterrows():
            cols = st.columns([2, 3, 2, 2, 2, 2, 2, 2])

            cols[0].write(row["Tanggal"])
            cols[1].write(row["Deskripsi"])
            cols[2].write(row["Akun"])
            cols[3].write(row["Kategori"])
            cols[4].write(row["Debit"])
            cols[5].write(row["Kredit"])

            if cols[6].button("Edit", key=f"edit_{idx}"):
                st.session_state.edit_index = idx

            if cols[7].button("Hapus", key=f"delete_{idx}"):
                delete_transaction(idx)
                st.rerun()

        # ===============================
        # Export Buttons
        # ===============================
        st.subheader("📦 Export Data")

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.download_button(
                label="⬇️ Export ke Excel",
                data=export_excel(),
                file_name="laporan_keuangan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_e2:
            st.download_button(
                label="⬇️ Export ke CSV",
                data=export_csv(),
                file_name="laporan_keuangan.csv",
                mime="text/csv"
            )
    else:
        st.info("Belum ada transaksi. Tambahkan transaksi di atas.")

    # ===============================
    # Ringkasan Saldo
    # ===============================
    st.subheader("📊 Ringkasan Saldo")

    total_debit = st.session_state.data["Debit"].sum()
    total_kredit = st.session_state.data["Kredit"].sum()
    saldo = total_debit - total_kredit

    colA, colB, colC = st.columns(3)
    colA.metric("Total Debit", f"Rp {total_debit:,.0f}")
    colB.metric("Total Kredit", f"Rp {total_kredit:,.0f}")
    colC.metric("Saldo", f"Rp {saldo:,.0f}")

# =======================================================================================
# HALAMAN BUKU BESAR
# =======================================================================================
def buku_besar_page():
    st.title("📗 Buku Besar")
    
    st.markdown("""
    **Buku besar akuntansi adalah catatan utama yang berisi kumpulan akun-akun keuangan perusahaan yang digunakan untuk menampung,
    mengelompokkan, dan merangkum seluruh transaksi dari jurnal umum, sehingga dapat diketahui perubahan dan saldo akhir 
    setiap akun yang menjadi dasar penyusunan laporan keuangan.**
    """)

    if st.session_state.data.empty:
        st.info("Belum ada data transaksi.")
        return

    akun_list = st.session_state.data["Akun"].unique()
    akun_pilihan = st.selectbox("Pilih Akun", akun_list)

    df = st.session_state.data[st.session_state.data["Akun"] == akun_pilihan].copy()
    df = df.sort_values("Tanggal")

    df["Saldo"] = (df["Debit"] - df["Kredit"]).cumsum()

    st.write(f"### Buku Besar: {akun_pilihan}")
    st.dataframe(df)

# =======================================================================================
# HALAMAN NERACA
# =======================================================================================
def neraca_page():
    st.title("📘 Neraca")
    
    st.markdown("""
    **Neraca dalam akuntansi adalah laporan keuangan yang menunjukkan posisi keuangan suatu perusahaan pada suatu titik waktu tertentu,
    dengan menampilkan jumlah aset, kewajiban, dan ekuitas untuk menggambarkan keseimbangan antara 
    apa yang dimiliki dan apa yang menjadi sumber pendanaannya.**
    """)

    if st.session_state.data.empty:
        st.info("Belum ada data transaksi.")
        return

    df = st.session_state.data.copy()
    df["Saldo"] = df["Debit"] - df["Kredit"]

    aset = df[df["Kategori"] == "Aset"]["Saldo"].sum()
    kewajiban = df[df["Kategori"] == "Kewajiban"]["Saldo"].sum()
    ekuitas = df[df["Kategori"] == "Ekuitas"]["Saldo"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Aset", f"Rp {aset:,.0f}")
    col2.metric("Total Kewajiban", f"Rp {kewajiban:,.0f}")
    col3.metric("Total Ekuitas", f"Rp {ekuitas:,.0f}")

    st.write("### Neraca Detail")
    st.dataframe(df[["Akun", "Kategori", "Saldo"]])

# =======================================================================================
# HALAMAN CHART OF ACCOUNTS (MANAGE AKUN & KATEGORI)
# =======================================================================================
def chart_akun_page():
    
    # --- RESET INPUT (HARUS SEBELUM WIDGET DITAMPILKAN) ---
    if "reset_input_akun" in st.session_state and st.session_state.reset_input_akun:
        st.session_state["akun_input_widget"] = ""
        st.session_state.reset_input_akun = False

    if "reset_input_kategori" in st.session_state and st.session_state.reset_input_kategori:
        st.session_state["kategori_input_widget"] = ""
        st.session_state.reset_input_kategori = False

    # --- LAYOUT ---
    st.title("🧾 Chart of Accounts (Daftar Akun)")
    
    st.markdown("""
    **Akun dalam akuntansi adalah tempat atau wadah pencatatan yang digunakan untuk mengelompokkan transaksi keuangan berdasarkan jenisnya, seperti kas,
    piutang, persediaan, penjualan, atau beban, sehingga setiap perubahan akibat transaksi dapat tercatat 
    dan dihitung saldonya secara jelas dan terstruktur.**
    """)

    col_add_acc, col_view = st.columns([1, 2])

    # ==============================
    #   KOLOM KIRI: ADD AKUN
    # ==============================
    with col_add_acc:
        st.subheader("Tambah Akun Baru")

        akun_baru = st.text_input("Nama Akun", key="akun_input_widget")

        kategori_pilihan = st.selectbox(
            "Pilih Kategori",
            st.session_state.kategori_list,
            key="select_kategori_widget"
        )

        if st.button("Tambah Akun"):
            if add_account(akun_baru, kategori_pilihan):
                st.session_state.reset_input_akun = True
                st.rerun()

        st.markdown("---")
        st.subheader("Tambah Kategori Baru")

        kategori_baru = st.text_input("Nama Kategori", key="kategori_input_widget")

        if st.button("Tambah Kategori"):
            if add_category(kategori_baru):
                st.session_state.reset_input_kategori = True
                st.rerun()

    # ==============================
    #   KOLOM KANAN: TABEL COA
    # ==============================
    with col_view:
        st.subheader("Daftar Akun")

        df_coa = pd.DataFrame({
            "Akun": st.session_state.akun_list,
            "Kategori": [
                st.session_state.kategori_map.get(a, "Lainnya")
                for a in st.session_state.akun_list
            ]
        })

        st.dataframe(df_coa, use_container_width=True)

        st.markdown("### Hapus Akun")
        akun_to_delete = st.selectbox(
            "Pilih akun yang ingin dihapus:",
            [""] + st.session_state.akun_list,
            key="del_acc_select"
        )

        if st.button("Hapus Akun"):
            if akun_to_delete:
                delete_account(akun_to_delete)
                st.rerun()
            else:
                st.warning("Pilih akun terlebih dahulu!")

        st.markdown("---")
        st.subheader("Daftar Kategori")
        st.write(st.session_state.kategori_list)

# =======================================================================================
# NAVIGASI MENU
# =======================================================================================
menu = st.sidebar.selectbox("Menu", ["Transaksi", "Buku Besar", "Neraca", "Chart Akun"])

# =======================================================================================
# EKSEKUSI UTAMA
# =======================================================================================
if not st.session_state.get("logged_in", False):
    login_page()
else:
    if menu == "Transaksi":
        transaksi_page()
    elif menu == "Buku Besar":
        buku_besar_page()
    elif menu == "Neraca":
        neraca_page()
    elif menu == "Chart Akun":
        chart_akun_page()
