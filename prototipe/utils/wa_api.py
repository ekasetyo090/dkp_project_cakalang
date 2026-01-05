"""
WHATSAPP WEB AUTOMATION API WRAPPER
===================================

Module: whatsapp_api.py
Description: Kelas wrapper untuk otomatisasi interaksi dengan WhatsApp Web menggunakan Selenium
Created: [Tanggal pembuatan]
Last Modified: [Tanggal modifikasi terakhir]
Version: 1.0.0

DEPENDENCIES:
-------------
- selenium==4.0.0+
- beautifulsoup4==4.12.0+
- psutil==5.9.0+
"""

import os
import time
import psutil
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


class WhatsAPI:
    """
    KELAS WHATSAPP API WRAPPER
    ===========================
    
    Kelas utama yang menangani semua interaksi dengan WhatsApp Web melalui Selenium.
    Menyediakan metode untuk inisialisasi, pengiriman pesan, penerimaan data, dan manajemen sesi.
    
    ATTRIBUTES:
    -----------
    driver_path : str
        Path ke Microsoft Edge WebDriver executable
    binary_path : str
        Path ke Microsoft Edge browser binary
    user_data_dir : str
        Directory user data Edge untuk menyimpan session dan cookies
    profile_directory : str
        Nama profil Edge yang akan digunakan
        
    CATATAN:
    --------
    - Menggunakan Microsoft Edge sebagai browser (dapat diadaptasi ke Chrome/Firefox)
    - Menggunakan user data directory untuk menghindari login berulang
    - Implementasi WebDriver Wait untuk menghandle async loading
    """
    
    def __init__(self):
        """
        INISIALISASI KONFIGURASI WHATSAPP API
        =====================================
        
        Menentukan path-path penting untuk driver Edge dan konfigurasi profil.
        Semua path menggunakan relative path untuk portabilitas.
        """
        # Dapatkan current directory untuk path relatif
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path ke Edge WebDriver (executable)
        self.driver_path = os.path.join(current_dir, "..", "edge web driver", "msedgedriver.exe")
        
        # Path ke Microsoft Edge binary
        self.binary_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        
        # Path ke user data directory (untuk session persistence)
        self.user_data_dir = r'C:\Users\eka agung\AppData\Local\Microsoft\Edge\User Data'
        
        # Nama profil yang digunakan (Default atau custom)
        self.profile_directory = 'Default'

    def check_edge_process(self):
        """
        CEK APAKAH PROSES EDGE SEDANG BERJALAN
        ======================================
        
        Memeriksa apakah ada instance Microsoft Edge yang sedang aktif.
        
        RETURNS:
        --------
        bool
            True jika ada proses msedge.exe berjalan, False jika tidak
            
        CATATAN:
        --------
        Menggunakan psutil untuk proses scanning, lebih reliable daripada tasklist
        """
        return any(proc.info['name'] == 'msedge.exe' for proc in psutil.process_iter(['name']))

    def terminate_edge_process(self):
        """
        TERMINASI SEMUA PROSES EDGE
        ============================
        
        Menghentikan semua instance Microsoft Edge yang sedang berjalan.
        
        ALUR:
        -----
        1. Iterasi semua proses sistem
        2. Identifikasi proses msedge.exe
        3. Terminasi proses dengan graceful termination
        
        CATATAN:
        --------
        - Menggunakan terminate() bukan kill() untuk graceful shutdown
        - Timeout 5 detik untuk setiap proses
        - Error handling untuk proses yang tidak bisa dihentikan
        """
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'msedge.exe':
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"Terminated Edge process with PID {proc.pid}")
                except Exception as e:
                    print(f"Failed to terminate process {proc.pid}: {e}")

    def get_driver(self):
        """
        BUAT SELENIUM WEBDRIVER INSTANCE
        =================================
        
        Konfigurasi dan inisialisasi WebDriver Edge dengan opsi-opsi khusus.
        
        RETURNS:
        --------
        webdriver.Edge
            Instance WebDriver yang sudah dikonfigurasi
            
        OPSI KONFIGURASI:
        -----------------
        1. User data directory: Untuk session persistence
        2. Profile directory: Menggunakan profil default
        3. Disable infobars: Menghilangkan "Chrome is being controlled..."
        4. No sandbox & disable dev shm: Untuk environment Docker/Linux
        5. Start maximized: Browser fullscreen
        6. Exclude automation switches: Menghindari detection sebagai bot
        """
        options = Options()
        options.binary_location = self.binary_path
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument(f"profile-directory={self.profile_directory}")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(executable_path=self.driver_path)
        return webdriver.Edge(service=service, options=options)

    def check_login_QR(self, driver):
        """
        CEK KETERSEDIAAN QR CODE LOGIN
        ===============================
        
        Memeriksa apakah QR code untuk login WhatsApp Web muncul.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
            
        RETURNS:
        --------
        int
            Jumlah elemen QR code yang ditemukan (0 = sudah login)
        """
        return len(driver.find_elements(By.XPATH, "//canvas[@aria-label='Scan this QR code to link a device!' and @role='img']"))

    def check_app_initialize_screen(self, driver):
        """
        CEK SCREEN INISIALISASI APLIKASI
        =================================
        
        Memeriksa apakah WhatsApp Web sedang dalam proses inisialisasi/loading.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
            
        RETURNS:
        --------
        int
            Jumlah elemen loading screen yang ditemukan
        """
        return len(driver.find_elements(By.XPATH, "//div[@id='wa_web_initial_startup' and @class='_apdl']"))

    def check_chat_icon(self, driver):
        """
        CEK ICON CHAT (INDIKATOR LOGIN SUKSES)
        ======================================
        
        Memeriksa apakah icon chat sidebar muncul, menandakan login berhasil.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
            
        RETURNS:
        --------
        int
            Jumlah elemen chat icon yang ditemukan (>0 = login sukses)
        """
        return len(driver.find_elements(By.XPATH, "//div[@class='x1c4vz4f xs83m0k xdl72j9 x1g77sc7 x78zum5 xozqiw3 x1oa3qoh x12fk4p8 xeuugli x2lwn1j x1nhvcw1 x1q0g3np x6s0dn4 xh8yej3']"))

    def get_profile_name_elements(self, driver):
        """
        AMBIL ELEMEN NAMA PROFIL
        ========================
        
        Mengambil semua elemen yang berisi nama kontak/profil.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
            
        RETURNS:
        --------
        list
            List WebElement yang mengandung nama profil
        """
        return driver.find_elements(By.XPATH, "//span[@dir='auto' and @class='x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1rg5ohu _ao3e']")

    def process_profile_name_element(self, element):
        """
        EKSTRAK TEKS DARI ELEMEN NAMA PROFIL
        ====================================
        
        Menggunakan BeautifulSoup untuk ekstraksi teks dari HTML element.
        
        PARAMETERS:
        -----------
        element : WebElement
            Element yang berisi nama profil
            
        RETURNS:
        --------
        str
            Nama profil yang sudah dibersihkan (tanpa tag HTML)
        """
        html = element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(strip=True)
        return text

    def wait_for_dom_stable(self, driver, timeout=30, check_interval=0.5):
        """
        TUNGGU HINGGA DOM STABIL
        =========================
        
        Menunggu hingga tidak ada perubahan pada DOM untuk memastikan halaman selesai loading.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        timeout : int, optional
            Maksimal waktu tunggu dalam detik (default: 30)
        check_interval : float, optional
            Interval pengecekan dalam detik (default: 0.5)
            
        RETURNS:
        --------
        bool
            True jika DOM stabil, False jika timeout
            
        MEKANISME:
        ----------
        1. Inject JavaScript MutationObserver ke halaman
        2. Monitor perubahan pada document.body
        3. Return ketika tidak ada perubahan dalam interval tertentu
        
        CATATAN:
        --------
        - Menggunakan JavaScript injection untuk monitoring real-time
        - Lebih reliable daripada implicit/explicit wait biasa
        """
        driver.execute_script("""
            window.domChanged = false;
            const observer = new MutationObserver(() => {
                window.domChanged = true;
            });
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true
            });
        """)
        end_time = time.time() + timeout
        while time.time() < end_time+1:
            changed = driver.execute_script("return window.domChanged;")
            if not changed:
                return True
            driver.execute_script("window.domChanged = false;")
            time.sleep(check_interval)
        return False
    
    def check_button(self, driver, xpath:str):
        """
        CEK KETERSEDIAAN TOMBOL BERDASARKAN XPATH
        ==========================================
        
        Generic method untuk mengecek keberadaan tombol.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        xpath : str
            XPath expression untuk mencari tombol
            
        RETURNS:
        --------
        list
            List WebElement yang sesuai dengan XPath
        """
        return driver.find_elements(By.XPATH, xpath)
    
    
    
    def klik_button_lanjut(self, driver, timeout=30):
        """
        KLIK TOMBOL 'LANJUT' PADA POPUP
        ================================
        
        Menangani popup dengan tombol 'Lanjut' (common pada WhatsApp Web).
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        timeout : int, optional
            Maksimal waktu tunggu popup (default: 30)
            
        CATATAN:
        --------
        - Menggunakan CSS selector untuk popup container
        - Mencari button dengan text "Lanjut" di dalam popup
        - Explicit wait untuk memastikan element clickable
        """
        try:
            # Tunggu div popup muncul
            popup_div = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-animate-modal-popup="true"]'))
            )

            # Cari tombol dengan teks "Lanjut" di dalam popup
            button_lanjut = popup_div.find_element(By.XPATH, './/button[.//div[text()="Lanjut"]]')
            
            # Klik tombolnya
            button_lanjut.click()
            print("✅ Tombol 'Lanjut' berhasil diklik.")

        except Exception as e:
            print("❌ Tidak menemukan tombol 'Lanjut' atau popup:", e)
        
    def tunggu_dan_klik_button(self, driver, class_name="x", timeout=30):
        """
        TUNGGU DAN KLIK TOMBOL BERDASARKAN CLASS NAME
        ==============================================
        
        Menunggu tombol tersedia dan melakukan click action.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        class_name : str, optional
            Class name tombol target (default: "x")
        timeout : int, optional
            Maksimal waktu tunggu (default: 30)
            
        RETURNS:
        --------
        bool
            True jika berhasil klik, False jika timeout/error
        """
        try:
            tombol = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CLASS_NAME, class_name))
            )
            tombol.click()
            print(f"✅ Tombol dengan class '{class_name}' berhasil diklik.")
            return True
        except TimeoutException:
                return False
        except Exception as e:
            print(f"❌ Gagal klik tombol dengan class '{class_name}': {e}")

    def scroll_div_check(self, driver, no_WA, tolerance=1, time_out_count=15):
        # """
        # CEK DAN SCROLL CHAT CONTAINER
        # ==============================
        
        # Mencari dan melakukan scroll pada chat container untuk memuat pesan.
        
        # PARAMETERS:
        # -----------
        # driver : webdriver.Edge
        #     Instance WebDriver yang sedang aktif
        # no_WA : str
        #     Nomor WhatsApp tujuan (untuk URL building)
        # time_out_count : int, optional
        #     Maksimal retry attempts (default: 15)
            
        # RETURNS:
        # --------
        # WebElement or False
        #     Element scrollable div jika ditemukan, False jika tidak
            
        # ALUR:
        # -----
        # 1. Navigasi ke URL chat
        # 2. Tunggu scrollable div muncul
        # 3. Lakukan scroll ke top untuk memuat semua pesan
        # 4. Retry dengan refresh jika timeout
        
        # CATATAN:
        # --------
        # - Menggunakan XPath spesifik untuk chat container WhatsApp
        # - Scroll ke top untuk memastikan semua pesan terload
        # """
        url=f"https://web.whatsapp.com/send?phone={no_WA}&source=&data=#"
        max_retry = 3
        timeout = 30
        time_out_count = 0
        
        # while time_out_count < max_retry:
        #     try:
        #         # Tunggu maksimal 'timeout' detik sampai elemen muncul
        #         scrollable_element = driver.find_element(By.XPATH, '//div[@data-scrolltracepolicy="wa.web.conversation.messages"]')
        #         scrollable_div = WebDriverWait(driver, timeout).until(
        #             EC.presence_of_element_located((By.XPATH, '//div[@tabindex="0" and @data-tab="8" and @role="application"]'))
        #         )
        #         # for _ in range(times):
        #         #     driver.execute_script("arguments[0].scrollTop = 0;", scrollable_div)
            
        #     except TimeoutException:
        #         time_out_count +=1
        #         print(f"Timeout: Elemen tidak muncul dalam {timeout} detik. Melakukan refresh halaman...")
        #         # driver.refresh()
        #         # time.sleep(60)
        #         # driver.get(url)
        #         time.sleep(10)
        #         continue
            
        #     except NoSuchElementException or time_out_count>=2:
        #         print("Elemen tidak ditemukan. Melakukan refresh halaman...")
        #         # driver.refresh()
        #         # time.sleep(30)
        #         return False
        #     else: 
        #         return scrollable_div
        # return False
        while time_out_count < max_retry:
            try:
                # Tunggu maksimal 'timeout' detik sampai elemen muncul
                scrollable_element = driver.find_element(By.XPATH, '//div[@data-scrolltracepolicy="wa.web.conversation.messages"]')
                
                scroll_driver = scrollable_element.parent  # Mendapatkan driver dari elemen
    
                result = scroll_driver.execute_script("""
                    const el = arguments[0];
                    return {
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight
                    };
                """, scrollable_element)  # element dilewatkan sebagai argumen ke JavaScript
                
                # Perhitungan dengan toleransi
                time.sleep(10)
                return (result['scrollHeight'] - result['clientHeight']) > tolerance
            
            except TimeoutException:
                time_out_count +=1
                print(f"Timeout: Elemen tidak muncul dalam {timeout} detik. Melakukan refresh halaman...")
                # driver.refresh()
                # time.sleep(60)
                # driver.get(url)
                time.sleep(10)
                continue
            
            except NoSuchElementException or time_out_count>=2:
                print("Elemen tidak ditemukan. Melakukan refresh halaman...")
                # driver.refresh()
                # time.sleep(30)
                return False

        return False
    
    def buka_chat_wa(self, driver, no_wa):
        """
        BUKA CHAT WHATSAPP BERDASARKAN NOMOR
        ====================================
        
        Navigasi ke chat spesifik berdasarkan nomor WhatsApp.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        no_wa : str
            Nomor WhatsApp tujuan
            
        ALUR:
        -----
        1. Format nomor WhatsApp
        2. Navigasi ke URL chat
        3. Tunggu DOM stabil
        4. Delay untuk memastikan chat terload sempurna
        
        CATATAN:
        --------
        - Menggunakan format_wa_number() helper function (harus didefinisikan di luar)
        - SCAN_TIMEOUT diambil dari environment variable
        """
        formatted_wa = format_wa_number(no_wa)  # Fungsi helper harus didefinisikan
        url = f"https://web.whatsapp.com/send?phone={formatted_wa}&source=&data=#"
        driver.get(url)
        while True:
            if WA_API.wait_for_dom_stable(driver, timeout=int(os.getenv('SCAN_TIMEOUT'))):
                print(f"📨 Membuka chat: {no_wa}")
                time.sleep(3)
                break

    def get_text_data(self, driver):
        """
        EKSTRAK DATA TEKS DARI CHAT
        ============================
        
        Mengambil semua pesan masuk (message-in) dari chat yang sedang aktif.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
            
        RETURNS:
        --------
        dict
            Dictionary struktur:
            {
                timestamp1: {
                    data_id1: [text_content1, text_content2],
                    data_id2: [text_content3]
                },
                timestamp2: {...}
            }
            
        FILTERING:
        ----------
        1. Hanya pesan masuk (message-in)
        2. Tidak termasuk pesan dengan URL
        3. Tidak termasuk pesan sangat pendek (<=15 karakter)
        4. Format timestamp: [HH.MM, DD/MM/YYYY]
        
        CATATAN:
        --------
        - Menggunakan regex untuk parsing timestamp
        - Skip pesan dengan link untuk fokus pada data teks
        """
        data = {}
        incoming_messages = driver.find_elements(By.XPATH, '//div[@tabindex="-1" and @role="row"]/div[@data-id]')

        for msg in incoming_messages:
            try:
                data_id = msg.get_attribute('data-id')
                msg_in = msg.find_element(By.XPATH,'.//div[contains(@class, "message-in")]')
                pre_plain_elem = msg_in.find_element(By.XPATH,'.//div[contains(@class, "copyable-text") and @data-pre-plain-text]')
                pre_plain_text = pre_plain_elem.get_attribute('data-pre-plain-text')
                match = re.search(r'\[(.*?)\]', pre_plain_text)
                if not match:
                    continue
                timestamp = datetime.strptime(match.group(1), "%H.%M, %d/%m/%Y")
                text_content = pre_plain_elem.text
                
            except Exception as e:
                continue
            if re.search(r'https?://\S+|www\.\S+', text_content) or len(text_content)<=15:
                continue
            # if len()
            # continue
            if timestamp not in data:
                data[timestamp] = {}
            if data_id not in data[timestamp]:
                data[timestamp][data_id] = []
            if text_content and text_content not in data[timestamp][data_id]:
                data[timestamp][data_id].append(text_content)
        #del incoming_messages,data_id,pre_plain_elem,pre_plain_text,timestamp,match,msg_in,text_content
        return data
    
    def check_new_respon(self, driver, waktu_terakhir_kirim_permintaan, max_timing, no_WA):
        """
        CEK RESPONS BARU DALAM INTERVAL WAKTU
        =====================================
        
        Monitoring chat untuk respons baru dalam rentang waktu tertentu.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        waktu_terakhir_kirim_permintaan : datetime
            Waktu terakhir permintaan dikirim (batas awal)
        max_timing : datetime
            Batas akhir monitoring (deadline)
        no_WA : str
            Nomor WhatsApp yang sedang dimonitor
            
        RETURNS:
        --------
        dict or None
            Data pesan baru jika ditemukan, None jika timeout
            
        ALUR:
        -----
        1. Loop monitoring selama 15 detik
        2. Ekstrak data chat setiap iterasi
        3. Cek apakah ada pesan dalam rentang waktu target
        4. Lakukan scroll untuk memuat pesan baru
        5. Return data jika ditemukan, None jika timeout
        
        CATATAN:
        --------
        - Timeout monitoring: 15 detik
        - Scroll chat untuk trigger lazy loading
        - Filter berdasarkan timestamp
        """
        start_time = time.time()
        while True:
            # Ambil data terbaru dari driver
            data_text = self.get_text_data(driver)
            
            
            # Cek apakah ada data BARU (lebih baru dari waktu referensi)
            found_new = False
            for timestamp in data_text.keys():
                if timestamp >= waktu_terakhir_kirim_permintaan and timestamp < max_timing:
                    found_new = True
                    break  # Keluar dari loop for begitu ditemukan satu data baru
            
            # Jika ditemukan data baru, keluar dari loop while
            if found_new:
                break
            
            # Jika tidak ada data baru, tunggu sebentar sebelum cek ulang
            
          
            if time.time() - start_time > 15:
                return None
            scroll_div_element = self.scroll_div_check(driver, no_WA)
            if scroll_div_element == False:
                break
            else:
                for _ in range(1):
                    driver.execute_script("arguments[0].scrollTop = 0;", scroll_div_element)
        return data_text
    
    def kirim_pesan_permintaan(self, driver, pesan_kirim: str):
        """
        KIRIM PESAN KE CHAT AKTIF
        ==========================
        
        Mengirim pesan teks ke chat yang sedang terbuka.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        pesan_kirim : str
            Teks pesan yang akan dikirim
            
        RETURNS:
        --------
        bool
            True jika pengiriman sukses, False jika gagal
            
        ALUR:
        -----
        1. Tunggu input box muncul
        2. Validasi pesan tidak kosong
        3. Click input box
        4. Ketik pesan
        5. Tekan ENTER
        
        CATATAN:
        --------
        - Menggunakan XPath spesifik untuk WhatsApp Web input box
        - Explicit wait 30 detik untuk element
        - Validasi pesan kosong untuk menghindari error
        """
        try:
            input_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//div[@aria-activedescendant and @contenteditable="true" and @role="textbox" and @aria-placeholder="Ketik pesan" and @aria-autocomplete="list"]'
                ))
            )
            try:
                if not pesan_kirim:  # Cek jika variabel kosong atau None
                    raise ValueError("❗ pesan_kirim kosong. Harap isi pesan terlebih dahulu.")
                pesan = pesan_kirim
            except NameError:
                raise NameError("❗ pesan_kirim belum didefinisikan.")
            
        except Exception as e:
            print(f"❌ Gagal mengirim pesan: {e}")
            return False
        else:
            input_box.click()
            input_box.send_keys(pesan)
            input_box.send_keys(Keys.ENTER)
            print("📩 Permintaan data terkirim.")
            return True
        
    def whatsapp_initialize(self):
        """
        INISIALISASI WHATSAPP WEB SESSION
        ==================================
        
        Proses utama untuk memulai sesi WhatsApp Web.
        
        RETURNS:
        --------
        tuple (DRIVER, WA_API)
            Driver instance dan API instance untuk penggunaan selanjutnya
            
        ALUR:
        -----
        1. Terminasi proses Edge yang masih berjalan
        2. Buat WebDriver instance baru
        3. Navigasi ke WhatsApp Web
        4. Tunggu QR code login (jika belum login)
        5. Tunggu sampai chat interface siap
        6. Klik tombol notifikasi (jika ada)
        
        CATATAN:
        --------
        - SCAN_TIMEOUT dari environment variable
        - Graceful handling untuk semua state (QR, loading, chat ready)
        - Delay 6 detik setelah login sukses untuk stabilisasi
        """
        WA_API = WhatsAPI()  # Instance dari class ini sendiri
        base_url_wa = 'https://' + "web.whatsapp.com"
        
        # Pastikan tidak ada proses Edge yang menggangu
        if WA_API.check_edge_process():
            WA_API.terminate_edge_process()
        else:
            pass
        
        # Inisialisasi driver
        DRIVER = WA_API.get_driver()
        DRIVER.get(base_url_wa)
        
        # Loop utama untuk waiting berbagai state
        while True:
            if WA_API.wait_for_dom_stable(DRIVER, timeout=int(os.getenv('SCAN_TIMEOUT'))):
                while True:
                    # Cek tiga kondisi untuk memastikan WhatsApp Web siap
                    if (WA_API.check_login_QR(DRIVER) == 0 and 
                        WA_API.check_app_initialize_screen(DRIVER) == 0 and 
                        WA_API.check_chat_icon(DRIVER) > 0):
                        
                        time.sleep(6)  # Delay untuk stabilisasi
                        # WA_API.tunggu_dan_klik_button(DRIVER,class_name="x889kno x1a8lsjc x13jy36j x64bnmy x1n2onr6 x1rg5ohu xk50ysn x1f6kntn xyesn5m x1rl75mt x19t5iym xz7t8uv x13xmedi x178xt8z x1lun4ml xso031l xpilrb4 x13fuv20 x18b5jzi x1q0q8m5 x1t7ytsu x1v8p93f x1o3jo1z x16stqrj xv5lvn5 x1hl8ikr xfagghw x9dyr19 x9lcvmn x1pse0pq xcjl5na xfn3atn x1k3x3db x9qntcr xuxw1ft xv52azi")
                        break
                    else:
                        time.sleep(1)
                        continue
                break
            else:
                continue
        
        return DRIVER, WA_API
    
    def validate_wa(self, driver, no_wa:str):
        """
        VALIDASI NOMOR WHATSAPP
        =======================
        
        Memvalidasi apakah nomor WhatsApp valid dan terdaftar.
        
        PARAMETERS:
        -----------
        driver : webdriver.Edge
            Instance WebDriver yang sedang aktif
        no_wa : str
            Nomor WhatsApp yang akan divalidasi
            
        RETURNS:
        --------
        bool
            True jika nomor valid, False jika tidak
            
        MEKANISME:
        ----------
        1. Navigasi ke chat dengan nomor target
        2. Cek popup error "Nomor telepon tidak valid"
        3. Jika popup muncul, klik "OKE" dan return False
        4. Jika tidak ada popup, nomor dianggap valid
        
        CATATAN:
        --------
        - Popup hanya muncul untuk nomor yang tidak terdaftar di WhatsApp
        - Timeout 10 detik untuk menunggu popup
        """
        url = f"https://web.whatsapp.com/send?phone={no_wa}&source=&data=#"
        driver.get(url)
        while True:
            if self.wait_for_dom_stable(driver):  # Perbaiki: self bukan WA_API
                break
            else:
                pass

        wa_val = True
        try:
            popup = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Nomor telepon yang dibagikan via tautan tidak valid."]'))
            )
            print("Dialog ditemukan.")

            # Cari dan klik tombol "OKE"
            oke_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//div[text()="OKE"]]'))
            )
            oke_button.click()
            print("Tombol OKE diklik.")
            wa_val = False
            del popup
        except Exception as e:
            print("Dialog atau tombol tidak ditemukan:", e)
            pass
        return wa_val


