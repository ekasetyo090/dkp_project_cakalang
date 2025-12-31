import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from database.queries import (
    get_kegiatan_usaha_by_id,
    get_df_jadwal,
    get_df_jadwal_count_all,
    get_df_reminder,
    insert_log_permintaan,
    insert_log_reminder,
    update_log_reminder,
    update_log_permintaan_inactive,
    update_text_data,
    check_data_text_exists
)
from whatsapp.message_handler import (
    create_initial_message,
    create_reminder_message,
    create_next_month_message
)
from utils.time_utils import (
    get_previous_month_date,
    get_next_month_date,
    get_data_deadline
)

def handle_permintaan_data(data, driver, whatsapp_api, interval_1, interval_2):
    """Menangani permintaan data untuk satu koresponden."""
    no_wa = data.get('no_wa')
    nama_upi = data.get('nama_upi')
    nama_pemilik = data.get('nama_pemilik_upi')
    
    # Buat koneksi database baru untuk setiap koresponden
    from database.connection import create_connection, create_cursor
    conn = create_connection()
    cursor = create_cursor(conn)
    
    # Ambil jenis data
    jenis_data_result = get_kegiatan_usaha_by_id(cursor, data.get('jenis_kegiatan'))
    if not jenis_data_result:
        print(f"❌ Jenis kegiatan tidak ditemukan untuk {data.get('jenis_kegiatan')}")
        cursor.close()
        conn.close()
        return
    jenis_data = jenis_data_result.get('jenis_data')
    
    # Buka chat WhatsApp
    whatsapp_api.open_chat(driver, no_wa)
    print(f"📨 Memproses: {nama_pemilik} ({no_wa})")
    
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    jadwal_aktif = get_df_jadwal(cursor, no_wa)
    jadwal_count = get_df_jadwal_count_all(cursor, no_wa)
    
    # Kasus 1: Tidak ada jadwal sama sekali
    if not jadwal_aktif and jadwal_count < 1:
        tanggal_data = get_previous_month_date(today)
        
        # Kirim pesan permintaan
        pesan = create_initial_message(nama_pemilik, jenis_data, nama_upi, tanggal_data)
        whatsapp_api.send_message(driver, pesan)
        
        # Simpan log
        insert_log_permintaan(cursor, conn, no_wa, today, tanggal_data)
        insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_1), tanggal_data)
        print(f"✅ Permintaan pertama dikirim untuk bulan {tanggal_data.strftime('%B %Y')}")
    
    # Kasus 2: Ada jadwal aktif
    elif jadwal_aktif:
        # Untuk sederhana, kita proses yang paling terakhir dulu
        # Tapi dalam kasus multiple, mungkin perlu loop
        # Di sini kita asumsikan hanya satu yang aktif atau kita proses yang terbaru
        if len(jadwal_aktif) == 1:
            jadwal = jadwal_aktif[0]
            tanggal_data = jadwal['tanggal_data']
            permintaan_id = jadwal['permintaan_id']
            
            batas_pengambilan_data = get_data_deadline(tanggal_data)
            reminder_data = get_df_reminder(cursor, no_wa, tanggal_data)
            
            # Cek apakah sudah melewati batas pengambilan data
            if today >= batas_pengambilan_data:
                # Minta data bulan berikutnya
                data_selanjutnya = get_next_month_date(tanggal_data)
                pesan = create_next_month_message(nama_pemilik, jenis_data, nama_upi, data_selanjutnya)
                whatsapp_api.send_message(driver, pesan)
                
                insert_log_permintaan(cursor, conn, no_wa, today, data_selanjutnya)
                insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), data_selanjutnya)
                print(f"📅 Permintaan baru untuk bulan {data_selanjutnya.strftime('%B %Y')}")
                
                # Nonaktifkan jadwal yang lama
                update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
            else:
                # Cek apakah sudah waktunya kirim reminder
                perlu_reminder = False
                if not reminder_data:
                    perlu_reminder = True
                else:
                    # Ambil reminder terakhir
                    last_reminder = max(reminder_data, key=lambda x: x['tanggal'])
                    if today >= last_reminder['tanggal']:
                        perlu_reminder = True
                
                if perlu_reminder:
                    # Cek apakah sudah ada respon
                    data_text = whatsapp_api.check_new_response(
                        driver=driver,
                        waktu_terakhir_kirim_permintaan=jadwal['tanggal_pengiriman'],
                        max_timing=batas_pengambilan_data,
                        no_WA=no_wa
                    )
                    
                    # Cek di database apakah data sudah ada
                    count_data_text = check_data_text_exists(cursor, no_wa, tanggal_data)
                    
                    if not data_text or count_data_text > 0:
                        # Kirim reminder
                        update_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), tanggal_data)
                        pesan = create_reminder_message(nama_pemilik, jenis_data, nama_upi, tanggal_data)
                        whatsapp_api.send_message(driver, pesan)
                        print(f"🔔 Reminder dikirim untuk bulan {tanggal_data.strftime('%B %Y')}")
                    else:
                        # Simpan data yang diterima
                        update_text_data(data_text, no_wa, cursor, conn, tanggal_data, permintaan_id)
                        update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
                        print(f"✅ Data diterima untuk bulan {tanggal_data.strftime('%B %Y')}")
                else:
                    # Cek apakah ada respon baru meski belum waktunya reminder
                    data_text = whatsapp_api.check_new_response(
                        driver=driver,
                        waktu_terakhir_kirim_permintaan=jadwal['tanggal_pengiriman'],
                        max_timing=batas_pengambilan_data,
                        no_WA=no_wa
                    )
                    if data_text:
                        update_text_data(data_text, no_wa, cursor, conn, tanggal_data, permintaan_id)
                        update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
                        print(f"✅ Data diterima untuk bulan {tanggal_data.strftime('%B %Y')}")
        else:
            # Multiple jadwal aktif
            print(f"⚠️ Multiple jadwal aktif untuk {no_wa}. Proses satu per satu...")
            # Proses jadwal tertua terlebih dahulu
            for jadwal in sorted(jadwal_aktif, key=lambda x: x['tanggal_data']):
                tanggal_data = jadwal['tanggal_data']
                permintaan_id = jadwal['permintaan_id']
                
                pesan = create_initial_message(nama_pemilik, jenis_data, nama_upi, tanggal_data)
                whatsapp_api.send_message(driver, pesan)
                time.sleep(3)
                print(f"📨 Mengirim permintaan untuk bulan {tanggal_data.strftime('%B %Y')}")
                
                # Setelah mengirim, nonaktifkan jadwal ini? Atau tunggu respon?
                # Untuk sementara, kita nonaktifkan setelah mengirim ulang permintaan
                update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
    
    cursor.close()
    conn.close()