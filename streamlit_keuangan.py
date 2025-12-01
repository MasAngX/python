import streamlit as st
import pandas as pd

st.set_page_config(page_title="Laporan Keuangan", layout="wide")

# ------------------------------
# Inisialisasi session state
# ------------------------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Tanggal", "Deskripsi", "Debit", "Kredit"])

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ------------------------------
# Fungsi
# ------------------------------
def add_transaction(tanggal, deskripsi, debit, kredit):
    new_row = {"Tanggal": tanggal, "Deskripsi": deskripsi, "Debit": debit, "Kredit": kredit}
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)

def update_transaction(index, tanggal, deskripsi, debit, kredit):
    st.session_state.data.loc[index] = [tanggal, deskripsi, debit, kredit]

def delete_transaction(index):
    st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)

# ------------------------------
# Input / Edit Form
# ------------------------------
st.title("📘 Aplikasi Laporan Keuangan (Debit & Kredit)")

with st.container():
    st.subheader("Input Transaksi")

    col1, col2, col3, col4 = st.columns(4)

    if st.session_state.edit_index is None:
        # Mode input baru
        tanggal = col1.date_input("Tanggal")
        deskripsi = col2.text_input("Deskripsi")
        debit = col3.number_input("Debit", min_value=0, value=0)
        kredit = col4.number_input("Kredit", min_value=0, value=0)

        if st.button("Tambah Transaksi"):
            add_transaction(tanggal, deskripsi, debit, kredit)
            st.success("Transaksi berhasil ditambahkan!")
    else:
        # Mode edit data
        row = st.session_state.data.loc[st.session_state.edit_index]

        tanggal = col1.date_input("Tanggal", value=pd.to_datetime(row["Tanggal"]))
        deskripsi = col2.text_input("Deskripsi", value=row["Deskripsi"])
        debit = col3.number_input("Debit", min_value=0, value=int(row["Debit"]))
        kredit = col4.number_input("Kredit", min_value=0, value=int(row["Kredit"]))

        if st.button("Simpan Perubahan"):
            update_transaction(st.session_state.edit_index, tanggal, deskripsi, debit, kredit)
            st.session_state.edit_index = None
            st.success("Data berhasil diperbarui!")

        if st.button("Batal Edit"):
            st.session_state.edit_index = None

# ------------------------------
# Tabel Data
# ------------------------------
st.subheader("📄 Daftar Transaksi")

if not st.session_state.data.empty:
    st.write("Klik tombol **Edit** atau **Hapus** di baris data.")

    for idx, row in st.session_state.data.iterrows():
        cols = st.columns([3, 6, 3, 3, 2, 2])

        cols[0].write(row["Tanggal"])
        cols[1].write(row["Deskripsi"])
        cols[2].write(row["Debit"])
        cols[3].write(row["Kredit"])

        if cols[4].button("Edit", key=f"edit_{idx}"):
            st.session_state.edit_index = idx

        if cols[5].button("Hapus", key=f"delete_{idx}"):
            delete_transaction(idx)
            st.rerun()
else:
    st.info("Belum ada transaksi. Tambahkan transaksi di atas.")

# ------------------------------
# Saldo
# ------------------------------
st.subheader("📊 Ringkasan Saldo")

total_debit = st.session_state.data["Debit"].sum()
total_kredit = st.session_state.data["Kredit"].sum()
saldo = total_debit - total_kredit

colA, colB, colC = st.columns(3)
colA.metric("Total Debit", f"Rp {total_debit:,.0f}")
colB.metric("Total Kredit", f"Rp {total_kredit:,.0f}")
colC.metric("Saldo", f"Rp {saldo:,.0f}")
