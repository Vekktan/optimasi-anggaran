"""Antarmuka prototipe perhitungan kebutuhan mahasiswa.

Aplikasi ini hanya menerima input dan menampilkan hasil perhitungan.
Algoritma Genetika, batas anggaran, basis data, login, dan API tidak digunakan.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from perhitungan import (
    MAX_KOMBINASI,
    CONTOH_KEBUTUHAN,
    AlternatifMasukan,
    BarisKombinasi,
    DataTidakValid,
    HasilKebutuhan,
    HasilKombinasi,
    KebutuhanMasukan,
    bobot_dari_persen_kepuasan,
    contoh_sebagai_masukan,
    evaluasi_semua,
    fitness_alternatif,
    format_jumlah,
    format_rupiah,
    format_skor,
    harga_valid,
    hitung_nilai_harga,
    kunci_nama,
    PESAN_HARGA_TIDAK_VALID,
    kombinasi_dari_hasil,
    peringkat_dalam_kebutuhan,
    skor_kepuasan,
)

SKALA_KEPUASAN = {
    1: "Sangat rendah, alternatif sangat tidak sesuai keinginan.",
    2: "Rendah, alternatif kurang sesuai.",
    3: "Sedang, alternatif cukup sesuai.",
    4: "Tinggi, alternatif sesuai dengan keinginan.",
    5: "Sangat tinggi, alternatif sangat sesuai dengan keinginan.",
}


def main() -> None:
    st.set_page_config(
        page_title="Optimasi Alokasi Anggaran Mahasiswa",
        layout="wide",
    )
    terapkan_gaya()
    inisialisasi_state()
    sinkronkan_input()

    try:
        bobot_harga, bobot_kepuasan = bobot_dari_persen_kepuasan(
            st.session_state.bobot_kepuasan_persen
        )
    except DataTidakValid as exc:
        st.error(str(exc))
        return

    persen = int(st.session_state.bobot_kepuasan_persen)
    hasil = evaluasi_semua(ke_masukan(), bobot_harga, bobot_kepuasan)
    kombinasi = kombinasi_dari_hasil(hasil)

    tampilkan_header()
    tampilkan_input(hasil)
    tampilkan_bobot(persen, bobot_harga, bobot_kepuasan)
    tampilkan_ringkasan(kombinasi)
    tampilkan_tabel(hasil, persen)
    tampilkan_peringkat(hasil)
    tampilkan_tabel_kombinasi(kombinasi)
    tampilkan_penjelasan(hasil, kombinasi, bobot_harga, bobot_kepuasan, persen)
    st.divider()
    st.caption(
        "Data yang diisi hanya tersimpan selama sesi aplikasi ini terbuka. "
        "Menutup halaman atau memulai ulang aplikasi akan menghapus input. "
        "Prototype ini belum memakai Algoritma Genetika, batas anggaran, basis data, atau login."
    )


def terapkan_gaya() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2.4rem; max-width: 1080px;}
        h1 {font-weight: 650; letter-spacing: -0.02em; margin-bottom: 0.15rem;}
        h2 {margin-top: 0.6rem;}
        .subtitle {color: #3d4c5c; font-size: 1.05rem; margin: 0 0 0.35rem 0;}
        div[data-testid="stMetric"] {
            background: #f3f6fa;
            border: 1px solid #e4ebf2;
            border-radius: 8px;
            padding: 0.55rem 0.75rem;
        }
        @media (max-width: 768px) {
            .block-container {padding-left: 0.8rem; padding-right: 0.8rem;}
            h1 {font-size: 1.45rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inisialisasi_state() -> None:
    if "kebutuhan" not in st.session_state:
        st.session_state.kebutuhan = []
    if "next_id" not in st.session_state:
        st.session_state.next_id = 0
    if "bobot_kepuasan_persen" not in st.session_state:
        st.session_state.bobot_kepuasan_persen = 50
    if "pesan_singkat" not in st.session_state:
        st.session_state.pesan_singkat = None


def sinkronkan_input() -> None:
    """Menyalin nilai widget ke data kebutuhan tanpa menghapus input."""
    for kebutuhan in st.session_state.kebutuhan:
        kunci_nama_kebutuhan = f"keb_nama_{kebutuhan['id']}"
        if kunci_nama_kebutuhan in st.session_state:
            kebutuhan["nama"] = st.session_state[kunci_nama_kebutuhan]
        for alternatif in kebutuhan["alternatif"]:
            kunci_nama_alt = f"alt_nama_{alternatif['id']}"
            kunci_harga = f"alt_harga_{alternatif['id']}"
            kunci_kepuasan = f"alt_kepuasan_{alternatif['id']}"
            if kunci_nama_alt in st.session_state:
                alternatif["nama"] = st.session_state[kunci_nama_alt]
            if kunci_harga in st.session_state:
                alternatif["harga"] = baca_harga(st.session_state[kunci_harga])
            if kunci_kepuasan in st.session_state:
                alternatif["kepuasan"] = int(st.session_state[kunci_kepuasan])


def ke_masukan() -> tuple[KebutuhanMasukan, ...]:
    return tuple(
        KebutuhanMasukan(
            kebutuhan["nama"],
            tuple(
                AlternatifMasukan(
                    alternatif["nama"],
                    alternatif["harga"],
                    alternatif["kepuasan"],
                )
                for alternatif in kebutuhan["alternatif"]
            ),
        )
        for kebutuhan in st.session_state.kebutuhan
    )


def baca_harga(nilai: object) -> float | None:
    """Menyimpan harga apa adanya. Kosong tetap kosong, bukan diubah menjadi nol."""
    if nilai is None:
        return None
    try:
        angka = float(nilai)
    except (TypeError, ValueError):
        return None
    if angka != angka or angka in (float("inf"), float("-inf")):
        return None
    return angka


def buat_id() -> str:
    st.session_state.next_id += 1
    return f"n{st.session_state.next_id}"


def pastikan_widget(kunci: str, nilai) -> None:
    if kunci not in st.session_state:
        st.session_state[kunci] = nilai


def label_kepuasan(nilai: int) -> str:
    pendek = {
        1: "Sangat rendah",
        2: "Rendah",
        3: "Sedang",
        4: "Tinggi",
        5: "Sangat tinggi",
    }
    return f"{nilai} — {pendek[int(nilai)]}"


def tampilkan_pesan_hasil(item: HasilKebutuhan) -> None:
    for pesan in item.kesalahan:
        st.error(pesan)
    for jenis, pesan in item.catatan:
        if jenis == "peringatan":
            st.warning(pesan)
        else:
            st.info(pesan)


def tampilkan_header() -> None:
    st.title("Optimasi Alokasi Anggaran Mahasiswa")
    st.markdown(
        '<p class="subtitle">Membandingkan alternatif kebutuhan berdasarkan harga dan kepuasan.</p>',
        unsafe_allow_html=True,
    )
    st.caption("Prototype penelitian. Algoritma Genetika belum digunakan pada versi ini.")
    if st.session_state.pesan_singkat:
        st.success(st.session_state.pesan_singkat)
        st.session_state.pesan_singkat = None


def tampilkan_input(hasil: tuple[HasilKebutuhan, ...]) -> None:
    st.header("Kebutuhan dan alternatif")
    st.caption(
        "Kebutuhan adalah hal yang ingin dipenuhi. Alternatif adalah pilihannya. "
        "Contoh: kebutuhan Laptop, alternatif Laptop A, harga 5000000 (Rp5.000.000), kepuasan 3 dari 5."
    )
    kolom_muat, kolom_hapus = st.columns(2)
    with kolom_muat:
        if st.button("Muat Data Contoh", type="primary", width="stretch"):
            st.session_state.kebutuhan = buat_data_contoh()
            st.session_state.pesan_singkat = (
                "Data contoh dimuat. Harga pada contoh ini adalah data simulasi, "
                "bukan harga pasar yang telah diverifikasi."
            )
            st.rerun()
    with kolom_hapus:
        if st.button("Hapus Semua Data", width="stretch"):
            st.session_state.kebutuhan = []
            st.session_state.pesan_singkat = "Seluruh input kebutuhan dihapus. Bobot tidak diubah."
            st.rerun()

    st.caption(
        "Muat Data Contoh mengganti input yang sedang ada. "
        "Harganya data simulasi, bukan harga pasar."
    )
    with st.expander("Lihat isi data contoh"):
        pratinjau = []
        for blok in CONTOH_KEBUTUHAN:
            for alternatif in blok["alternatif"]:
                pratinjau.append(
                    {
                        "Kebutuhan": blok["nama"],
                        "Alternatif": alternatif["nama"],
                        "Harga": format_rupiah(alternatif["harga"]),
                        "Kepuasan": alternatif["kepuasan"],
                    }
                )
        st.dataframe(pd.DataFrame(pratinjau), hide_index=True, width="stretch")

    with st.form("form_tambah_kebutuhan", clear_on_submit=True):
        nama_baru = st.text_input(
            "Nama kebutuhan",
            placeholder="Laptop",
            help="Hal yang ingin dipenuhi. Contoh: Laptop.",
        )
        if st.form_submit_button("Tambah Kebutuhan", width="stretch"):
            if not nama_baru.strip():
                st.error("Nama kebutuhan tidak boleh kosong.")
            elif any(
                kunci_nama(item["nama"]) == kunci_nama(nama_baru)
                for item in st.session_state.kebutuhan
            ):
                st.error("Nama kebutuhan sudah digunakan. Gunakan nama yang berbeda.")
            else:
                st.session_state.kebutuhan.append(
                    {"id": buat_id(), "nama": nama_baru.strip(), "alternatif": []}
                )
                st.rerun()

    if not st.session_state.kebutuhan:
        st.info("Belum ada kebutuhan. Tambahkan kebutuhan atau muat data contoh.")
    else:
        st.caption(
            "Buka setiap kebutuhan untuk mengubah, menambah, atau menghapus alternatif. "
            "Panel yang datanya belum valid terbuka otomatis."
        )

    for kebutuhan, item in zip(st.session_state.kebutuhan, hasil):
        tampilkan_satu_kebutuhan(kebutuhan, item)

    with st.expander("Arti kepuasan 1 sampai 5"):
        for nilai, arti in SKALA_KEPUASAN.items():
            st.write(
                f"**{nilai}.** {arti} Skor = {format_skor(skor_kepuasan(nilai))}."
            )
    st.caption(
        "Ketik harga tanpa titik, misalnya 5000000. "
        "Harga harus lebih besar dari Rp0. Kolom yang dikosongkan tidak diubah menjadi nol."
    )


def buat_data_contoh() -> list[dict]:
    kebutuhan = []
    for blok in contoh_sebagai_masukan():
        kebutuhan.append(
            {
                "id": buat_id(),
                "nama": blok.nama,
                "alternatif": [
                    {
                        "id": buat_id(),
                        "nama": alternatif.nama,
                        "harga": float(alternatif.harga),
                        "kepuasan": int(alternatif.kepuasan),
                    }
                    for alternatif in blok.alternatif
                ],
            }
        )
    return kebutuhan


def tampilkan_satu_kebutuhan(kebutuhan: dict, item: HasilKebutuhan) -> None:
    nama_judul = kebutuhan["nama"].strip() or "(tanpa nama)"
    status = "" if item.valid else " — data belum valid"
    judul = f"{nama_judul} ({len(kebutuhan['alternatif'])} alternatif){status}"
    with st.expander(judul, expanded=not item.valid):
        kolom_nama, kolom_hapus = st.columns([4, 1.3])
        with kolom_nama:
            kunci = f"keb_nama_{kebutuhan['id']}"
            pastikan_widget(kunci, kebutuhan["nama"])
            st.text_input(
                "Nama kebutuhan",
                key=kunci,
                help="Hal yang ingin dipenuhi. Contoh: Laptop.",
            )
        with kolom_hapus:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            if st.button("Hapus kebutuhan", key=f"hapus_keb_{kebutuhan['id']}", width="stretch"):
                st.session_state.kebutuhan = [
                    data for data in st.session_state.kebutuhan if data["id"] != kebutuhan["id"]
                ]
                st.rerun()

        tampilkan_pesan_hasil(item)
        if not kebutuhan["alternatif"]:
            st.caption("Kebutuhan ini belum memiliki alternatif.")

        for alternatif in kebutuhan["alternatif"]:
            with st.container(border=True):
                kunci_nama_alt = f"alt_nama_{alternatif['id']}"
                kunci_harga = f"alt_harga_{alternatif['id']}"
                kunci_kepuasan = f"alt_kepuasan_{alternatif['id']}"
                pastikan_widget(kunci_nama_alt, alternatif["nama"])
                pastikan_widget(kunci_harga, baca_harga(alternatif["harga"]))
                pastikan_widget(kunci_kepuasan, int(alternatif["kepuasan"]))
                st.text_input(
                    "Nama alternatif",
                    key=kunci_nama_alt,
                    placeholder="Laptop A",
                    help="Pilihan untuk kebutuhan ini. Contoh: Laptop A.",
                )
                kolom_harga, kolom_kepuasan = st.columns(2)
                with kolom_harga:
                    st.number_input(
                        "Harga (Rp)",
                        value=None,
                        step=1000.0,
                        placeholder="5000000",
                        key=kunci_harga,
                        help=PESAN_HARGA_TIDAK_VALID,
                    )
                    if not harga_valid(alternatif["harga"]):
                        st.error(PESAN_HARGA_TIDAK_VALID)
                with kolom_kepuasan:
                    st.selectbox(
                        "Kepuasan (1–5)",
                        options=[1, 2, 3, 4, 5],
                        format_func=label_kepuasan,
                        key=kunci_kepuasan,
                        help="Tingkat kepuasan Anda. Contoh: 3 dari 5.",
                    )
                if st.button("Hapus alternatif", key=f"hapus_alt_{alternatif['id']}"):
                    kebutuhan["alternatif"] = [
                        data for data in kebutuhan["alternatif"] if data["id"] != alternatif["id"]
                    ]
                    st.rerun()

        kunci_form_nama = f"form_alt_nama_{kebutuhan['id']}"
        kunci_form_harga = f"form_alt_harga_{kebutuhan['id']}"
        kunci_form_kepuasan = f"form_alt_kepuasan_{kebutuhan['id']}"
        if st.session_state.pop(f"bersihkan_form_alt_{kebutuhan['id']}", False):
            st.session_state[kunci_form_nama] = ""
            st.session_state[kunci_form_harga] = None
            st.session_state[kunci_form_kepuasan] = 3
        if kunci_form_nama not in st.session_state:
            st.session_state[kunci_form_nama] = ""
        if kunci_form_harga not in st.session_state:
            st.session_state[kunci_form_harga] = None
        if kunci_form_kepuasan not in st.session_state:
            st.session_state[kunci_form_kepuasan] = 3
        with st.form(f"form_alt_{kebutuhan['id']}", clear_on_submit=False):
            st.markdown("**Tambah alternatif**")
            st.caption("Contoh: Laptop A, harga 5000000, kepuasan 3 dari 5.")
            nama_alt = st.text_input(
                "Nama alternatif",
                key=kunci_form_nama,
                placeholder="Laptop A",
                help="Pilihan untuk kebutuhan ini. Contoh: Laptop A.",
            )
            kolom_harga, kolom_kepuasan = st.columns(2)
            with kolom_harga:
                harga_alt = st.number_input(
                    "Harga (Rp)",
                    value=None,
                    step=1000.0,
                    placeholder="5000000",
                    key=kunci_form_harga,
                    help=PESAN_HARGA_TIDAK_VALID,
                )
            with kolom_kepuasan:
                kepuasan_alt = st.selectbox(
                    "Kepuasan (1–5)",
                    options=[1, 2, 3, 4, 5],
                    key=kunci_form_kepuasan,
                    format_func=label_kepuasan,
                    help="Tingkat kepuasan Anda. Contoh: 3 dari 5.",
                )
            if st.form_submit_button("Tambah Alternatif"):
                if not str(nama_alt or "").strip():
                    st.error("Nama alternatif tidak boleh kosong.")
                elif any(
                    kunci_nama(data["nama"]) == kunci_nama(str(nama_alt))
                    for data in kebutuhan["alternatif"]
                ):
                    st.error("Nama alternatif sudah digunakan pada kebutuhan ini.")
                elif not harga_valid(harga_alt):
                    st.error(PESAN_HARGA_TIDAK_VALID)
                else:
                    kebutuhan["alternatif"].append(
                        {
                            "id": buat_id(),
                            "nama": str(nama_alt).strip(),
                            "harga": float(harga_alt),
                            "kepuasan": int(kepuasan_alt),
                        }
                    )
                    st.session_state[f"bersihkan_form_alt_{kebutuhan['id']}"] = True
                    st.rerun()


def tampilkan_bobot(persen: int, bobot_harga: float, bobot_kepuasan: float) -> None:
    st.header("Preferensi harga dan kepuasan")
    st.caption("Atur tingkat kepentingan harga dan kepuasan sesuai preferensi Anda.")
    st.slider(
        "Bobot kepuasan (%)",
        min_value=0,
        max_value=100,
        step=1,
        key="bobot_kepuasan_persen",
        help="Bobot harga = 100% dikurangi bobot kepuasan. Total keduanya selalu 100%.",
    )
    kolom_harga, kolom_kepuasan = st.columns(2)
    kolom_harga.metric("Bobot harga", f"{100 - persen}%")
    kolom_kepuasan.metric("Bobot kepuasan", f"{persen}%")
    st.caption(
        f"Total bobot = 100%. Dalam perhitungan: harga {format_skor(bobot_harga)} "
        f"dan kepuasan {format_skor(bobot_kepuasan)}, jumlah "
        f"{format_skor(bobot_harga + bobot_kepuasan)}. "
        "Menggeser slider tidak menghapus nama, harga, atau kepuasan."
    )
    if persen == 50:
        st.caption(
            "Posisi 50% dan 50% adalah titik awal percobaan, bukan bobot yang sudah divalidasi secara ilmiah."
        )


def tampilkan_tabel(hasil: tuple[HasilKebutuhan, ...], persen: int) -> None:
    st.header("Perbandingan alternatif")
    st.caption(
        "Nilai harga hanya dibandingkan dengan alternatif lain pada kebutuhan yang sama."
    )
    if not hasil:
        st.info("Tabel muncul setelah ada kebutuhan yang datanya valid.")
        return

    ada_tabel = False
    for item in hasil:
        st.subheader(item.nama or "(tanpa nama)")
        if not item.valid:
            tampilkan_pesan_hasil(item)
            st.caption("Fitness tidak ditampilkan karena data kebutuhan ini belum valid.")
            continue
        ada_tabel = True
        tampilkan_pesan_hasil(item)
        st.caption(
            f"Bobot yang dipakai: harga {100 - persen}% ({format_skor(item.alternatif[0].bobot_harga)}), "
            f"kepuasan {persen}% ({format_skor(item.alternatif[0].bobot_kepuasan)}). "
            f"Total harga alternatif pada kebutuhan ini: {format_rupiah(item.total_harga)}."
        )
        baris = []
        for alternatif in item.alternatif:
            baris.append(
                {
                    "Nama kebutuhan": item.nama,
                    "Nama alternatif": alternatif.nama,
                    "Harga": format_rupiah(alternatif.harga),
                    "Nilai harga": format_skor(alternatif.nilai_harga),
                    "Nilai kepuasan (1–5)": alternatif.kepuasan,
                    "Skor kepuasan (0–1)": format_skor(alternatif.skor_kepuasan),
                    f"Bobot harga ({100 - persen}%)": format_skor(alternatif.bobot_harga),
                    f"Bobot kepuasan ({persen}%)": format_skor(alternatif.bobot_kepuasan),
                    "Fitness alternatif": format_skor(alternatif.fitness),
                }
            )
        st.dataframe(pd.DataFrame(baris), hide_index=True, width="stretch")
        jumlah_nilai_harga = sum(alternatif.nilai_harga for alternatif in item.alternatif)
        st.caption(
            "Jumlah nilai harga pada kebutuhan ini adalah "
            f"{format_skor(jumlah_nilai_harga)}. Untuk data yang valid, jumlah itu "
            f"sama dengan jumlah alternatif dikurangi satu, yaitu {len(item.alternatif) - 1}."
        )

    if ada_tabel:
        st.caption(
            "Skor ditampilkan dengan empat angka desimal. Harga ditampilkan dalam rupiah. "
            "Bobot pada tabel adalah bobot desimal yang sedang digunakan, bukan bobot tetap."
        )


def tampilkan_peringkat(hasil: tuple[HasilKebutuhan, ...]) -> None:
    st.header("Peringkat dalam setiap kebutuhan")
    st.caption(
        "Peringkat ini hanya berlaku di dalam satu kebutuhan. "
        "Fitness tertinggi di sini belum berarti kombinasi tersebut memenuhi anggaran, "
        "karena batas anggaran belum diterapkan."
    )
    valid = [item for item in hasil if item.valid]
    if not valid:
        st.info("Peringkat muncul setelah ada kebutuhan yang datanya valid.")
        return

    for item in valid:
        st.subheader(item.nama)
        if item.catatan:
            tampilkan_pesan_hasil(item)
        peringkat = peringkat_dalam_kebutuhan(item.alternatif)
        baris = []
        for urutan in peringkat:
            if urutan.tertinggi and sum(1 for data in peringkat if data.tertinggi) > 1:
                keterangan = "Fitness tertinggi pada kebutuhan ini (nilai sama)"
            elif urutan.tertinggi:
                keterangan = "Fitness tertinggi pada kebutuhan ini"
            else:
                keterangan = ""
            baris.append(
                {
                    "Peringkat": urutan.peringkat,
                    "Nama alternatif": urutan.alternatif.nama,
                    "Harga": format_rupiah(urutan.alternatif.harga),
                    "Nilai harga": format_skor(urutan.alternatif.nilai_harga),
                    "Skor kepuasan": format_skor(urutan.alternatif.skor_kepuasan),
                    "Fitness alternatif": format_skor(urutan.alternatif.fitness),
                    "Keterangan": keterangan,
                }
            )
        st.dataframe(pd.DataFrame(baris), hide_index=True, width="stretch")
        gambar = gambar_fitness(item)
        st.pyplot(gambar, clear_figure=True, width="stretch")
        plt.close(gambar)
        st.caption(
            "Batang hijau menandai fitness tertinggi pada kebutuhan ini saja. "
            "Sumbu horizontal adalah fitness alternatif pada rentang 0 sampai 1."
        )


def gambar_fitness(item: HasilKebutuhan):
    urutan = peringkat_dalam_kebutuhan(item.alternatif)
    nama = [baris.alternatif.nama for baris in urutan]
    nilai = [baris.alternatif.fitness for baris in urutan]
    warna = ["#1b7f4e" if baris.tertinggi else "#4c78a8" for baris in urutan]
    gambar, sumbu = plt.subplots(
        figsize=(8, max(2.2, 0.52 * len(nama) + 0.9)),
        constrained_layout=True,
    )
    posisi = list(range(len(nama)))
    sumbu.barh(posisi, nilai, color=warna)
    sumbu.set_yticks(posisi, nama)
    sumbu.invert_yaxis()
    sumbu.set_xlim(0, 1)
    sumbu.set_xlabel("Fitness alternatif")
    sumbu.set_title(f"Fitness alternatif — {item.nama}")
    sumbu.grid(axis="x", linestyle="--", alpha=0.35)
    sumbu.spines["top"].set_visible(False)
    sumbu.spines["right"].set_visible(False)
    for indeks, angka in enumerate(nilai):
        teks = format_skor(angka)
        if angka >= 0.82:
            sumbu.text(
                angka - 0.02,
                indeks,
                teks,
                va="center",
                ha="right",
                color="white",
                fontsize=9,
            )
        else:
            sumbu.text(
                max(angka + 0.02, 0.02),
                indeks,
                teks,
                va="center",
                ha="left",
                color="#17202a",
                fontsize=9,
            )
    return gambar


def tampilkan_ringkasan(kombinasi: HasilKombinasi) -> None:
    st.header("Hasil perhitungan")
    st.caption(
        "Nilai fitness membandingkan kombinasi alternatif berdasarkan bobot harga dan kepuasan. "
        "Angka yang lebih besar lebih unggul pada preferensi yang sedang dipakai. "
        "Ini bukan hasil optimasi Algoritma Genetika."
    )
    if not kombinasi.dihitung:
        st.warning(kombinasi.pesan or "Kombinasi belum dapat dihitung.")
        return

    peringkat_satu = [baris for baris in kombinasi.baris if baris.peringkat == 1]
    if len(peringkat_satu) == 1:
        st.subheader("Kombinasi dengan nilai fitness tertinggi")
    else:
        st.subheader("Kombinasi dengan nilai fitness tertinggi yang sama")

    for baris in peringkat_satu:
        pilihan = ", ".join(f"{nama}: {alternatif}" for nama, alternatif in baris.pilihan)
        st.write(pilihan)
        kolom_harga, kolom_fitness = st.columns(2)
        kolom_harga.metric("Total harga", format_rupiah(baris.total_harga))
        kolom_fitness.metric("Total nilai fitness", format_skor(baris.total_fitness))
    st.caption(
        "Total harga hanya informasi. Total fitness adalah jumlah fitness alternatif yang dipilih, "
        "bukan persentase kepuasan dan bukan persentase penghematan."
    )


def tampilkan_tabel_kombinasi(kombinasi: HasilKombinasi) -> None:
    st.header("Semua kombinasi")
    st.caption(
        f"Setiap baris memilih satu alternatif dari setiap kebutuhan. "
        f"Pencacahan dibatasi {format_jumlah(MAX_KOMBINASI)} kombinasi. "
        "Urutan memakai total fitness, bukan total harga."
    )
    if not kombinasi.dihitung:
        st.caption("Tabel ini muncul setelah setiap kebutuhan memiliki data yang valid.")
        return

    nama_kebutuhan = [nama for nama, _ in kombinasi.baris[0].pilihan]
    records = []
    for baris in kombinasi.baris:
        peta = dict(baris.pilihan)
        record = {"Peringkat": baris.peringkat}
        for nama in nama_kebutuhan:
            record[nama] = peta[nama]
        record["Total harga"] = format_rupiah(baris.total_harga)
        record["Total fitness"] = format_skor(baris.total_fitness)
        records.append(record)
    tabel = pd.DataFrame(records)
    if len(records) > 12:
        st.dataframe(tabel, hide_index=True, width="stretch", height=460)
    else:
        st.dataframe(tabel, hide_index=True, width="stretch")
    if len(records) > 12:
        st.caption("Gulir tabel untuk melihat seluruh kombinasi. Tidak ada kombinasi yang dibuang.")
    if len([baris for baris in kombinasi.baris if baris.peringkat == 1]) > 1:
        st.caption("Beberapa kombinasi memiliki total fitness yang sama, sehingga nomor peringkatnya sama.")


def tampilkan_penjelasan(
    hasil: tuple[HasilKebutuhan, ...],
    kombinasi: HasilKombinasi,
    bobot_harga: float,
    bobot_kepuasan: float,
    persen: int,
) -> None:
    st.header("Penjelasan perhitungan")
    st.caption("Buka bagian yang ingin dipahami. Angka pada data Anda tetap dihitung dengan rumus yang sama.")

    with st.expander("Bagaimana nilai harga dihitung?"):
        st.markdown(
            "Nilai harga membandingkan suatu alternatif dengan alternatif lain "
            "**pada kebutuhan yang sama**. Harga kebutuhan lain tidak dijumlahkan."
        )
        st.latex(r"H_i = 1 - \frac{P_i}{T_k}")
        st.caption("P_i adalah harga alternatif. T_k adalah total harga alternatif pada kebutuhan yang sama.")
        st.markdown(
            "Semakin kecil porsi harganya terhadap total kebutuhan itu, semakin besar nilai harganya. "
            "Nilai mendekati 1 berarti relatif murah di dalam kebutuhannya. "
            "Nilai mendekati 0 berarti harganya memakai porsi yang besar."
        )
        contoh = hitung_nilai_harga([2_000, 3_000, 5_000])
        st.markdown(f"Contoh tetap, total {format_rupiah(10_000)}:")
        if contoh.valid and contoh.nilai is not None:
            for harga, nilai in zip((2_000, 3_000, 5_000), contoh.nilai):
                st.markdown(
                    f"- {format_rupiah(harga)}: 1 − ({format_rupiah(harga)} / "
                    f"{format_rupiah(10_000)}) = {format_skor(nilai)}."
                )

    with st.expander("Bagaimana skor kepuasan dihitung?"):
        st.markdown("Kepuasan diisi dari 1 sampai 5, lalu diubah ke skor 0 sampai 1.")
        st.latex(r"S_i = \frac{R_i - 1}{4}")
        st.caption("R_i adalah kepuasan yang Anda pilih.")
        for nilai in range(1, 6):
            st.markdown(
                f"- {nilai} dari 5: ({nilai} − 1) / 4 = {format_skor(skor_kepuasan(nilai))}."
            )

    with st.expander("Apa arti nilai fitness?"):
        st.markdown(
            "Fitness menggabungkan nilai harga dan skor kepuasan sesuai bobot yang Anda atur. "
            "Fitness alternatif berada pada rentang 0 sampai 1."
        )
        st.latex(r"F_i = w_{harga} \cdot H_i + w_{kepuasan} \cdot S_i")
        st.latex(r"F_{total} = \sum F_i")
        st.markdown(
            "Total fitness kombinasi menjumlahkan fitness satu alternatif dari setiap kebutuhan. "
            "Karena dijumlahkan, totalnya dapat lebih dari 1. Angka itu bukan persentase kepuasan "
            "dan bukan persentase penghematan."
        )
        fitness_contoh = fitness_alternatif(0.8, skor_kepuasan(3), bobot_harga, bobot_kepuasan)
        st.markdown(
            f"Contoh dengan bobot yang sedang aktif (harga {100 - persen}%, kepuasan {persen}%): "
            f"nilai harga 0,8000 dan kepuasan 3 menghasilkan fitness "
            f"({format_skor(bobot_harga)} × 0,8000) + "
            f"({format_skor(bobot_kepuasan)} × {format_skor(skor_kepuasan(3))}) "
            f"= {format_skor(fitness_contoh)}."
        )

    with st.expander("Bagaimana bobot memengaruhi hasil?"):
        st.markdown(
            "Slider mengatur bobot kepuasan dari 0% sampai 100%. "
            "Bobot harga mengikutinya agar keduanya selalu berjumlah 100%."
        )
        st.latex(r"w_{harga} + w_{kepuasan} = 1")
        st.markdown(
            f"Saat ini bobot harga {100 - persen}% ({format_skor(bobot_harga)}) "
            f"dan bobot kepuasan {persen}% ({format_skor(bobot_kepuasan)}). "
            "Menambah bobot kepuasan membuat alternatif yang lebih memuaskan naik, "
            "meski harganya lebih mahal. Menambah bobot harga melakukan sebaliknya. "
            "Posisi awal 50% dan 50% adalah titik percobaan, bukan bobot ilmiah yang sudah final."
        )

    with st.expander("Lihat perhitungan data yang sedang dipakai"):
        if not hasil:
            st.info("Belum ada data. Tambahkan kebutuhan atau muat data contoh.")
        else:
            for item in hasil:
                st.markdown(f"**Kebutuhan {item.nama or '(tanpa nama)'}**")
                if not item.valid or item.total_harga is None:
                    for pesan in item.kesalahan:
                        st.error(pesan)
                    st.caption("Angka kebutuhan ini tidak ditampilkan karena datanya belum valid.")
                    continue
                st.markdown(f"Total harga alternatif = {format_rupiah(item.total_harga)}.")
                for alternatif in item.alternatif:
                    st.markdown(
                        f"- **{alternatif.nama}.** Harga {format_rupiah(alternatif.harga)}. "
                        f"Nilai harga = 1 − ({format_rupiah(alternatif.harga)} / "
                        f"{format_rupiah(item.total_harga)}) = {format_skor(alternatif.nilai_harga)}. "
                        f"Kepuasan {alternatif.kepuasan}, skor = ({alternatif.kepuasan} − 1) / 4 "
                        f"= {format_skor(alternatif.skor_kepuasan)}. "
                        f"Fitness = ({format_skor(alternatif.bobot_harga)} × "
                        f"{format_skor(alternatif.nilai_harga)}) + "
                        f"({format_skor(alternatif.bobot_kepuasan)} × "
                        f"{format_skor(alternatif.skor_kepuasan)}) "
                        f"= {format_skor(alternatif.fitness)}."
                    )
                for _, pesan in item.catatan:
                    st.caption(pesan)
            if not kombinasi.dihitung:
                st.warning(kombinasi.pesan or "Kombinasi belum dapat dijelaskan karena belum dihitung.")
            else:
                st.markdown(
                    "Total fitness kombinasi = jumlah fitness alternatif yang dipilih, "
                    "tepat satu dari setiap kebutuhan."
                )
                peringkat_satu = [baris for baris in kombinasi.baris if baris.peringkat == 1]
                for baris in peringkat_satu[:5]:
                    narasi_kombinasi(hasil, baris)
                if len(peringkat_satu) > 5:
                    st.caption("Kombinasi lain dengan peringkat yang sama ada pada tabel semua kombinasi.")
        st.caption(
            "Angka ditampilkan dengan empat angka desimal. Perhitungan memakai nilai penuh, "
            "lalu hasilnya dibulatkan. Perkalian angka yang sudah dibulatkan kadang selisih 0,0001."
        )


def narasi_kombinasi(hasil: tuple[HasilKebutuhan, ...], baris: BarisKombinasi) -> None:
    bagian = []
    suku_fitness = []
    for nama_kebutuhan, nama_alternatif in baris.pilihan:
        alternatif = cari_alternatif(hasil, nama_kebutuhan, nama_alternatif)
        if alternatif is None:
            bagian.append(f"{nama_kebutuhan}: {nama_alternatif}")
            continue
        bagian.append(
            f"{nama_kebutuhan}: {nama_alternatif} "
            f"(fitness {format_skor(alternatif.fitness)})"
        )
        suku_fitness.append(format_skor(alternatif.fitness))
    suku = " + ".join(suku_fitness)
    st.markdown(
        f"**Peringkat {baris.peringkat}.** {' ; '.join(bagian)}. "
        f"Total fitness = {suku} = {format_skor(baris.total_fitness)}. "
        f"Total harga = {format_rupiah(baris.total_harga)}. "
        "Total harga hanya informasi dan tidak dibandingkan dengan batas anggaran."
    )


def cari_alternatif(hasil: tuple[HasilKebutuhan, ...], nama_kebutuhan: str, nama_alternatif: str):
    for item in hasil:
        if item.nama == nama_kebutuhan:
            for alternatif in item.alternatif:
                if alternatif.nama == nama_alternatif:
                    return alternatif
    return None


if __name__ == "__main__":
    main()
