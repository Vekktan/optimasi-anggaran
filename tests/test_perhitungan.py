"""Pengujian fungsi perhitungan inti.

Pemetaan uji wajib:
1. Harga 2.000, 3.000, dan 5.000 -> nilai harga 0,8; 0,7; 0,5.
2. Harga 7.000 dan 3.000 -> nilai harga 0,3 dan 0,7.
3. Kepuasan 1–5 -> skor 0; 0,25; 0,5; 0,75; 1.
4. Fitness alternatif dengan bobot 50:50.
5. Fitness kombinasi adalah jumlah fitness yang dipilih.
6. Bobot harga dan kepuasan berjumlah 1.
7. Harga negatif dan harga nol ditolak.
8. Total harga nol atau harga tidak valid ditangani tanpa pembagian dengan nol.
9. Kombinasi tidak dihitung jika jumlahnya melebihi 10.000.
"""

import pytest

from perhitungan import (
    MAX_KOMBINASI,
    AlternatifMasukan,
    AlternatifPilihan,
    DataTidakValid,
    KebutuhanMasukan,
    bobot_dari_persen_kepuasan,
    PESAN_HARGA_TIDAK_VALID,
    kombinasi_dari_hasil,
    contoh_sebagai_masukan,
    enumerasi_kombinasi,
    evaluasi_kebutuhan,
    evaluasi_semua,
    fitness_alternatif,
    fitness_kombinasi,
    format_rupiah,
    format_skor,
    harga_valid,
    hitung_nilai_harga,
    skor_kepuasan,
)


def test_nilai_harga_2000_3000_5000():
    hasil = hitung_nilai_harga([2_000, 3_000, 5_000])

    assert hasil.valid is True
    assert hasil.nilai == pytest.approx((0.8, 0.7, 0.5))
    assert sum(hasil.nilai) == pytest.approx(2)


def test_nilai_harga_7000_3000():
    hasil = hitung_nilai_harga([7_000, 3_000])

    assert hasil.valid is True
    assert hasil.nilai == pytest.approx((0.3, 0.7))


def test_skor_kepuasan_skala_1_sampai_5():
    assert skor_kepuasan(1) == pytest.approx(0.0)
    assert skor_kepuasan(2) == pytest.approx(0.25)
    assert skor_kepuasan(3) == pytest.approx(0.5)
    assert skor_kepuasan(4) == pytest.approx(0.75)
    assert skor_kepuasan(5) == pytest.approx(1.0)


@pytest.mark.parametrize("nilai", [0, 6, -1, 3.5, True, False, "5", None])
def test_kepuasan_di_luar_skala_ditolak(nilai):
    with pytest.raises(DataTidakValid, match="1 sampai 5"):
        skor_kepuasan(nilai)


def test_fitness_alternatif_bobot_setengah():
    bobot_harga, bobot_kepuasan = bobot_dari_persen_kepuasan(50)
    skor = skor_kepuasan(3)
    fitness = fitness_alternatif(0.8, skor, bobot_harga, bobot_kepuasan)

    assert bobot_harga == pytest.approx(0.5)
    assert bobot_kepuasan == pytest.approx(0.5)
    assert fitness == pytest.approx(0.65)

    # H = 0,6 dan 0,4 dari harga 2.000 dan 3.000; kepuasan 3 dan 5.
    kebutuhan = evaluasi_kebutuhan(
        "Makan",
        (
            AlternatifMasukan("Nasi", 2_000, 3),
            AlternatifMasukan("Roti", 3_000, 5),
        ),
        bobot_harga,
        bobot_kepuasan,
    )
    assert kebutuhan.valid is True
    assert kebutuhan.alternatif[0].fitness == pytest.approx(0.55)
    assert kebutuhan.alternatif[1].fitness == pytest.approx(0.70)


