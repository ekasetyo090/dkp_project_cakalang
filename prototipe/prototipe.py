import utils.wa_api as wa_api
import os
import time
import mysql.connector
# import pandas as pd

from mysql.connector import Error
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv('MYSQL_HOST')
USER = os.getenv('MYSQL_USER')
PASSWORD = os.getenv('MYSQL_PASSWORD')
DATABASE = os.getenv('MYSQL_DATABASE')
PORT = int(os.getenv('MYSQL_PORT'))
JADWAL_SWITCH_PARAM = {
                'prototipe':{'normal':timedelta(minutes=0.3),'eskalasi':timedelta(minutes=0.1)},
                'production':{'normal':timedelta(days=7),'eskalasi':timedelta(days=3)}
                 }
JADWAL_SWITCH_OPERATOR = JADWAL_SWITCH_PARAM.get('prototipe')


def make_cursor():
        try:
            connection = mysql.connector.connect(
                host=HOST or os.getenv("DB_HOST"),
                user=USER or os.getenv("DB_USER"),
                password=PASSWORD or os.getenv("DB_PASSWORD"),
                database=DATABASE or os.getenv("DB_NAME"),
                port=PORT or int(os.getenv("DB_PORT", 3306))
            )
            cursor = connection.cursor(dictionary=True)
            return cursor, connection
        except Error as e:
            raise ConnectionError(f"❌ Gagal membuat koneksi database: {e}")

def get_min_max_id_koresponden(connection, cursor):
    try:
        if connection.is_connected():
            query = "SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM data_koresponden;"
            cursor.execute(query)
            result = cursor.fetchone()
            if result and result['min_id'] is not None and result['max_id'] is not None:
                min_id = int(result['min_id'])
                max_id = int(result['max_id'])
                return min_id, max_id
            else:
                print("⚠️ Tabel kosong atau tidak ada ID")
                return None, None

    except Error as e:
        print("❌ Gagal koneksi:", e)
        return None, None

   

def format_wa_number(no_wa: str) -> str:
    """
    Jika nomor diawali dengan '0', ganti menjadi '62' (kode negara Australia).
    """
    no_wa = no_wa.strip()
    if no_wa.startswith("0"):
        return "62" + no_wa[1:]
    return no_wa

def get_koresponden_by_id(connection,cursor,id_koresponden):
    try:
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM data_koresponden WHERE id = %s"
            cursor.execute(query, (id_koresponden,))
            result = cursor.fetchone()
            return result
    except Error as e:
        print(f"❌ Gagal mengambil data id={id_koresponden}:", e)
        return None


def update_text_data(data_text, no_wa,cursor,conn):
    valid_data = False
    for date, items in data_text.items():
        for data_id, texts in items.items():
            cursor.execute(
                """SELECT COUNT(*) as jumlah FROM respon_koresponden 
                   WHERE no_wa = %s AND pukul_respon = %s AND data_id = %s AND tipe_respon = 'text'""",
                (no_wa, date, data_id)
            )
            if cursor.fetchone()['jumlah'] == 0:
                cursor.execute(
                    "INSERT INTO respon_koresponden (no_wa, pukul_respon, data_id, tipe_respon) VALUES (%s, %s, %s, 'text')",
                    (no_wa, date, data_id)
                )
                conn.commit()
            for text in texts:
                cursor.execute(
                    "SELECT COUNT(*) as jumlah FROM text_respon WHERE data_id = %s AND text_respon = %s",
                    (data_id, text)
                )
                if cursor.fetchone()['jumlah'] == 0:
                    cursor.execute(
                        "INSERT INTO text_respon (data_id, text_respon) VALUES (%s, %s)",
                        (data_id, text)
                    )
                    conn.commit()
                    valid_data = True
    return valid_data

