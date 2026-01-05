"""
AUTOMATED WHATSAPP DATA COLLECTION HANDLER
===========================================

Module: data_request_handler.py
Description: Menangani logika pengiriman permintaan data dan reminder melalui WhatsApp
Created: [Tanggal pembuatan]
Last Modified: [Tanggal modifikasi terakhir]
Version: 1.0.0
"""

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Import modul database untuk operasi query dan manipulasi data
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

# Import modul handler pesan WhatsApp untuk berbagai tipe pesan
from whatsapp.message_handler import (
    create_initial_message,
    create_reminder_message,
    create_next_month_message
)

# Import utilitas waktu untuk perhitungan tanggal
from utils.time_utils import (
    get_previous_month_date,
    get_next_month_date,
    get_data_deadline
)


def handle_permintaan_data(data, driver, whatsapp_api, interval_1, interval_2):
    """
    MENANGANI PERMINTAAN DATA UNTUK SATU KORESPONDEN
    ================================================
    
    Fungsi utama untuk mengelola seluruh siklus pengiriman permintaan data,
    reminder, dan penerimaan respons melalui WhatsApp.
    
    PARAMETER:
    ----------
    data : dict
        Dictionary berisi informasi koresponden dengan keys:
        - no_wa (str): Nomor WhatsApp tujuan
        - nama_upi (str): Nama Unit Pengumpul Informasi
        - nama_pemilik_upi (str): Nama pemilik UPI
        - jenis_kegiatan (int/str): ID jenis kegiatan usaha
    
    driver : selenium.webdriver
        Instance WebDriver Selenium untuk kontrol browser
    
    whatsapp_api : WhatsAppAPI
        Instance wrapper untuk operasi WhatsApp
    
    interval_1 : int
        Interval menit untuk reminder pertama setelah permintaan awal
    
    interval_2 : int
        Interval menit untuk reminder berikutnya
    
    ALUR LOGIKA:
    ------------
    1. Membuka koneksi database baru
    2. Membuka chat WhatsApp koresponden
    3. Mengevaluasi status jadwal pengiriman:
       - Kasus 1: Tidak ada jadwal sama sekali → Kirim permintaan pertama
       - Kasus 2: Ada jadwal aktif → Proses berdasarkan deadline dan reminder
    4. Menutup koneksi database
    
    CATATAN:
    -------
    - Setiap koresponden menggunakan koneksi database terpisah
    - Mengasumsikan satu jenis data per koresponden per eksekusi
    - Multiple jadwal aktif ditangani dengan pengiriman berurutan
    """
    
    # Ekstrak data koresponden dari parameter input
    no_wa = data.get('no_wa')
    nama_upi = data.get('nama_upi')
    nama_pemilik = data.get('nama_pemilik_upi')
    
    # BUAT KONEKSI DATABASE BARU UNTUK SETIAP KORESPONDEN
    # ===================================================
    # Koneksi dibuat per koresponden untuk isolasi transaksi
    from database.connection import create_connection, create_cursor
    conn = create_connection()
    cursor = create_cursor(conn)
    
    # AMBIL JENIS DATA BERDASARKAN ID KEGIATAN
    # =========================================
    # Jenis data menentukan template pesan yang akan dikirim
    jenis_data_result = get_kegiatan_usaha_by_id(cursor, data.get('jenis_kegiatan'))
    if not jenis_data_result:
        print(f"❌ Jenis kegiatan tidak ditemukan untuk {data.get('jenis_kegiatan')}")
        cursor.close()
        conn.close()
        return
    jenis_data = jenis_data_result.get('jenis_data')
    
    # BUKA CHAT WHATSAPP KORESPONDEN
    # ===============================
    whatsapp_api.open_chat(driver, no_wa)
    print(f"📨 Memproses: {nama_pemilik} ({no_wa})")
    
    # INISIALISASI VARIABEL WAKTU
    # ============================
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # AMBIL DATA JADWAL DARI DATABASE
    # ================================
    # jadwal_aktif: Jadwal yang masih aktif (belum diproses)
    # jadwal_count: Total semua jadwal (termasuk yang sudah selesai)
    jadwal_aktif = get_df_jadwal(cursor, no_wa)
    jadwal_count = get_df_jadwal_count_all(cursor, no_wa)
    
    # KASUS 1: TIDAK ADA JADWAL SAMA SEKALI
    # ======================================
    # Kondisi: Koresponden baru pertama kali dimintai data
    if not jadwal_aktif and jadwal_count < 1:
        # Tentukan tanggal data (bulan sebelumnya)
        tanggal_data = get_previous_month_date(today)
        
        # Buat dan kirim pesan permintaan awal
        pesan = create_initial_message(nama_pemilik, jenis_data, nama_upi, tanggal_data)
        whatsapp_api.send_message(driver, pesan)
        
        # SIMPAN LOG PERMINTAAN DAN REMINDER
        # ==================================
        insert_log_permintaan(cursor, conn, no_wa, today, tanggal_data)
        insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_1), tanggal_data)
        print(f"✅ Permintaan pertama dikirim untuk bulan {tanggal_data.strftime('%B %Y')}")
    
    # KASUS 2: ADA JADWAL AKTIF
    # ==========================
    # Kondisi: Koresponden memiliki jadwal permintaan yang belum selesai
    elif jadwal_aktif:
        # SUB-KASUS 2A: HANYA SATU JADWAL AKTIF
        # ======================================
        # Penanganan optimal untuk kasus tunggal
        if len(jadwal_aktif) == 1:
            jadwal = jadwal_aktif[0]
            tanggal_data = jadwal['tanggal_data']
            permintaan_id = jadwal['permintaan_id']
            
            # Hitung batas akhir pengambilan data
            batas_pengambilan_data = get_data_deadline(tanggal_data)
            
            # Ambil data reminder yang sudah dikirim
            reminder_data = get_df_reminder(cursor, no_wa, tanggal_data)
            
            # CEK APAKAH SUDAH MELEWATI BATAS PENGAMBILAN DATA
            # ================================================
            # Jika sudah lewat deadline, minta data bulan berikutnya
            if today >= batas_pengambilan_data:
                # Generate tanggal untuk bulan berikutnya
                data_selanjutnya = get_next_month_date(tanggal_data)
                pesan = create_next_month_message(nama_pemilik, jenis_data, nama_upi, data_selanjutnya)
                whatsapp_api.send_message(driver, pesan)
                
                # Buat log baru untuk permintaan bulan berikutnya
                insert_log_permintaan(cursor, conn, no_wa, today, data_selanjutnya)
                insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), data_selanjutnya)
                print(f"📅 Permintaan baru untuk bulan {data_selanjutnya.strftime('%B %Y')}")
                
                # Nonaktifkan jadwal lama yang sudah expired
                update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
            
            # SUB-KASUS 2B: BELUM MELEWATI BATAS DEADLINE
            # ============================================
            # Lakukan pengecekan status dan kirim reminder jika perlu
            else:
                # TENTUKAN APAKAH PERLU KIRIM REMINDER
                # ====================================
                perlu_reminder = False
                if not reminder_data:
                    # Belum ada reminder sama sekali
                    perlu_reminder = True
                else:
                    # Ambil reminder terakhir untuk mengecek interval
                    last_reminder = max(reminder_data, key=lambda x: x['tanggal'])
                    if today >= last_reminder['tanggal']:
                        perlu_reminder = True
                
                # PROSES REMINDER ATAU PENERIMAAN DATA
                # ====================================
                if perlu_reminder:
                    # Cek apakah ada respons baru di WhatsApp
                    data_text = whatsapp_api.check_new_response(
                        driver=driver,
                        waktu_terakhir_kirim_permintaan=jadwal['tanggal_pengiriman'],
                        max_timing=batas_pengambilan_data,
                        no_WA=no_wa
                    )
                    
                    # Cek di database apakah data sudah pernah diterima
                    count_data_text = check_data_text_exists(cursor, no_wa, tanggal_data)
                    
                    # KIRIM REMINDER JIKA BELUM ADA RESPONS
                    # =====================================
                    if not data_text or count_data_text > 0:
                        # Update jadwal reminder berikutnya
                        update_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), tanggal_data)
                        
                        # Kirim pesan reminder
                        pesan = create_reminder_message(nama_pemilik, jenis_data, nama_upi, tanggal_data)
                        whatsapp_api.send_message(driver, pesan)
                        print(f"🔔 Reminder dikirim untuk bulan {tanggal_data.strftime('%B %Y')}")
                    
                    # SIMPAN DATA JIKA ADA RESPONS BARU
                    # ==================================
                    else:
                        update_text_data(data_text, no_wa, cursor, conn, tanggal_data, permintaan_id)
                        update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
                        print(f"✅ Data diterima untuk bulan {tanggal_data.strftime('%B %Y')}")
                
                # CEK RESPONS SPONTAN (TANPA MENUNGGU REMINDER)
                # =============================================
                else:
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
        
        # SUB-KASUS 2C: MULTIPLE JADWAL AKTIF
        # ====================================
        # Penanganan untuk beberapa jadwal aktif secara bersamaan
        else:
            print(f"⚠️ Multiple jadwal aktif untuk {no_wa}. Proses satu per satu...")
            
            # Proses jadwal dari yang paling lama (tertua)
            for jadwal in sorted(jadwal_aktif, key=lambda x: x['tanggal_data']):
                tanggal_data = jadwal['tanggal_data']
                permintaan_id = jadwal['permintaan_id']
                
                # Kirim ulang permintaan untuk setiap jadwal
                pesan = create_initial_message(nama_pemilik, jenis_data, nama_upi, tanggal_data)
                whatsapp_api.send_message(driver, pesan)
                time.sleep(3)  # Delay antar pesan untuk menghindari spam
                print(f"📨 Mengirim permintaan untuk bulan {tanggal_data.strftime('%B %Y')}")
                
                # Nonaktifkan jadwal setelah dikirim ulang
                update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
    
    # TUTUP KONEKSI DATABASE
    # ======================
    cursor.close()
    conn.close()


