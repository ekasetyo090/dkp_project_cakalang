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




class WhatsAPI:
    def __init__(self):
        self.driver_path = r'edge web driver\msedgedriver.exe'
        self.binary_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        self.user_data_dir = r'C:\Users\eka agung\AppData\Local\Microsoft\Edge\User Data'
        self.profile_directory = 'Default'

    def check_edge_process(self):
        return any(proc.info['name'] == 'msedge.exe' for proc in psutil.process_iter(['name']))

    def terminate_edge_process(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'msedge.exe':
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"Terminated Edge process with PID {proc.pid}")
                except Exception as e:
                    print(f"Failed to terminate process {proc.pid}: {e}")

    def get_driver(self):
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
        return len(driver.find_elements(By.XPATH, "//canvas[@aria-label='Scan this QR code to link a device!' and @role='img']"))

    def check_app_initialize_screen(self, driver):
        return len(driver.find_elements(By.XPATH, "//div[@id='wa_web_initial_startup' and @class='_apdl']"))

    def check_chat_icon(self, driver):
        return len(driver.find_elements(By.XPATH, "//div[@class='x1c4vz4f xs83m0k xdl72j9 x1g77sc7 x78zum5 xozqiw3 x1oa3qoh x12fk4p8 xeuugli x2lwn1j x1nhvcw1 x1q0g3np x6s0dn4 xh8yej3']"))

    def get_profile_name_elements(self, driver):
        return driver.find_elements(By.XPATH, "//span[@dir='auto' and @class='x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1rg5ohu _ao3e']")

    def process_profile_name_element(self, element):
        html = element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(strip=True)
        return text

    def wait_for_dom_stable(self, driver, timeout=30, check_interval=0.5):
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
        while time.time() < end_time:
            changed = driver.execute_script("return window.domChanged;")
            if not changed:
                return True
            driver.execute_script("window.domChanged = false;")
            time.sleep(check_interval)
        return False
    def check_button(self,driver,xpath:str):
        return driver.find_elements(By.XPATH, xpath)
        
    def tunggu_dan_klik_button(self, driver, class_name="x", timeout=30):
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

    def scroll_message(self, driver, times=1):
        try:
            scrollable_div = driver.find_element(
                By.XPATH,
                '//div[@class="x10l6tqk x13vifvy x1o0tod xyw6214 x9f619 x78zum5 xdt5ytf xh8yej3 x5yr21d x6ikm8r x1rife3k xjbqb8w x1ewm37j" and @tabindex="0"]'
            )
            for _ in range(times):
                driver.execute_script("arguments[0].scrollTop = 0;", scrollable_div)
        except NoSuchElementException:
            print("Elemen tidak ditemukan. Melakukan refresh halaman...")
            driver.refresh()
            time.sleep(3)

    def get_text_data(self,driver):
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
            if re.search(r'https?://\S+|www\.\S+', text_content) or len(text_content)==0:
                continue
            # continue
            if timestamp not in data:
                data[timestamp] = {}
            if data_id not in data[timestamp]:
                data[timestamp][data_id] = []
            if text_content and text_content not in data[timestamp][data_id]:
                data[timestamp][data_id].append(text_content)
        #del incoming_messages,data_id,pre_plain_elem,pre_plain_text,timestamp,match,msg_in,text_content
        return data
    def check_new_respon(self,driver,waktu_terakhir_kirim_permintaan):
        start_time = time.time()
        while True:
            # Ambil data terbaru dari driver
            data_text = self.get_text_data(driver)
            
            
            # Cek apakah ada data BARU (lebih baru dari waktu referensi)
            found_new = False
            for timestamp in data_text.keys():
                if timestamp < waktu_terakhir_kirim_permintaan:
                    found_new = True
                    break  # Keluar dari loop for begitu ditemukan satu data baru
            
            # Jika ditemukan data baru, keluar dari loop while
            if found_new:
                break
            
            # Jika tidak ada data baru, tunggu sebentar sebelum cek ulang
            
          
            if time.time() - start_time > 15:
                return None
            self.scroll_message(driver)
        return data_text
    
    def kirim_pesan_permintaan(self, driver, pesan_kirim: str):
        try:
            input_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//div[@contenteditable="true" and @aria-label="Ketik pesan"]'
                ))
            )
            try:
                if not pesan_kirim:  # Cek jika variabel kosong atau None
                    raise ValueError("❗ pesan_kirim kosong. Harap isi pesan terlebih dahulu.")
                pesan = pesan_kirim
            except NameError:
                raise NameError("❗ pesan_kirim belum didefinisikan.")
            input_box.click()
            input_box.send_keys(pesan)
            input_box.send_keys(Keys.ENTER)
            print("📩 Permintaan data terkirim.")
            return True
        except Exception as e:
            print(f"❌ Gagal mengirim pesan: {e}")
            return False