def log_pengiriman_dan_update_jadwal(cursor, conn, no_wa, time_now, jadwal_selanjutnya,boolean:int,condition_data:str = 'existing'):
    if condition_data not in ['existing', 'new']:
        raise ValueError("❌ Parameter 'condition_data' harus 'existing' atau 'new'.")

    try:
        cursor.execute(
            "INSERT INTO log_pengiriman_permintaan (no_wa, waktu_pengiriman, respon) VALUES (%s, %s, %s)",
            (no_wa, time_now, boolean)
        )
        conn.commit()
   
        if condition_data == 'existing':
            cursor.execute(
                """
                UPDATE jadwal_pengiriman_pesan_selanjutnya
                SET jadwal_pengiriman_pesan_selanjutnya = %s
                WHERE no_wa = %s
                """,
                (jadwal_selanjutnya, no_wa)
            )
            conn.commit()
        elif condition_data == 'new':
            try:
                cursor.execute(
                    "INSERT INTO jadwal_pengiriman_pesan_selanjutnya (no_wa, jadwal_pengiriman_pesan_selanjutnya) VALUES (%s, %s)",
                    (no_wa, jadwal_selanjutnya)
                )
                conn.commit()
                print('penyimpanan log permintaan berhasil')
            except Exception as e:
                print(f"❌ Gagal insert Jadwal: {e}")
        print("✅ Jadwal pengiriman berhasil diperbarui")
    except Exception as e:
        print(f"❌ Gagal update Jadwal: {e}")

def get_jenis_data(cursor,kegiatan:str):
    try:
        query = "SELECT jenis_data FROM jenis_data as jenis_data WHERE jenis_kegiatan = %s"
        cursor.execute(query, (kegiatan,))
        results = cursor.fetchall()
        return results  # list of dict
    except Error as e:
        print("❌ Gagal mengambil data jenis_kegiatan:", e)
        return None
    
def whatsapp_initialize():
    WA_API = wa_api.WhatsAPI()
    base_url_wa = 'https://' +"web.whatsapp.com"
    if WA_API.check_edge_process():
        WA_API.terminate_edge_process()
    else:
        pass
    DRIVER = WA_API.get_driver()
    DRIVER.get(base_url_wa)
    while True:
        if WA_API.wait_for_dom_stable(DRIVER,timeout=int(os.getenv('SCAN_TIMEOUT'))):
            while True:
                if WA_API.check_login_QR(DRIVER) == 0 and WA_API.check_app_initialize_screen(DRIVER) == 0 and WA_API.check_chat_icon(DRIVER)>0:
                    time.sleep(6)
                    
                    # WA_API.tunggu_dan_klik_button(DRIVER,class_name="x889kno x1a8lsjc x13jy36j x64bnmy x1n2onr6 x1rg5ohu xk50ysn x1f6kntn xyesn5m x1rl75mt x19t5iym xz7t8uv x13xmedi x178xt8z x1lun4ml xso031l xpilrb4 x13fuv20 x18b5jzi x1q0q8m5 x1t7ytsu x1v8p93f x1o3jo1z x16stqrj xv5lvn5 x1hl8ikr xfagghw x9dyr19 x9lcvmn x1pse0pq xcjl5na xfn3atn x1k3x3db x9qntcr xuxw1ft xv52azi")
                    
                    break
                else:
                    time.sleep(1)
                    continue
            break

        else:
            continue
    
    return DRIVER, WA_API


def salam_waktu():
    jam = datetime.now().hour

    if 4 <= jam < 11:
        return "Selamat Pagi"
    elif 11 <= jam < 15:
        return "Selamat Siang"
    elif 15 <= jam < 18:
        return "Selamat Sore"
    else:
        return "Selamat Malam"

