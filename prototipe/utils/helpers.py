import locale
from datetime import datetime

locale.setlocale(locale.LC_TIME, 'id_ID.utf8')

def format_wa_number(no_wa: str) -> str:
    """Memformat nomor WhatsApp."""
    no_wa = no_wa.strip()
    if no_wa.startswith("0"):
        return "62" + no_wa[1:]
    return no_wa

def salam_waktu():
    """Mengembalikan salam sesuai waktu."""
    jam = datetime.now().hour
    if 4 <= jam < 11:
        return "Selamat Pagi"
    elif 11 <= jam < 15:
        return "Selamat Siang"
    elif 15 <= jam < 18:
        return "Selamat Sore"
    else:
        return "Selamat Malam"

def panggilan_sopan(jenis_kelamin: str) -> str:
    """Mengembalikan panggilan sopan berdasarkan jenis kelamin."""
    if not jenis_kelamin:
        return "Bapak/Ibu"
    jenis_kelamin = jenis_kelamin.strip().lower()
    if jenis_kelamin in ['l', 'laki-laki', 'laki']:
        return "Bapak"
    elif jenis_kelamin in ['p', 'perempuan', 'wanita']:
        return "Ibu"
    else:
        return "Yang Terhormat"