"""
CATATAN PENTING:
---------------
1. FLOW CONTROL:
   - Fungsi ini menggunakan early return pattern untuk error handling
   - Setiap path eksekusi harus menutup koneksi database sebelum return

2. WAKTU DAN TANGGAL:
   - Semua perhitungan tanggal menggunakan waktu server/lokal
   - Batas waktu dihitung berdasarkan tanggal_data, bukan tanggal_pengiriman

3. PENGIRIMAN PESAN:
   - Setiap jenis pesan (initial, reminder, next_month) menggunakan template terpisah
   - Interval reminder bersifat konfigurable melalui parameter

4. PENGECEKAN RESPONS:
   - Dilakukan baik pada saat reminder maupun di luar jadwal reminder
   - Data yang sudah diterima tidak akan diminta ulang

5. ERROR HANDLING:
   - Error pada level database ditangani dengan print statement
   - Error WhatsApp (no WA invalid, dll) ditangani oleh modul whatsapp_api
"""

"""
REVISI YANG DISARANKAN (FUTURE ENHANCEMENT):
-------------------------------------------
1. Tambahkan retry mechanism untuk failed message sending
2. Implementasi logging system yang lebih robust (file-based)
3. Tambahkan konfigurasi untuk custom interval per koresponden
4. Optimasi query database dengan batch processing
5. Tambahkan timeout mechanism untuk respons checking
"""