def test_fitness_kombinasi_adalah_jumlah_fitness_yang_dipilih():
    assert fitness_kombinasi([0.65, 0.80]) == pytest.approx(1.45)
    assert fitness_kombinasi([]) == pytest.approx(0.0)

    bobot_harga, bobot_kepuasan = bobot_dari_persen_kepuasan(50)
    makan = evaluasi_kebutuhan(
        "Makan",
        (
            AlternatifMasukan("Nasi", 2_000, 3),
            AlternatifMasukan("Roti", 3_000, 5),
        ),
        bobot_harga,
        bobot_kepuasan,
    )
    transport = evaluasi_kebutuhan(
        "Transport",
        (
            AlternatifMasukan("Bus", 7_000, 2),
            AlternatifMasukan("Kereta", 3_000, 4),
        ),
        bobot_harga,
        bobot_kepuasan,
    )

    assert makan.alternatif[0].nilai_harga == pytest.approx(0.6)
    assert makan.alternatif[1].nilai_harga == pytest.approx(0.4)
    assert transport.alternatif[0].nilai_harga == pytest.approx(0.3)
    assert transport.alternatif[1].nilai_harga == pytest.approx(0.7)
    assert transport.alternatif[0].fitness == pytest.approx(0.275)
    assert transport.alternatif[1].fitness == pytest.approx(0.725)

    kombinasi = kombinasi_dari_hasil((makan, transport))
    assert kombinasi.dihitung is True
    assert kombinasi.jumlah == 4

    for baris in kombinasi.baris:
        terpilih = []
        total_harga = 0.0
        for nama_kebutuhan, nama_alternatif in baris.pilihan:
            sumber = makan if nama_kebutuhan == "Makan" else transport
            alternatif = next(
                item for item in sumber.alternatif if item.nama == nama_alternatif
            )
            terpilih.append(alternatif.fitness)
            total_harga += alternatif.harga
        assert baris.total_fitness == pytest.approx(fitness_kombinasi(terpilih))
        assert baris.total_harga == pytest.approx(total_harga)

    fitness_urutan = [baris.total_fitness for baris in kombinasi.baris]
    assert fitness_urutan == sorted(fitness_urutan, reverse=True)
    assert kombinasi.baris[0].pilihan == (
        ("Makan", "Roti"),
        ("Transport", "Kereta"),
    )
    assert kombinasi.baris[0].total_fitness == pytest.approx(1.425)


@pytest.mark.parametrize("persen", list(range(0, 101)))
def test_bobot_harga_dan_kepuasan_berjumlah_satu(persen):
    bobot_harga, bobot_kepuasan = bobot_dari_persen_kepuasan(persen)

    assert bobot_kepuasan == pytest.approx(persen / 100)
    assert bobot_harga == pytest.approx(1 - (persen / 100))
    assert bobot_harga + bobot_kepuasan == pytest.approx(1.0)


def test_bobot_di_luar_rentang_ditolak():
    with pytest.raises(DataTidakValid):
        bobot_dari_persen_kepuasan(-0.1)
    with pytest.raises(DataTidakValid):
        bobot_dari_persen_kepuasan(100.1)


def test_fitness_menolak_bobot_yang_tidak_berjumlah_satu():
    with pytest.raises(DataTidakValid, match="berjumlah 1"):
        fitness_alternatif(0.8, 0.5, 0.2, 0.2)


def test_harga_negatif_ditolak():
    hasil = hitung_nilai_harga([2_000, -1, 3_000])

    assert hasil.valid is False
    assert hasil.nilai is None
    assert hasil.pesan == PESAN_HARGA_TIDAK_VALID

    evaluasi = evaluasi_kebutuhan(
        "Makan",
        (
            AlternatifMasukan("A", -1_000, 3),
            AlternatifMasukan("B", 2_000, 4),
        ),
        0.5,
        0.5,
    )
    assert evaluasi.valid is False
    assert evaluasi.alternatif == ()
    assert any(PESAN_HARGA_TIDAK_VALID in pesan for pesan in evaluasi.kesalahan)
    assert kombinasi_dari_hasil((evaluasi,)).dihitung is False


@pytest.mark.parametrize("harga", [[0], [0, 0], [0.0, 0.0, 0.0], [None], [0, None, -5]])
def test_total_harga_nol_aman(harga):
    hasil = hitung_nilai_harga(harga)

    assert hasil.valid is False
    assert hasil.nilai is None
    assert hasil.pesan == PESAN_HARGA_TIDAK_VALID

    evaluasi = evaluasi_kebutuhan(
        "Makan",
        tuple(AlternatifMasukan(f"Menu {i}", nilai, 3) for i, nilai in enumerate(harga, start=1)),
        0.5,
        0.5,
    )
    assert evaluasi.valid is False
    assert evaluasi.alternatif == ()
    assert evaluasi.total_harga is None
    assert kombinasi_dari_hasil((evaluasi,)).baris == ()


def test_kombinasi_tidak_dihitung_jika_melebihi_10000():
    kelompok = [
        [AlternatifPilihan("A", str(i), 1.0, 0.01) for i in range(101)],
        [AlternatifPilihan("B", str(i), 1.0, 0.01) for i in range(100)],
    ]

    hasil = enumerasi_kombinasi(kelompok)

    assert 101 * 100 == 10_100
    assert hasil.jumlah == 10_100
    assert hasil.jumlah > MAX_KOMBINASI
    assert hasil.dihitung is False
    assert hasil.baris == ()
    assert "10.100" in hasil.pesan
    assert "10.000" in hasil.pesan


