import time
from database.connection import create_connection, create_cursor
from database.queries import get_min_max_id_koresponden, get_koresponden_by_id
from whatsapp.api import WhatsAppAPI
from services.data_service import handle_permintaan_data

def main():
    # Inisialisasi WhatsApp API
    whatsapp_api = WhatsAppAPI()
    driver = whatsapp_api.initialize_driver()
    
    # Koneksi database
    conn = create_connection()
    cursor = create_cursor(conn)
    
    # Ambil range ID koresponden
    min_id, max_id = get_min_max_id_koresponden(cursor)
    
    if min_id and max_id:
        print(f"🔢 Memulai dari ID {min_id} hingga {max_id}")
        
        for idx in range(min_id, max_id + 1):
            data = get_koresponden_by_id(cursor, idx)
            if data:
                print(f"\n🔄 Memproses ID {idx}: {data.get('nama_pemilik_upi')}")
                try:
                    handle_permintaan_data(data, driver, whatsapp_api, interval_1=3, interval_2=5)
                except Exception as e:
                    print(f"❌ Gagal memproses ID {idx}: {e}")
                time.sleep(10)  # Delay antara pengiriman
            else:
                print(f"⚠️ Data ID {idx} tidak ditemukan")
            
            time.sleep(2)
    
    cursor.close()
    conn.close()
    driver.quit()
    print("✅ Selesai memproses semua koresponden.")

if __name__ == '__main__':
    main()