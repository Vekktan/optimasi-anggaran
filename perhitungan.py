"""Perhitungan nilai harga, skor kepuasan, dan fitness.

Modul ini dipakai oleh antarmuka dan oleh pengujian otomatis.
Algoritma Genetika, batas anggaran, basis data, dan login tidak ada di sini.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product
from typing import Sequence

MAX_KOMBINASI = 10_000
_TOLERANSI = 1e-9
_TOLERANSI_PERINGKAT = 1e-12
PESAN_HARGA_TIDAK_VALID = (
    "Harga harus lebih besar dari Rp0. Jika data belum diisi, lengkapi harga terlebih dahulu."
)


class DataTidakValid(ValueError):
    """Input tidak dapat dihitung dengan aman."""


CONTOH_KEBUTUHAN = (
    {
        "nama": "Laptop",
        "alternatif": (
            {"nama": "Laptop A", "harga": 5_000_000, "kepuasan": 3},
            {"nama": "Laptop B", "harga": 8_000_000, "kepuasan": 5},
            {"nama": "Laptop C", "harga": 10_000_000, "kepuasan": 4},
        ),
    },
    {
        "nama": "Kost",
        "alternatif": (
            {"nama": "Kost A", "harga": 800_000, "kepuasan": 4},
            {"nama": "Kost B", "harga": 1_200_000, "kepuasan": 5},
            {"nama": "Kost C", "harga": 2_000_000, "kepuasan": 3},
        ),
    },
)


@dataclass(frozen=True)
class AlternatifMasukan:
    nama: str
    harga: float | None
    kepuasan: int


@dataclass(frozen=True)
class KebutuhanMasukan:
    nama: str
    alternatif: tuple[AlternatifMasukan, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "alternatif", tuple(self.alternatif))


@dataclass(frozen=True)
class HasilNilaiHarga:
    nilai: tuple[float, ...] | None
    valid: bool
    pesan: str | None
    satu_alternatif: bool = False
    ada_harga_nol: bool = False


@dataclass(frozen=True)
class AlternatifHasil:
    nama: str
    harga: float
    nilai_harga: float
    kepuasan: int
    skor_kepuasan: float
    bobot_harga: float
    bobot_kepuasan: float
    fitness: float


@dataclass(frozen=True)
class HasilKebutuhan:
    nama: str
    valid: bool
    kesalahan: tuple[str, ...]
    catatan: tuple[tuple[str, str], ...]
    total_harga: float | None
    alternatif: tuple[AlternatifHasil, ...]


@dataclass(frozen=True)
class AlternatifPilihan:
    kebutuhan: str
    nama: str
    harga: float
    fitness: float


@dataclass(frozen=True)
class BarisKombinasi:
    peringkat: int
    pilihan: tuple[tuple[str, str], ...]
    total_harga: float
    total_fitness: float


@dataclass(frozen=True)
class HasilKombinasi:
    dihitung: bool
    jumlah: int
    pesan: str | None
    baris: tuple[BarisKombinasi, ...]


@dataclass(frozen=True)
class BarisPeringkat:
    peringkat: int
    alternatif: AlternatifHasil
    tertinggi: bool


def kunci_nama(nama: str) -> str:
    """Kunci pembanding nama: tanpa beda huruf besar dan spasi berlebih."""
    if not isinstance(nama, str):
        return ""
    return " ".join(nama.strip().lower().split())


def format_skor(nilai: float) -> str:
    """Menampilkan skor dengan empat angka desimal dan koma desimal."""
    return f"{float(nilai):.4f}".replace(".", ",")


def format_rupiah(nilai: float) -> str:
    """Menampilkan harga dalam rupiah, misalnya Rp5.000.000."""
    angka = _sebagai_angka(nilai)
    if angka is None:
        return "Rp-"
    negatif = angka < 0
    angka = abs(angka)
    if abs(angka - round(angka)) < 1e-6:
        tubuh = f"{int(round(angka)):,}".replace(",", ".")
    else:
        tubuh = f"{angka:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-Rp{tubuh}" if negatif else f"Rp{tubuh}"


def format_jumlah(jumlah: int) -> str:
    """Menampilkan bilangan bulat dengan pemisah ribuan."""
    if jumlah > 1_000_000_000_000:
        return "lebih dari 1.000.000.000.000"
    return f"{jumlah:,}".replace(",", ".")


def harga_valid(nilai: object) -> bool:
    """Harga alternatif valid hanya jika berupa angka yang lebih besar dari nol."""
    angka = _sebagai_angka(nilai)
    return angka is not None and angka > 0


def hitung_nilai_harga(harga: Sequence[float]) -> HasilNilaiHarga:
    """Menghitung H_i = 1 - (P_i / total harga) untuk satu kebutuhan.

    Daftar harga yang diberikan harus berasal dari kebutuhan yang sama.
    Fungsi ini tidak menjumlahkan harga dari kebutuhan lain.
    Harga kosong, nol, atau negatif tidak dihitung, sehingga tidak ada
    pembagian dengan nol.
    """
    if len(harga) == 0:
        return HasilNilaiHarga(
            None,
            False,
            "Kebutuhan belum memiliki alternatif.",
            False,
            False,
        )

    angka: list[float] = []
    for nilai in harga:
        if not harga_valid(nilai):
            return HasilNilaiHarga(
                None,
                False,
                PESAN_HARGA_TIDAK_VALID,
                False,
                False,
            )
        angka.append(float(nilai))

    total = math.fsum(angka)
    if total <= 0:
        return HasilNilaiHarga(
            None,
            False,
            PESAN_HARGA_TIDAK_VALID,
            False,
            False,
        )

    nilai = tuple(1.0 - (p / total) for p in angka)
    if len(angka) == 1:
        return HasilNilaiHarga(
            nilai,
            True,
            (
                "Kebutuhan ini hanya memiliki satu alternatif. Nilai harga adalah "
                "0,0000 karena harga alternatif sama dengan total harga pada "
                "kebutuhan ini. Angka tersebut bukan penilaian bahwa harganya buruk, "
                "melainkan tanda bahwa belum ada alternatif pembanding. Pembagian "
                "dengan nol tidak terjadi."
            ),
            True,
            False,
        )
    return HasilNilaiHarga(nilai, True, None, False, False)


def skor_kepuasan(nilai: int) -> float:
    """Mengubah kepuasan 1–5 menjadi skor 0–1: S = (R - 1) / 4."""
    angka = _pastikan_kepuasan(nilai)
    return (angka - 1) / 4


def bobot_dari_persen_kepuasan(persen_kepuasan: float) -> tuple[float, float]:
    """Mengembalikan (bobot harga, bobot kepuasan) yang jumlahnya 1.

    Bobot harga = 1 - bobot kepuasan. Bobot kepuasan berasal dari persen / 100.
    """
    angka = _sebagai_angka(persen_kepuasan)
    if angka is None or angka < 0 or angka > 100:
        raise DataTidakValid("Bobot kepuasan harus berada pada rentang 0% sampai 100%.")
    bobot_kepuasan = angka / 100.0
    bobot_harga = 1.0 - bobot_kepuasan
    return bobot_harga, bobot_kepuasan


def fitness_alternatif(
    nilai_harga: float,
    skor: float,
    bobot_harga: float,
    bobot_kepuasan: float,
) -> float:
    """F_i = (bobot harga × nilai harga) + (bobot kepuasan × skor kepuasan)."""
    harga = _sebagai_angka(nilai_harga)
    kepuasan = _sebagai_angka(skor)
    w_harga = _sebagai_angka(bobot_harga)
    w_kepuasan = _sebagai_angka(bobot_kepuasan)
    if None in (harga, kepuasan, w_harga, w_kepuasan):
        raise DataTidakValid("Fitness hanya dapat dihitung dari angka yang valid.")
    if abs((w_harga + w_kepuasan) - 1.0) > _TOLERANSI:
        raise DataTidakValid("Bobot harga dan bobot kepuasan harus berjumlah 1.")
    return (w_harga * harga) + (w_kepuasan * kepuasan)


def fitness_kombinasi(daftar_fitness: Sequence[float]) -> float:
    """Total fitness kombinasi adalah jumlah fitness alternatif yang dipilih."""
    return float(math.fsum(daftar_fitness))


def evaluasi_kebutuhan(
    nama: str,
    alternatif: Sequence[AlternatifMasukan],
    bobot_harga: float,
    bobot_kepuasan: float,
    *,
    nama_duplikat: bool = False,
) -> HasilKebutuhan:
    """Memvalidasi satu kebutuhan dan menghitung fitness jika datanya sah."""
    kesalahan: list[str] = []
    nama_bersih = nama.strip() if isinstance(nama, str) else ""
    if not nama_bersih:
        kesalahan.append("Nama kebutuhan tidak boleh kosong.")

    bobot_harga_angka = _sebagai_angka(bobot_harga)
    bobot_kepuasan_angka = _sebagai_angka(bobot_kepuasan)
    if (
        bobot_harga_angka is None
        or bobot_kepuasan_angka is None
        or abs((bobot_harga_angka + bobot_kepuasan_angka) - 1.0) > _TOLERANSI
    ):
        kesalahan.append("Bobot harga dan bobot kepuasan harus berjumlah 1.")

    if nama_duplikat and nama_bersih:
        kesalahan.append(
            f'Nama kebutuhan "{nama_bersih}" sudah digunakan pada kebutuhan lain. '
            "Gunakan nama yang berbeda."
        )

    if len(alternatif) == 0:
        kesalahan.append(
            "Kebutuhan belum memiliki alternatif. Tambahkan minimal satu alternatif."
        )
        return _tidak_valid(nama_bersih, kesalahan)

    harga_siap: list[float] = []
    kepuasan_siap: list[int] = []
    nama_siap: list[str] = []
    harga_dapat_dihitung = True
    sudah_terlihat: dict[str, list[int]] = {}

    for indeks, item in enumerate(alternatif, start=1):
        nama_alt = item.nama.strip() if isinstance(item.nama, str) else ""
        label = f"Alternatif ke-{indeks}"
        if nama_alt:
            label = f"{label} ({nama_alt})"
        else:
            kesalahan.append(f"Alternatif ke-{indeks}: nama tidak boleh kosong.")

        kunci = kunci_nama(nama_alt)
        if kunci:
            sudah_terlihat.setdefault(kunci, []).append(indeks)

        if not harga_valid(item.harga):
            kesalahan.append(f"{label}: {PESAN_HARGA_TIDAK_VALID}")
            harga_dapat_dihitung = False
        else:
            harga_siap.append(float(item.harga))

        try:
            kepuasan_siap.append(_pastikan_kepuasan(item.kepuasan))
        except DataTidakValid as exc:
            kesalahan.append(f"{label}: {exc}")
            harga_dapat_dihitung = False

        nama_siap.append(nama_alt)

    for nomor in sudah_terlihat.values():
        if len(nomor) > 1:
            nama_tampil = nama_siap[nomor[0] - 1]
            kesalahan.append(
                f'Nama alternatif "{nama_tampil}" dipakai lebih dari satu kali '
                f"({_gabung_nomor(nomor)}). Gunakan nama yang berbeda."
            )

    if kesalahan or not harga_dapat_dihitung:
        return _tidak_valid(nama_bersih, kesalahan)

    hasil_harga = hitung_nilai_harga(harga_siap)
    if not hasil_harga.valid or hasil_harga.nilai is None:
        kesalahan.append(
            hasil_harga.pesan
            or "Nilai harga tidak dapat dihitung dari harga yang dimasukkan."
        )
        return _tidak_valid(nama_bersih, kesalahan)

    catatan: list[tuple[str, str]] = []
    if hasil_harga.satu_alternatif and hasil_harga.pesan:
        catatan.append(("info", hasil_harga.pesan))

    hasil_alternatif: list[AlternatifHasil] = []
    for nama_alt, harga, kepuasan, nilai_harga in zip(
        nama_siap, harga_siap, kepuasan_siap, hasil_harga.nilai
    ):
        skor = skor_kepuasan(kepuasan)
        fitness = fitness_alternatif(
            nilai_harga, skor, bobot_harga_angka, bobot_kepuasan_angka
        )
        hasil_alternatif.append(
            AlternatifHasil(
                nama=nama_alt,
                harga=harga,
                nilai_harga=nilai_harga,
                kepuasan=kepuasan,
                skor_kepuasan=skor,
                bobot_harga=bobot_harga_angka,
                bobot_kepuasan=bobot_kepuasan_angka,
                fitness=fitness,
            )
        )

    return HasilKebutuhan(
        nama=nama_bersih,
        valid=True,
        kesalahan=(),
        catatan=tuple(catatan),
        total_harga=float(math.fsum(harga_siap)),
        alternatif=tuple(hasil_alternatif),
    )


def evaluasi_semua(
    daftar: Sequence[KebutuhanMasukan],
    bobot_harga: float,
    bobot_kepuasan: float,
) -> tuple[HasilKebutuhan, ...]:
    """Mengevaluasi setiap kebutuhan secara terpisah."""
    kunci = [
        kunci_nama(item.nama) if isinstance(item.nama, str) else "" for item in daftar
    ]
    hasil = []
    for indeks, item in enumerate(daftar):
        duplikat = kunci[indeks] != "" and kunci.count(kunci[indeks]) > 1
        hasil.append(
            evaluasi_kebutuhan(
                item.nama,
                item.alternatif,
                bobot_harga,
                bobot_kepuasan,
                nama_duplikat=duplikat,
            )
        )
    return tuple(hasil)


def enumerasi_kombinasi(
    kelompok: Sequence[Sequence[AlternatifPilihan]],
) -> HasilKombinasi:
    """Menghitung seluruh kombinasi jika jumlahnya tidak melebihi batas.

    Setiap kelompok adalah alternatif dari satu kebutuhan. Satu kombinasi
    memilih tepat satu alternatif dari setiap kelompok. Jika jumlah kombinasi
    lebih dari 10.000, tidak ada kombinasi yang dihitung.
    """
    if len(kelompok) == 0:
        return HasilKombinasi(
            False,
            0,
            (
                "Belum ada kebutuhan. Tambahkan kebutuhan atau muat data contoh "
                "agar kombinasi dapat dihitung."
            ),
            (),
        )
    if any(len(grup) == 0 for grup in kelompok):
        return HasilKombinasi(
            False,
            0,
            "Ada kebutuhan tanpa alternatif, sehingga kombinasi belum dihitung.",
            (),
        )

    jumlah = 1
    for grup in kelompok:
        jumlah *= len(grup)

    if jumlah > MAX_KOMBINASI:
        return HasilKombinasi(
            False,
            jumlah,
            (
                f"Ada {format_jumlah(jumlah)} kombinasi. Prototipe ini hanya "
                f"menghitung kombinasi jika jumlahnya tidak melebihi "
                f"{format_jumlah(MAX_KOMBINASI)}. Perhitungan kombinasi tidak "
                "dijalankan agar aplikasi tidak menjadi lambat."
            ),
            (),
        )

    mentah: list[tuple[float, float, tuple[tuple[str, str], ...]]] = []
    for pilihan in product(*kelompok):
        total_fitness = fitness_kombinasi([item.fitness for item in pilihan])
        total_harga = float(math.fsum(item.harga for item in pilihan))
        identitas = tuple((item.kebutuhan, item.nama) for item in pilihan)
        mentah.append((total_fitness, total_harga, identitas))

    mentah.sort(key=lambda item: (-item[0], item[2]))
    baris: list[BarisKombinasi] = []
    peringkat = 1
    for indeks, (total_fitness, total_harga, identitas) in enumerate(mentah):
        if indeks > 0 and abs(total_fitness - mentah[indeks - 1][0]) > _TOLERANSI_PERINGKAT:
            peringkat = indeks + 1
        baris.append(
            BarisKombinasi(
                peringkat=peringkat,
                pilihan=identitas,
                total_harga=total_harga,
                total_fitness=total_fitness,
            )
        )
    return HasilKombinasi(True, jumlah, None, tuple(baris))


def kombinasi_dari_hasil(hasil: Sequence[HasilKebutuhan]) -> HasilKombinasi:
    """Menyusun kombinasi hanya jika setiap kebutuhan datanya valid."""
    if len(hasil) == 0:
        return HasilKombinasi(
            False,
            0,
            (
                "Belum ada kebutuhan. Tambahkan kebutuhan atau muat data contoh "
                "agar kombinasi dapat dihitung."
            ),
            (),
        )

    tidak_valid = []
    for item in hasil:
        if not item.valid:
            tidak_valid.append(item.nama.strip() or "(tanpa nama)")
    if tidak_valid:
        return HasilKombinasi(
            False,
            0,
            (
                "Kombinasi belum dihitung karena masih ada kebutuhan yang datanya "
                f"belum valid: {_gabung_kalimat(tidak_valid)}. Fitness dari data "
                "yang belum valid tidak ditampilkan, dan kombinasi yang melewati "
                "kebutuhan tersebut tidak disusun."
            ),
            (),
        )

    kelompok = [
        tuple(
            AlternatifPilihan(
                kebutuhan=item.nama,
                nama=alternatif.nama,
                harga=alternatif.harga,
                fitness=alternatif.fitness,
            )
            for alternatif in item.alternatif
        )
        for item in hasil
    ]
    return enumerasi_kombinasi(kelompok)


def peringkat_dalam_kebutuhan(
    alternatif: Sequence[AlternatifHasil],
) -> tuple[BarisPeringkat, ...]:
    """Mengurutkan alternatif pada satu kebutuhan dari fitness tertinggi."""
    if len(alternatif) == 0:
        return ()
    urut = sorted(alternatif, key=lambda item: (-item.fitness, item.nama))
    baris: list[BarisPeringkat] = []
    peringkat = 1
    for indeks, item in enumerate(urut):
        if indeks > 0 and abs(item.fitness - urut[indeks - 1].fitness) > _TOLERANSI_PERINGKAT:
            peringkat = indeks + 1
        tertinggi = abs(item.fitness - urut[0].fitness) <= _TOLERANSI_PERINGKAT
        baris.append(BarisPeringkat(peringkat, item, tertinggi))
    return tuple(baris)


def contoh_sebagai_masukan() -> tuple[KebutuhanMasukan, ...]:
    """Data simulasi Laptop dan Kost untuk percobaan awal."""
    return tuple(
        KebutuhanMasukan(
            blok["nama"],
            tuple(
                AlternatifMasukan(item["nama"], item["harga"], item["kepuasan"])
                for item in blok["alternatif"]
            ),
        )
        for blok in CONTOH_KEBUTUHAN
    )


def _tidak_valid(nama: str, kesalahan: list[str]) -> HasilKebutuhan:
    return HasilKebutuhan(nama, False, tuple(kesalahan), (), None, ())


def _sebagai_angka(nilai: object) -> float | None:
    if isinstance(nilai, bool) or nilai is None:
        return None
    if isinstance(nilai, (int, float)):
        angka = float(nilai)
    else:
        nama_tipe = type(nilai).__name__
        if not nama_tipe.startswith(("int", "float")):
            return None
        try:
            angka = float(nilai)
        except (TypeError, ValueError):
            return None
    if not math.isfinite(angka):
        return None
    return angka


def _pastikan_kepuasan(nilai: object) -> int:
    if isinstance(nilai, bool) or nilai is None:
        raise DataTidakValid("nilai kepuasan harus bilangan bulat 1 sampai 5.")
    if isinstance(nilai, int):
        angka = nilai
    elif isinstance(nilai, float):
        if not nilai.is_integer():
            raise DataTidakValid("nilai kepuasan harus bilangan bulat 1 sampai 5.")
        angka = int(nilai)
    else:
        nama_tipe = type(nilai).__name__
        if nama_tipe.startswith("int"):
            try:
                angka = int(nilai)
            except (TypeError, ValueError) as exc:
                raise DataTidakValid(
                    "nilai kepuasan harus bilangan bulat 1 sampai 5."
                ) from exc
        else:
            raise DataTidakValid("nilai kepuasan harus bilangan bulat 1 sampai 5.")
    if angka < 1 or angka > 5:
        raise DataTidakValid("nilai kepuasan harus bilangan bulat 1 sampai 5.")
    return angka


def _gabung_nomor(nomor: Sequence[int]) -> str:
    teks = [f"ke-{item}" for item in nomor]
    return _gabung_kalimat(teks)


def _gabung_kalimat(bagian: Sequence[str]) -> str:
    if len(bagian) == 0:
        return ""
    if len(bagian) == 1:
        return bagian[0]
    if len(bagian) == 2:
        return f"{bagian[0]} dan {bagian[1]}"
    return ", ".join(bagian[:-1]) + f", dan {bagian[-1]}"
