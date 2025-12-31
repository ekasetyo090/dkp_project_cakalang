import utils.wa_api as wa_api
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WhatsAppAPI:
    def __init__(self):
        self.wa_api = wa_api.WhatsAPI()
        self.base_url = 'https://web.whatsapp.com'
        
    def initialize_driver(self):
        """Menginisialisasi driver WhatsApp."""
        if self.wa_api.check_edge_process():
            self.wa_api.terminate_edge_process()
        
        driver = self.wa_api.get_driver()
        driver.get(self.base_url)
        
        # Tunggu hingga login berhasil
        while True:
            if self.wa_api.wait_for_dom_stable(driver, timeout=int(os.getenv('SCAN_TIMEOUT'))):
                while True:
                    if (self.wa_api.check_login_QR(driver) == 0 and 
                        self.wa_api.check_app_initialize_screen(driver) == 0 and 
                        self.wa_api.check_chat_icon(driver) > 0):
                        time.sleep(6)
                        self.wa_api.klik_button_lanjut(driver)
                        break
                    else:
                        time.sleep(1)
                        continue
                break
            else:
                continue
        return driver
    
    def open_chat(self, driver, no_wa):
        """Membuka chat dengan nomor WhatsApp tertentu."""
        from utils.helpers import format_wa_number
        formatted_wa = format_wa_number(no_wa)
        url = f"https://web.whatsapp.com/send?phone={formatted_wa}&source=&data=#"
        driver.get(url)
        time.sleep(10)  # Tunggu chat terbuka
    
    def send_message(self, driver, message):
        """Mengirim pesan ke chat yang terbuka."""
        self.wa_api.kirim_pesan_permintaan(driver, message)
    
    def check_new_response(self, driver, waktu_terakhir_kirim_permintaan, max_timing, no_WA):
        """Memeriksa respon baru."""
        return self.wa_api.check_new_respon(driver, waktu_terakhir_kirim_permintaan, max_timing, no_WA)