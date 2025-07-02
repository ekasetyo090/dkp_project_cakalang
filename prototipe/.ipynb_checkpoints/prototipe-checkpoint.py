# -*- coding: utf-8 -*-
"""
#Created on Tue Jun 24 11:59:30 2025

@author: eka setyo agung mahanani # Dinas Kelautan Dan Perikanan Kabupaten Halmahera TImur

"""

import time
import os
import json
import psutil 

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
#from selenium.common.exceptions import SessionNotCreatedException


load_dotenv()

class Whats_API():
    
    def __init__(self):
        self.driver_path = r'edge web driver\msedgedriver.exe'
        self.binary_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        self.user_data_dir = r'C:\Users\snsv\AppData\Local\Microsoft\Edge\User Data'
        self.profile_directory = 'Profile 1'
      
        
    def check_edge_process(self):
        """Cek apakah ada proses Edge (msedge.exe) yang sedang berjalan"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'msedge.exe':
                print(f"Edge is running with PID {proc.pid}")
                return True
        print("Edge is not running.")
        return False
    
    def terminate_edge_process(self):
        """Hentikan semua proses Edge (msedge.exe)"""
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
        service = Service()
        options.binary_location = self.binary_path
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument(f"profile-directory={self.profile_directory}")
        
        
        # Additional recommended options
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(executable_path=self.driver_path)
        
        driver = webdriver.Edge(service=service, options=options)
        return driver
    
    def check_login_QR(self,driver):
        elements = driver.find_elements(By.XPATH,"//canvas[@aria-label='Scan this QR code to link a device!' and @role='img']")
        return len(elements)
    
    def check_app_initialize_screen(self,driver):
        elements = driver.find_elements(By.XPATH,"//div[@id='wa_web_initial_startup' and @class='_apdl']")
        return len(elements)
    
    def check_profile_img(self,driver):
        elements = driver.find_elements(By.XPATH,"//div[@class='x1n2onr6 x1c9tyrk xeusxvb x1pahc9y x1ertn4p']")
        return len(elements)
        
    def wait_for_dom_stable(self,driver, timeout=30, check_interval=0.5):
        """Menunggu hingga DOM stabil (tidak ada perubahan)"""
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
            # Reset flag
            driver.execute_script("window.domChanged = false;")
            time.sleep(check_interval)
        return False
    
        
def main_program():
    
    WA_API = Whats_API()
    
    if WA_API.check_edge_process():
        WA_API.terminate_edge_process()
    else:
        pass
    
    DRIVER = WA_API.get_driver()
    #google_url = 'https://' +"www.google.com"
    base_url_wa = 'https://' +"web.whatsapp.com"

    
    cookie_path = os.getenv('COOKIE_PATH')
    if not os.path.exists(cookie_path):
        print(f"Not found existing cookies at: {cookie_path}")
        
        
        
    else:
        try:
            DRIVER.get(base_url_wa)
            DRIVER.refresh()
            
            
            with open(cookie_path) as file:
                cookies = json.load(file)
            for cookie in cookies:
                DRIVER.add_cookie(cookie)
            #with open(cookie_path, "rb") as f:
            #    cookies = pickle.load(f)
            
            # Periksa apakah cookies None atau kosong sebelum iterasi
            #if cookies is None:
            #    print("⚠️ Warning: No cookies found in file")
            #else:
            #    for cookie in cookies:
            #        try:
            #            DRIVER.add_cookie(cookie)
            #        except Exception as e:#
            #            print(f"⚠️ Warning: Could not add cookie {cookie.get('name')}: {str(e)}")
        
        except Exception as e:
            # Tangani error yang terjadi saat loading file
            print(f"⚠️ Error loading cookies: {str(e)}")
    
    DRIVER.refresh()
   
    while True:
        if WA_API.wait_for_dom_stable(DRIVER,timeout=int(os.getenv('SCAN_TIMEOUT'))):
            #check jika ada file cookies
            
            while True:
        
                if WA_API.check_login_QR(DRIVER) == 0 and WA_API.check_app_initialize_screen(DRIVER) == 0 and WA_API.check_profile_img(DRIVER)>0:
                   # with open(cookie_path, 'wb') as file:
                        #pickle.dump(DRIVER.get_cookies(), file)
                    with open(cookie_path, 'w') as file:
                        json.dump(DRIVER.get_cookies(), file, indent=4)
                    print('login')
                    break
                else:
                    print('scaan')
                    time.sleep(1)
                    continue
            break
            
        else:
            continue
        
    
    
    url_mesage = base_url_wa+"/send?phone={}&source=&data=#"
    
    DRIVER.get(url_mesage.format('6282192362650'))
    
    
    print("\nYou can now close this window or press Ctrl+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        DRIVER.quit()
        print("\nBrowser closed. Next time you run this script, ")
        print("it should automatically log you in using the saved profile.")

if __name__ == "__main__":
    main_program()