"""
FUNGSI HELPER YANG DIBUTUHKAN:
===============================
1. format_wa_number(no_wa): 
   - Fungsi untuk memformat nomor WhatsApp
   - Harus didefinisikan di module yang sama atau diimport
   
2. Environment Variables:
   - SCAN_TIMEOUT: Timeout untuk DOM stable check
   - Harus di-set di environment atau .env file
"""

"""
CATATAN PENTING UNTUK PENGGUNAAN:
=================================
1. Pastikan Microsoft Edge dan WebDriver versi kompatibel
2. Profile directory harus sudah login WhatsApp Web sebelumnya
3. Untuk environment baru, perlu scan QR code manual pertama kali
4. Waktu tunggu (timeout) perlu disesuaikan dengan koneksi internet
5. Implementasi ini spesifik untuk WhatsApp Web interface tertentu
   (mungkin perlu update jika WhatsApp Web berubah)

REVISI YANG DISARANKAN:
======================
1. Tambahkan exception handling yang lebih komprehensif
2. Implementasi retry mechanism untuk semua operasi
3. Logging system yang lebih baik (file-based, rotation)
4. Support untuk multiple browser (Chrome, Firefox)
5. Tambahkan method untuk handle media messages (gambar, dokumen)
6. Implementasi database untuk menyimpan chat history
"""