def test_kombinasi_tepat_pada_batas_masih_dihitung():
    kelompok = [
        [AlternatifPilihan("A", str(i), 1.0, 0.01) for i in range(100)],
        [AlternatifPilihan("B", str(i), 1.0, 0.01) for i in range(100)],
    ]

    hasil = enumerasi_kombinasi(kelompok)

    assert hasil.jumlah == MAX_KOMBINASI
    assert hasil.dihitung is True
    assert len(hasil.baris) == MAX_KOMBINASI
    assert {baris.peringkat for baris in hasil.baris} == {1}


def test_satu_alternatif_nilai_harga_nol_tanpa_pembagian_nol():
    hasil = hitung_nilai_harga([4_000])

    assert hasil.valid is True
    assert hasil.satu_alternatif is True
    assert hasil.nilai == pytest.approx((0.0,))

    evaluasi = evaluasi_kebutuhan(
        "Buku",
        (AlternatifMasukan("Buku A", 4_000, 5),),
        0.5,
        0.5,
    )
    assert evaluasi.valid is True
    assert evaluasi.alternatif[0].nilai_harga == pytest.approx(0.0)
    assert evaluasi.alternatif[0].fitness == pytest.approx(0.5)
    assert evaluasi.catatan[0][0] == "info"


def test_harga_nol_dan_kosong_tidak_masuk_perhitungan():
    assert harga_valid(None) is False
    assert harga_valid(0) is False
    assert harga_valid(-1) is False
    assert harga_valid(1_000) is True

    hasil = hitung_nilai_harga([0, 1_000])
    assert hasil.valid is False
    assert hasil.nilai is None
    assert hasil.pesan == PESAN_HARGA_TIDAK_VALID

    evaluasi = evaluasi_kebutuhan(
        "Laptop",
        (
            AlternatifMasukan("Laptop A", 5_000_000, 3),
            AlternatifMasukan("Laptop D", 0, 4),
            AlternatifMasukan("Laptop B", 8_000_000, 5),
        ),
        *bobot_dari_persen_kepuasan(50),
    )
    assert evaluasi.valid is False
    assert evaluasi.alternatif == ()
    assert any("Laptop D" in pesan for pesan in evaluasi.kesalahan)
    assert all(alternatif.fitness != pytest.approx(0.75) for alternatif in evaluasi.alternatif)

    kosong = evaluasi_kebutuhan(
        "Laptop",
        (
            AlternatifMasukan("Laptop A", 5_000_000, 3),
            AlternatifMasukan("Laptop D", None, 4),
        ),
        0.5,
        0.5,
    )
    assert kosong.valid is False
    assert kosong.alternatif == ()
    assert any("Laptop D" in pesan and PESAN_HARGA_TIDAK_VALID in pesan for pesan in kosong.kesalahan)

    kombinasi = kombinasi_dari_hasil((evaluasi, kosong))
    assert kombinasi.dihitung is False
    assert kombinasi.baris == ()


def test_nilai_harga_dihitung_terpisah_per_kebutuhan():
    bobot_harga, bobot_kepuasan = bobot_dari_persen_kepuasan(50)
    hasil = evaluasi_semua(contoh_sebagai_masukan(), bobot_harga, bobot_kepuasan)
    laptop, kost = hasil

    assert laptop.total_harga == pytest.approx(23_000_000)
    assert laptop.alternatif[0].nilai_harga == pytest.approx(1 - (5_000_000 / 23_000_000))
    assert kost.total_harga == pytest.approx(4_000_000)
    assert kost.alternatif[0].nilai_harga == pytest.approx(0.8)
    assert sum(item.nilai_harga for item in laptop.alternatif) == pytest.approx(2)
    assert sum(item.nilai_harga for item in kost.alternatif) == pytest.approx(2)