def tambah_waktu_pesan(time_now, jumlah_belum_respon, waktu_terakhir_kirim_permintaan, pesan: str, JADWAL_SWITCH_OPERATOR: dict):
    if jumlah_belum_respon < 1:
        jadwal_selanjutnya = time_now + JADWAL_SWITCH_OPERATOR.get('normal')
        pesan = f"{pesan} tanggal {time_now.strftime('%d/%m/%Y')}"
    else:
        jadwal_selanjutnya = time_now + JADWAL_SWITCH_OPERATOR.get('eskalasi')
        pesan = f"{pesan} periode tanggal {waktu_terakhir_kirim_permintaan.strftime('%d/%m/%Y')} - {time_now.strftime('%d/%m/%Y')}"

    return pesan, jadwal_selanjutnya

def panggilan_sopan(jenis_kelamin: str) -> str:
    if not jenis_kelamin:
        return "Bapak/Ibu"

    jenis_kelamin = jenis_kelamin.strip().lower()

    if jenis_kelamin in ['l', 'laki-laki', 'laki']:
        return "Bapak"
    elif jenis_kelamin in ['p', 'perempuan', 'wanita']:
        return "Ibu"
    else:
        return "Yang Terhormat"
    

    

def main(DRIVER,WA_API):
    
    cursor, conn  = make_cursor()
    min_id_var,max_id_var = get_min_max_id_koresponden(conn,cursor)
    jenis_data = {
        'pengolahan fufu': 'penjualan ikan, harga ikan, jumlah produksi, jenis ikan',
        'pengolahan rumput laut': 'panen rumput laut, data 1, data 2 data blablbabla',
        'petani': 'data luas tambak, panen udang, blablabla',
    }
    for idx in range(min_id_var,min_id_var+1,1):
        # get row value from table data_koresponden with idx
        data = get_koresponden_by_id(conn,cursor,idx)
        no_wa = data['no_wa']
        nama_upi = data['nama_upi']
        kecamatan = data['kecamatan']
        desa = data['desa']
        nama_pemilik = data['nama_pemilik_upi']
        jenis_kelamin = data['jenis_kelamin']
        jenis_kegiatan = data['jenis_kegiatan']
        jenis_data = get_jenis_data(cursor,jenis_kegiatan)[0].get('jenis_data')        
        formatted_wa = format_wa_number(no_wa)
        url = f"https://web.whatsapp.com/send?phone={formatted_wa}&source=&data=#"
        DRIVER.get(url)
        while True:
            if WA_API.wait_for_dom_stable(DRIVER,timeout=int(os.getenv('SCAN_TIMEOUT'))):
                print(f"📨 Membuka chat: {no_wa}")
                break
            else:
                continue
        print("Menjalankan proses... (Tekan Ctrl+C untuk berhenti)")
        time.sleep(6)
        
        cursor, conn  = make_cursor()
        cursor.execute(
            "SELECT MAX(jadwal_pengiriman_pesan_selanjutnya) AS jadwal FROM jadwal_pengiriman_pesan_selanjutnya WHERE no_wa = %s",
            (no_wa,)
        )
        result = cursor.fetchone()
        jadwal = result['jadwal'] if result and result['jadwal'] else None
        time_now = datetime.now()
        if jadwal is None:
            time.sleep(10)
            print('jadwal '+str(jadwal))
            # tetap sebagai objek datetime
            jadwal_selanjutnya = time_now + JADWAL_SWITCH_OPERATOR.get('normal') 
            pesan = f'''{salam_waktu()} {panggilan_sopan(jenis_kelamin)} {nama_pemilik} selaku pemilik {nama_upi}, ini adalah sistem pengambilan data otomatis melalui whatsapps.
            sistem ini tidak menerima data berupa foto, vidio dan pesan suara, sistem hanya menerima pesan tulisan.
            data yang kami harapkan dari {panggilan_sopan(jenis_kelamin)} {nama_pemilik} berupa data {jenis_data}
            kami berharap kerja sama dengan {panggilan_sopan(jenis_kelamin)} {nama_pemilik}, terima kasih'''
            WA_API.kirim_pesan_permintaan(DRIVER,pesan)
            # log_pengiriman_dan_update_jadwal(cursor, conn, no_wa, time_now, jadwal_selanjutnya,boolean=0)
            log_pengiriman_dan_update_jadwal(cursor, conn, no_wa, time_now, jadwal_selanjutnya,boolean=0,condition_data='new')

        elif jadwal is not None and time_now >= jadwal:
            
            cursor.execute(
                """
                SELECT MIN(waktu_pengiriman) FROM log_pengiriman_permintaan 
                WHERE no_wa = %s AND respon = %s ORDER BY waktu_pengiriman ASC 
                """,
                (no_wa, 0)
            )
            waktu_terakhir_kirim_permintaan = cursor.fetchone().get('MIN(waktu_pengiriman)')
            print(waktu_terakhir_kirim_permintaan)
            data_text = WA_API.check_new_respon(DRIVER,waktu_terakhir_kirim_permintaan)
            if data_text:
                print(data_text)
                valid_data = update_text_data(data_text,no_wa,cursor,conn)
                if valid_data:
                    cursor.execute(
                        """
                        SELECT MAX(waktu_pengiriman) FROM log_pengiriman_permintaan 
                        WHERE no_wa = %s AND respon = %s ORDER BY waktu_pengiriman ASC 
                        """,
                        (no_wa, 0)
                    )
                    waktu_terakhir_kirim_permintaan_max = cursor.fetchone().get('MAX(waktu_pengiriman)')
                    cursor.execute(
                        """
                        UPDATE log_pengiriman_permintaan
                        SET respon = %s
                        WHERE no_wa = %s AND respon = %s AND waktu_pengiriman <= %s
                        """,
                        (1, no_wa, 0, waktu_terakhir_kirim_permintaan_max)
                    )
                    conn.commit()
                    
                cursor.execute(
                    """
                    SELECT COUNT(*) AS jumlah_belum_respon FROM log_pengiriman_permintaan
                    WHERE no_wa = %s AND respon = %s
                    """,
                    (no_wa, 0)
                )
                time.sleep(10)
                result = cursor.fetchone()
                jumlah_belum_respon = result['jumlah_belum_respon'] if result else 0
                pesan_awal = f'{salam_waktu()} {panggilan_sopan(jenis_kelamin)} {nama_pemilik} harap segera mengirim data {jenis_data} '
                pesan_final, jadwal_selanjutnya = tambah_waktu_pesan(time_now,jumlah_belum_respon,waktu_terakhir_kirim_permintaan,pesan_awal,JADWAL_SWITCH_OPERATOR)
                WA_API.kirim_pesan_permintaan(DRIVER, pesan_final)
                log_pengiriman_dan_update_jadwal(cursor, conn, no_wa, time_now, jadwal_selanjutnya,boolean=0)
                
            else:
                time.sleep(10)
                cursor.execute(
                    """
                    SELECT COUNT(*) AS jumlah_belum_respon FROM log_pengiriman_permintaan
                    WHERE no_wa = %s AND respon = %s
                    """,
                    (no_wa, 0)
                )
                result = cursor.fetchone()
                jumlah_belum_respon = result['jumlah_belum_respon'] if result else 0
                pesan_awal = f'{salam_waktu()} {panggilan_sopan(jenis_kelamin)} {nama_pemilik} harap segera mengirim data {jenis_data} '
                pesan_final, jadwal_selanjutnya = tambah_waktu_pesan(time_now,jumlah_belum_respon,waktu_terakhir_kirim_permintaan,pesan_awal,JADWAL_SWITCH_OPERATOR)
                WA_API.kirim_pesan_permintaan(DRIVER, pesan_final)
                
                # WA_API.kirim_pesan_permintaan(DRIVER, pesan)
                log_pengiriman_dan_update_jadwal(cursor, conn, no_wa, time_now, jadwal_selanjutnya,boolean=0)
    
if __name__ == '__main__':
    DRIVER,WA_API = whatsapp_initialize()
    while True:
        main(DRIVER,WA_API)
        time.sleep(10)

    