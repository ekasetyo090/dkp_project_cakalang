from utils.helpers import salam_waktu, format_wa_number
from database.queries import get_kegiatan_usaha_by_id

def create_initial_message(nama_pemilik, jenis_data, nama_upi, tanggal_data):
    """Membuat pesan permintaan data pertama."""
    salam = salam_waktu()
    pesan = f"""{salam} Bapak/Ibu {nama_pemilik}, 
Mohon bantuannya untuk mengirimkan data {jenis_data} bulan {tanggal_data.strftime('%B %Y')}
untuk kelompok/upi {nama_upi}, terima kasih. 
Sistem ini tidak menerima data berupa foto, video, dan pesan suara; sistem hanya menerima pesan tulisan."""
    return pesan

def create_reminder_message(nama_pemilik, jenis_data, nama_upi, tanggal_data):
    """Membuat pesan reminder."""
    salam = salam_waktu()
    pesan = f"""{salam} Bapak/Ibu {nama_pemilik}, 
Mengingatkan bapak/ibu untuk mengirimkan data {jenis_data} bulan {tanggal_data.strftime('%B %Y')}
untuk kelompok/upi {nama_upi}, terima kasih. 
Sistem ini tidak menerima data berupa foto, video, dan pesan suara, sistem hanya menerima pesan tulisan."""
    return pesan

def create_next_month_message(nama_pemilik, jenis_data, nama_upi, tanggal_data):
    """Membuat pesan untuk bulan berikutnya."""
    salam = salam_waktu()
    pesan = f"""{salam} Bapak/Ibu {nama_pemilik}, 
Mohon bantuannya untuk mengirimkan data {jenis_data} bulan {tanggal_data.strftime('%B %Y')}
untuk kelompok/upi {nama_upi}, terima kasih. 
Sistem ini tidak menerima data berupa foto, video, dan pesan suara; sistem hanya menerima pesan tulisan."""
    return pesan