def test_tampilan_dan_peringkat_data_contoh():
    hasil = evaluasi_semua(contoh_sebagai_masukan(), *bobot_dari_persen_kepuasan(50))
    laptop = {item.nama: item for item in hasil[0].alternatif}
    kost = {item.nama: item for item in hasil[1].alternatif}

    assert format_skor(laptop["Laptop A"].nilai_harga) == "0,7826"
    assert format_skor(laptop["Laptop A"].skor_kepuasan) == "0,5000"
    assert format_skor(laptop["Laptop A"].fitness) == "0,6413"
    assert format_skor(laptop["Laptop B"].nilai_harga) == "0,6522"
    assert format_skor(laptop["Laptop B"].fitness) == "0,8261"
    assert format_skor(laptop["Laptop C"].nilai_harga) == "0,5652"
    assert format_skor(laptop["Laptop C"].fitness) == "0,6576"
    assert format_rupiah(laptop["Laptop A"].harga) == "Rp5.000.000"

    assert format_skor(kost["Kost A"].nilai_harga) == "0,8000"
    assert format_skor(kost["Kost A"].fitness) == "0,7750"
    assert format_skor(kost["Kost B"].nilai_harga) == "0,7000"
    assert format_skor(kost["Kost B"].fitness) == "0,8500"
    assert format_skor(kost["Kost C"].nilai_harga) == "0,5000"
    assert format_skor(kost["Kost C"].fitness) == "0,5000"
    assert format_rupiah(kost["Kost B"].harga) == "Rp1.200.000"

    kombinasi = kombinasi_dari_hasil(hasil)
    assert kombinasi.dihitung is True
    assert kombinasi.jumlah == 9
    assert [
        (
            baris.peringkat,
            baris.pilihan,
            format_rupiah(baris.total_harga),
            format_skor(baris.total_fitness),
        )
        for baris in kombinasi.baris
    ] == [
        (1, (("Laptop", "Laptop B"), ("Kost", "Kost B")), "Rp9.200.000", "1,6761"),
        (2, (("Laptop", "Laptop B"), ("Kost", "Kost A")), "Rp8.800.000", "1,6011"),
        (3, (("Laptop", "Laptop C"), ("Kost", "Kost B")), "Rp11.200.000", "1,5076"),
        (4, (("Laptop", "Laptop A"), ("Kost", "Kost B")), "Rp6.200.000", "1,4913"),
        (5, (("Laptop", "Laptop C"), ("Kost", "Kost A")), "Rp10.800.000", "1,4326"),
        (6, (("Laptop", "Laptop A"), ("Kost", "Kost A")), "Rp5.800.000", "1,4163"),
        (7, (("Laptop", "Laptop B"), ("Kost", "Kost C")), "Rp10.000.000", "1,3261"),
        (8, (("Laptop", "Laptop C"), ("Kost", "Kost C")), "Rp12.000.000", "1,1576"),
        (9, (("Laptop", "Laptop A"), ("Kost", "Kost C")), "Rp7.000.000", "1,1413"),
    ]


def test_peringkat_individu_berubah_saat_bobot_berubah():
    alternatif = (
        AlternatifMasukan("Murah", 2_000, 1),
        AlternatifMasukan("Mahal", 8_000, 5),
    )
    penuh_harga = evaluasi_kebutuhan("Kebutuhan", alternatif, *bobot_dari_persen_kepuasan(0))
    penuh_kepuasan = evaluasi_kebutuhan(
        "Kebutuhan", alternatif, *bobot_dari_persen_kepuasan(100)
    )

    assert penuh_harga.alternatif[0].fitness == pytest.approx(0.8)
    assert penuh_harga.alternatif[1].fitness == pytest.approx(0.2)
    assert penuh_kepuasan.alternatif[0].fitness == pytest.approx(0.0)
    assert penuh_kepuasan.alternatif[1].fitness == pytest.approx(1.0)


def test_kombinasi_tidak_disusun_dari_data_tidak_valid():
    baik = evaluasi_kebutuhan(
        "Buku",
        (AlternatifMasukan("Buku A", 4_000, 5),),
        0.5,
        0.5,
    )
    buruk = evaluasi_kebutuhan(
        "Transport",
        (AlternatifMasukan("Bus", -10, 3),),
        0.5,
        0.5,
    )
    hasil = kombinasi_dari_hasil((baik, buruk))

    assert baik.valid is True
    assert buruk.valid is False
    assert hasil.dihitung is False
    assert hasil.baris == ()
    assert "10.000" not in hasil.pesan


def test_nama_duplikat_dan_kebutuhan_tanpa_alternatif():
    hasil = evaluasi_semua(
        (
            KebutuhanMasukan(
                "Laptop",
                (
                    AlternatifMasukan("A", 2_000, 3),
                    AlternatifMasukan("a", 3_000, 4),
                ),
            ),
            KebutuhanMasukan("laptop", (AlternatifMasukan("B", 1_000, 5),)),
            KebutuhanMasukan("Kosong", ()),
        ),
        0.5,
        0.5,
    )

    assert all(not item.valid for item in hasil)
    assert hasil[2].alternatif == ()
    kombinasi = kombinasi_dari_hasil(hasil)
    assert kombinasi.dihitung is False
    assert kombinasi.baris == ()


def test_format_skor_dan_rupiah():
    assert format_skor(0.8) == "0,8000"
    assert format_skor(0.25) == "0,2500"
    assert format_skor(1) == "1,0000"
    assert format_rupiah(5_000_000) == "Rp5.000.000"
    assert format_rupiah(800_000) == "Rp800.000"
    assert format_rupiah(1_234.5) == "Rp1.234,50"
    assert format_rupiah(-1_500) == "-Rp1.500"
