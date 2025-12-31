import utils.wa_api as wa_api
import os
import time
import mysql.connector
import pandas as pd
import locale
from datetime import datetime
from dateutil.relativedelta import relativedelta

from mysql.connector import Error
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
locale.setlocale(locale.LC_TIME, 'id_ID.utf8')
load_dotenv()
HOST = os.getenv('MYSQL_HOST')
USER = os.getenv('MYSQL_USER')
PASSWORD = os.getenv('MYSQL_PASSWORD')
DATABASE = os.getenv('MYSQL_DATABASE')
PORT = int(os.getenv('MYSQL_PORT'))
JADWAL_SWITCH_PARAM = {
                'prototipe':relativedelta(minutes=15),
                'production':relativedelta(days=7)
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

def get_kegiatan_usaha_by_id(connection,cursor,jenisKegiatan:str):
    try:
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT jenis_data FROM jenis_data WHERE jenis_kegiatan = %s"
            cursor.execute(query, (jenisKegiatan,))
            result = cursor.fetchone()
            return result
    except Error as e:
        print(f"❌ Gagal mengambil data id={id_koresponden}:", e)
        return None


def update_text_data(data_text, no_wa,cursor,conn,tanggal_data,permintaan_id):
    valid_data = False
    for date, items in data_text.items():
        for data_id, texts in items.items():
            cursor.execute(
                """SELECT COUNT(*) as jumlah FROM data_text 
                   WHERE no_wa = %s AND data_id = %s AND tanggal_data = %s""",
                (no_wa, data_id,tanggal_data)
            )
            if cursor.fetchone()['jumlah'] == 0:
                cursor.execute(
                    "INSERT INTO data_text (no_wa, pukul_respon, data_id, text, tanggal_data,permintaan_id) VALUES (%s,%s,%s,%s,%s,%s)",
                    (no_wa, date, data_id, texts[0], tanggal_data,int(permintaan_id))
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
                    WA_API.klik_button_lanjut(DRIVER)
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
    
def buka_chat_wa(driver, no_wa):
    formatted_wa = format_wa_number(no_wa)
    url = f"https://web.whatsapp.com/send?phone={formatted_wa}&source=&data=#"
    driver.get(url)
    time.sleep(30)
    # while True:
    #     if WA_API.wait_for_dom_stable(driver, timeout=int(os.getenv('SCAN_TIMEOUT'))):
    #         print(f"📨 Membuka chat: {no_wa}")
    #         time.sleep(10)
    #         break

def insert_log_permintaan(cursor, conn, no_wa, tanggal_pengiriman, tanggal_data):
    try:
        cursor.execute(
            "INSERT INTO log_permintaan (no_wa, tanggal_pengiriman, tanggal_data) VALUES (%s, %s, %s)",
            (no_wa, tanggal_pengiriman, tanggal_data)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Gagal insert log_permintaan: {e}")

def insert_log_reminder(cursor, conn, no_wa, tanggal, tanggal_data):
    try:
        cursor.execute(
            "INSERT INTO log_reminder (no_wa, tanggal, tanggal_data) VALUES (%s, %s, %s)",
            (no_wa, tanggal, tanggal_data)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Gagal insert log_reminder: {e}")

def update_log_reminder(cursor, conn, no_wa, tanggal, tanggal_data):
    try:
        cursor.execute(
            "UPDATE log_reminder SET tanggal = %s, tanggal_data = %s WHERE no_wa = %s",
            (tanggal, tanggal_data, no_wa)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Gagal update log_reminder: {e}")


def update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data):
    try:

        # Tunggal datetime
        if isinstance(tanggal_data, datetime):
            cursor.execute(
                """
                UPDATE log_permintaan 
                SET is_condition = %s 
                WHERE no_wa = %s AND tanggal_data = %s
                """,
                ('inactive', no_wa, tanggal_data)
            )

        # List of datetime
        elif isinstance(tanggal_data, list): #and all(isinstance(t, datetime) for t in tanggal_data):
            #tanggal_data = tanggal_data.tolist()
            for t in tanggal_data:
                cursor.execute(
                    """
                    UPDATE log_permintaan 
                    SET is_condition = %s 
                    WHERE no_wa = %s AND tanggal_data = %s
                    """,
                    ('inactive', no_wa, t)
                )
        else:
            print("❗ Format tanggal_data tidak dikenali")

        conn.commit()

    except Exception as e:
        print(f"❌ Gagal update log_permintaan: {e}")

# def update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data):
#     try:
#         # Fungsi bantu untuk mengonversi satu tanggal ke datetime.datetime
#         def convert_to_datetime(obj):
#             if isinstance(obj, str):
#                 return datetime.strptime(obj, '%Y-%m-%d')
#             elif isinstance(obj, pd.Timestamp):
#                 return obj.to_pydatetime()
#             elif isinstance(obj, datetime):
#                 return obj
#             else:
#                 return None

#         # Jika input adalah list
#         if isinstance(tanggal_data, list):
#             # Konversi semua elemen ke datetime
#             tanggal_data = [convert_to_datetime(t) for t in tanggal_data if convert_to_datetime(t) is not None]
#             for t in tanggal_data:
#                 cursor.execute(
#                     """
#                     UPDATE log_permintaan 
#                     SET is_condition = %s 
#                     WHERE no_wa = %s AND tanggal_data = %s
#                     """,
#                     ('inactive', no_wa, t)
#                 )

#         # Jika input tunggal
#         else:
#             t = convert_to_datetime(tanggal_data)
#             if t:
#                 cursor.execute(
#                     """
#                     UPDATE log_permintaan 
#                     SET is_condition = %s 
#                     WHERE no_wa = %s AND tanggal_data = %s
#                     """,
#                     ('inactive', no_wa, t)
#                 )
#             else:
#                 print("❗ Format tanggal_data tidak dikenali")

#         conn.commit()

#     except Exception as e:
#         print(f"❌ Gagal update log_permintaan: {e}")

def get_df_jadwal(cursor, no_wa):
    cursor.execute(
        "SELECT * FROM log_permintaan WHERE no_wa = %s AND is_condition = %s",
        (no_wa, 'active')
    )
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(result, columns=columns)

def get_df_jadwal_count_all(cursor, no_wa):
    # def get_df_jadwal_count_all(cursor, no_wa):
    cursor.execute(
        "SELECT COUNT(*) FROM log_permintaan WHERE no_wa = %s",
        (no_wa,)
    )
    result = cursor.fetchone()
    if result:
        return  result['COUNT(*)']
    else:
        return 0  # hasilnya berupa tuple (jumlah,)

def get_df_reminder(cursor, no_wa, tanggal_data):
    cursor.execute(
        "SELECT * FROM log_reminder WHERE no_wa = %s AND tanggal_data = %s",
        (no_wa, tanggal_data)
    )
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(result, columns=columns)

def handle_permintaan_data(data, driver,interval_1:int,interval_2:int):
       
    no_wa = data.get('no_wa')
    nama_upi = data.get('nama_upi')
    kecamatan = data.get('kecamatan')
    desa = data.get('desa')
    nama_pemilik = data.get('nama_pemilik_upi')

    cursor, conn  = make_cursor()
    jenis_data = get_kegiatan_usaha_by_id(conn, cursor, data.get('jenis_kegiatan')).get('jenis_data')

    buka_chat_wa(driver, no_wa)
    print("Menjalankan proses...")

    today = datetime.today()
    df_jadwal = get_df_jadwal(cursor, no_wa)
    jadwal_count = get_df_jadwal_count_all(cursor, no_wa)

    if df_jadwal.empty and jadwal_count<1:
        tanggal_data = ((today.replace(day=1) - relativedelta(months=1))).replace(hour=0, minute=0, second=0,microsecond=0)
        time.sleep(5)
        pesan = [f"{salam_waktu()} Bapak/Ibu {nama_pemilik}, Mohon bantuannya untuk mengirimkan data {jenis_data} bulan {tanggal_data.strftime('%B %Y')}",
                 f"untuk kelompok/upi {nama_upi}, terima kasih. Sistem ini tidak menerima data berupa foto, video, dan pesan suara; sistem hanya menerima pesan tulisan."]
        WA_API.kirim_pesan_permintaan(driver, ' '.join(pesan))
        print(tanggal_data)
        insert_log_permintaan(cursor, conn, no_wa, today, tanggal_data)
        insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_1), tanggal_data)
        
    if df_jadwal.shape[0]==1 and jadwal_count>=1:
        tanggal_data = df_jadwal['tanggal_data'].max().replace(hour=0, minute=0, second=0,microsecond=0)
        batas_pengambilan_data = (tanggal_data + relativedelta(months=2)).replace(hour=0, minute=0, second=0,microsecond=0)
        data_selanjutnya = (tanggal_data + relativedelta(months=1)).replace(hour=0, minute=0, second=0,microsecond=0)
        df_reminder = get_df_reminder(cursor, no_wa, tanggal_data)

        if today < batas_pengambilan_data and today >= df_reminder['tanggal'].max():
            # Check data response
            data_text = WA_API.check_new_respon(driver=driver,
                                                waktu_terakhir_kirim_permintaan=df_jadwal['tanggal_pengiriman'].max(),
                                                max_timing=batas_pengambilan_data,no_WA=no_wa)
            # if not data_text:
            #     return
            cursor.execute("SELECT COUNT(*) FROM data_text WHERE no_wa = %s AND tanggal_data = %s", (no_wa, tanggal_data))
            # count_data_text = cursor.fetchone()[0]
            result = cursor.fetchone()
            count_data_text = result['COUNT(*)'] if result else 0

            if not data_text or len(data_text) < 1 or count_data_text > 0:
                update_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), tanggal_data)
                pesan = [
                    f'{salam_waktu()} Bapak/Ibu {nama_pemilik}, Mengingatkan bapak/ibu untuk mengirimkan data {jenis_data} bulan {tanggal_data.strftime('%B %Y')}',
                    f'untuk kelompok/upi {nama_upi}, terima kasih. Sistem ini tidak menerima data berupa foto, video, dan pesan suara, sistem hanya menerima pesan tulisan.'
                ]
                WA_API.kirim_pesan_permintaan(driver, ' '.join(pesan))
            else:
                update_text_data(data_text, no_wa, cursor, conn, tanggal_data.replace(hour=0, minute=0, second=0), df_jadwal['permintaan_id'].iat[0])
                update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)

        elif today >= batas_pengambilan_data:
            pesan = [f"{salam_waktu()} Bapak/Ibu {nama_pemilik}, Mohon bantuannya untuk mengirimkan data {jenis_data}",
                    f"bulan {data_selanjutnya.strftime('%B %Y')} untuk kelompok/upi {nama_upi}, terima kasih. Sistem ini tidak menerima",
                    "data berupa foto, video, dan pesan suara; sistem hanya menerima pesan tulisan."]
            WA_API.kirim_pesan_permintaan(driver, ' '.join(pesan))
            insert_log_permintaan(cursor, conn, no_wa, today, data_selanjutnya)
            insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), data_selanjutnya)

        else:
            # data sudah masuk tapi belum ditandai inactive
            data_text = WA_API.check_new_respon(driver=driver,
                                                waktu_terakhir_kirim_permintaan=df_jadwal['tanggal_pengiriman'].max(),
                                                max_timing=batas_pengambilan_data,no_WA=no_wa)
            
            if data_text:
                update_text_data(data_text, no_wa, cursor, conn, tanggal_data, df_jadwal['permintaan_id'].max())
                update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data)
            else:
                return

    if df_jadwal.shape[0]>1 and jadwal_count>=1:
        tanggal_data = df_jadwal['tanggal_data'].max().replace(hour=0, minute=0, second=0,microsecond=0)
        batas_pengambilan_data = (tanggal_data + relativedelta(months=2)).replace(hour=0, minute=0, second=0,microsecond=0)
        data_selanjutnya = (tanggal_data + relativedelta(months=1)).replace(hour=0, minute=0, second=0,microsecond=0)
        df_reminder = get_df_reminder(cursor, no_wa, tanggal_data)
        # bulan_tahun_list = [tanggal.strftime('%B %Y') for tanggal in df_jadwal['tanggal_data'].unique()]

        bulan_tahun_list = df_jadwal['tanggal_data'].unique().tolist()

        bulan_tahun_str = ', '.join([tanggal.strftime('%B %Y') for tanggal in bulan_tahun_list])

        if today <= batas_pengambilan_data and today >= df_reminder['tanggal'].max():
            # Check data response
            data_text = WA_API.check_new_respon(driver=driver,
                                                waktu_terakhir_kirim_permintaan=df_jadwal['tanggal_pengiriman'].max(),
                                                max_timing=batas_pengambilan_data,no_WA=no_wa)

            cursor.execute("SELECT COUNT(*) FROM data_text WHERE no_wa = %s AND tanggal_data = %s", (no_wa, tanggal_data))
            # count_data_text = cursor.fetchone()[0]
            result = cursor.fetchone()
            count_data_text = result['COUNT(*)'] if result else 0

            if not data_text or len(data_text) < 1 or count_data_text > 0:
                update_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), tanggal_data)
                #bulan_tahun_str = ', '.join(tanggal.strftime('%B %Y') for tanggal in df_jadwal['tanggal_data'].unique())

                pesan = [
                    f'{salam_waktu()} Bapak/Ibu {nama_pemilik}, Mengingatkan bapak/ibu untuk mengirimkan data {jenis_data} bulan {bulan_tahun_str}',
                    f'untuk kelompok/upi {nama_upi}, terima kasih. Sistem ini tidak menerima data berupa foto, video, dan pesan suara, sistem hanya menerima pesan tulisan.'
                ]
                WA_API.kirim_pesan_permintaan(driver, ' '.join(pesan))
            else:
                update_text_data(data_text, no_wa, cursor, conn, tanggal_data, bulan_tahun_list)
                update_log_permintaan_inactive(cursor, conn, no_wa, bulan_tahun_list)

        elif today >= batas_pengambilan_data:
            #bulan_tahun_str = ', '.join(tanggal.strftime('%B %Y') for tanggal in df_jadwal['tanggal_data'].unique())
            pesan = [f"{salam_waktu()} Bapak/Ibu {nama_pemilik}, Mohon bantuannya untuk mengirimkan data {jenis_data}",
                    f"bulan {bulan_tahun_str} untuk kelompok/upi {nama_upi}, terima kasih. Sistem ini tidak menerima",
                    "data berupa foto, video, dan pesan suara; sistem hanya menerima pesan tulisan."]
            WA_API.kirim_pesan_permintaan(driver, ' '.join(pesan))
            insert_log_permintaan(cursor, conn, no_wa, today, data_selanjutnya)
            insert_log_reminder(cursor, conn, no_wa, today + timedelta(minutes=interval_2), data_selanjutnya)

        else:
            # data sudah masuk tapi belum ditandai inactive
            data_text = WA_API.check_new_respon(driver=driver,
                                                waktu_terakhir_kirim_permintaan=df_jadwal['tanggal_pengiriman'].max(),
                                                max_timing=batas_pengambilan_data,no_WA=no_wa)
            if data_text:
                update_text_data(data_text, no_wa, cursor, conn, tanggal_data, df_jadwal['permintaan_id'].max())
                update_log_permintaan_inactive(cursor, conn, no_wa, bulan_tahun_list)
            else:
                return

if __name__ == '__main__':
    DRIVER,WA_API = whatsapp_initialize()
    cursor, conn  = make_cursor()
    min_id_var,max_id_var = get_min_max_id_koresponden(conn,cursor)
    while True:
        # for idx in range(min_id_var,max_id_var+1,1):
        #     #get row value from table data_koresponden with idx
        #     data = get_koresponden_by_id(conn,cursor,idx)
        #     # handle_permintaan_data(data, DRIVER)
        #     handle_permintaan_data(data, DRIVER,interval_1=3,interval_2=5)
        #     # print(data)
        #     cursor.nextset()
        #     time.sleep(10)

        data = get_koresponden_by_id(conn,cursor,7)
        handle_permintaan_data(data, DRIVER,interval_1=3,interval_2=5)
        # handle_permintaan_data(data, driver,interval_1:int,interval_2:int)
        # print(data)
        cursor.nextset()
        time.sleep(10)