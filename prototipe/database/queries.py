from mysql.connector import Error

def get_min_max_id_koresponden(cursor):
    """Mendapatkan ID minimum dan maksimum dari tabel data_koresponden."""
    try:
        query = "SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM data_koresponden;"
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result['min_id'] is not None and result['max_id'] is not None:
            return int(result['min_id']), int(result['max_id'])
        else:
            print("⚠️ Tabel kosong atau tidak ada ID")
            return None, None
    except Error as e:
        print("❌ Gagal koneksi:", e)
        return None, None

def get_koresponden_by_id(cursor, id_koresponden):
    """Mendapatkan data koresponden berdasarkan ID."""
    try:
        query = "SELECT * FROM data_koresponden WHERE id = %s"
        cursor.execute(query, (id_koresponden,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Gagal mengambil data id={id_koresponden}:", e)
        return None

def get_kegiatan_usaha_by_id(cursor, jenisKegiatan):
    """Mendapatkan jenis data berdasarkan jenis kegiatan."""
    try:
        query = "SELECT jenis_data FROM jenis_data WHERE jenis_kegiatan = %s"
        cursor.execute(query, (jenisKegiatan,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"❌ Gagal mengambil data untuk jenis_kegiatan={jenisKegiatan}:", e)
        return None

def get_df_jadwal(cursor, no_wa):
    """Mendapatkan jadwal aktif untuk nomor WA tertentu."""
    cursor.execute(
        "SELECT * FROM log_permintaan WHERE no_wa = %s AND is_condition = %s",
        (no_wa, 'active')
    )
    result = cursor.fetchall()
    return result

def get_df_jadwal_count_all(cursor, no_wa):
    """Menghitung total jadwal untuk nomor WA tertentu."""
    cursor.execute(
        "SELECT COUNT(*) as jumlah FROM log_permintaan WHERE no_wa = %s",
        (no_wa,)
    )
    result = cursor.fetchone()
    return result['jumlah'] if result else 0

def get_df_reminder(cursor, no_wa, tanggal_data):
    """Mendapatkan data reminder untuk nomor WA dan tanggal data tertentu."""
    cursor.execute(
        "SELECT * FROM log_reminder WHERE no_wa = %s AND tanggal_data = %s",
        (no_wa, tanggal_data)
    )
    result = cursor.fetchall()
    return result

def insert_log_permintaan(cursor, conn, no_wa, tanggal_pengiriman, tanggal_data):
    """Menyimpan log permintaan."""
    try:
        cursor.execute(
            """INSERT INTO log_permintaan (no_wa, tanggal_pengiriman, tanggal_data) 
               VALUES (%s, %s, %s)""",
            (no_wa, tanggal_pengiriman, tanggal_data)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"❌ Gagal insert log_permintaan: {e}")
        return None

def insert_log_reminder(cursor, conn, no_wa, tanggal, tanggal_data):
    """Menyimpan log reminder."""
    try:
        cursor.execute(
            "INSERT INTO log_reminder (no_wa, tanggal, tanggal_data) VALUES (%s, %s, %s)",
            (no_wa, tanggal, tanggal_data)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Gagal insert log_reminder: {e}")

def update_log_reminder(cursor, conn, no_wa, tanggal, tanggal_data):
    """Memperbarui log reminder."""
    try:
        cursor.execute(
            "UPDATE log_reminder SET tanggal = %s, tanggal_data = %s WHERE no_wa = %s",
            (tanggal, tanggal_data, no_wa)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ Gagal update log_reminder: {e}")

def update_log_permintaan_inactive(cursor, conn, no_wa, tanggal_data):
    """Menonaktifkan log permintaan."""
    try:
        if isinstance(tanggal_data, list):
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
            cursor.execute(
                """
                UPDATE log_permintaan 
                SET is_condition = %s 
                WHERE no_wa = %s AND tanggal_data = %s
                """,
                ('inactive', no_wa, tanggal_data)
            )
        conn.commit()
    except Exception as e:
        print(f"❌ Gagal update log_permintaan: {e}")

def update_text_data(data_text, no_wa, cursor, conn, tanggal_data, permintaan_id):
    """Menyimpan data teks yang diterima."""
    valid_data = False
    for date, items in data_text.items():
        for data_id, texts in items.items():
            cursor.execute(
                """SELECT COUNT(*) as jumlah FROM data_text 
                   WHERE no_wa = %s AND data_id = %s AND tanggal_data = %s""",
                (no_wa, data_id, tanggal_data)
            )
            if cursor.fetchone()['jumlah'] == 0:
                cursor.execute(
                    """INSERT INTO data_text (no_wa, pukul_respon, data_id, text, tanggal_data, permintaan_id) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (no_wa, date, data_id, texts[0], tanggal_data, int(permintaan_id))
                )
                conn.commit()
                valid_data = True
    return valid_data

def check_data_text_exists(cursor, no_wa, tanggal_data):
    """Memeriksa apakah data teks sudah ada."""
    cursor.execute(
        "SELECT COUNT(*) as jumlah FROM data_text WHERE no_wa = %s AND tanggal_data = %s",
        (no_wa, tanggal_data)
    )
    result = cursor.fetchone()
    return result['jumlah'] if result else 0