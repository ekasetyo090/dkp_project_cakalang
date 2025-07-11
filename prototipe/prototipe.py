# -*- coding: utf-8 -*-
"""
#Created on Tue Jun 24 11:59:30 2025

@author: eka setyo agung mahanani # Dinas Kelautan Dan Perikanan Kabupaten Halmahera TImur

"""

import time
import os
import psutil
import re

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
#from selenium.common.exceptions import SessionNotCreatedException
from bs4 import BeautifulSoup


#load_dotenv()



#load_dotenv(find_dotenv())
class Whats_API():
    
    def __init__(self):
        self.driver_path = r'edge web driver\msedgedriver.exe'
        self.binary_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        self.user_data_dir = r'C:\Users\eka agung\AppData\Local\Microsoft\Edge\User Data'
        self.profile_directory = 'Default'
      
        
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
        #service = Service()
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
        elements = driver.find_elements(
            By.XPATH,"//canvas[@aria-label='Scan this QR code to link a device!' and @role='img']"
        )
        return len(elements)
    
    def check_app_initialize_screen(self,driver):
        elements = driver.find_elements(
            By.XPATH,"//div[@id='wa_web_initial_startup' and @class='_apdl']"
        )
        return len(elements)
    
    def check_profile_img(self,driver):
        elements = driver.find_elements(
            By.XPATH,"//div[@class='x1n2onr6 x1c9tyrk xeusxvb x1pahc9y x1ertn4p']"
        )
        return len(elements)
    def get_profile_name_elemen(self,driver):
        elements = driver.find_elements(
            By.XPATH,"//span[@dir='auto' and @class='x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1rg5ohu _ao3e']"
        )
        return elements
    def process_profile_name_element(self,elements):
        html = elements.get_attribute("outerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        
        text = soup.get_text(strip=True)
        del soup,html
        return text
        
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
    
    def button_click(self,DRIVER):
        try:
            WebDriverWait(DRIVER, 10).until(EC.presence_of_element_located(
                (
                By.XPATH,
                '//button[@class="x889kno.x1a8lsjc.x13jy36j.x64bnmy.x1n2onr6.x1rg5ohu.xk50ysn.x1f6kntn.xyesn5m.x1rl75mt.x19t5iym.xz7t8uv.x13xmedi.x178xt8z.x1lun4ml.xso031l.xpilrb4.x13fuv20.x18b5jzi.x1q0q8m5.x1t7ytsu.x1v8p93f.x1o3jo1z.x16stqrj.xv5lvn5.x1hl8ikr.xfagghw.x9dyr19.x9lcvmn.x1pse0pq.xcjl5na.xfn3atn.x1k3x3db.x9qntcr.xuxw1ft.xv52azi"]'
                #"button.x889kno.x1a8lsjc.x13jy36j.x64bnmy.x1n2onr6.x1rg5ohu.xk50ysn.x1f6kntn.xyesn5m.x1rl75mt.x19t5iym.xz7t8uv.x13xmedi.x178xt8z.x1lun4ml.xso031l.xpilrb4.x13fuv20.x18b5jzi.x1q0q8m5.x1t7ytsu.x1v8p93f.x1o3jo1z.x16stqrj.xv5lvn5.x1hl8ikr.xfagghw.x9dyr19.x9lcvmn.x1pse0pq.xcjl5na.xfn3atn.x1k3x3db.x9qntcr.xuxw1ft.xv52azi"
            )))
        except TimeoutException:
            pass
        else:
            button = DRIVER.find_element(
                By.XPATH,
                '//button[@class="x889kno.x1a8lsjc.x13jy36j.x64bnmy.x1n2onr6.x1rg5ohu.xk50ysn.x1f6kntn.xyesn5m.x1rl75mt.x19t5iym.xz7t8uv.x13xmedi.x178xt8z.x1lun4ml.xso031l.xpilrb4.x13fuv20.x18b5jzi.x1q0q8m5.x1t7ytsu.x1v8p93f.x1o3jo1z.x16stqrj.xv5lvn5.x1hl8ikr.xfagghw.x9dyr19.x9lcvmn.x1pse0pq.xcjl5na.xfn3atn.x1k3x3db.x9qntcr.xuxw1ft.xv52azi"]'
            )
            button.click()
    def scroll_message(self,DRIVER,times:int):
        try:
            scrollable_div = DRIVER.find_element(
                By.XPATH,
                '//div[@class="x10l6tqk x13vifvy x1o0tod xyw6214 x9f619 x78zum5 xdt5ytf xh8yej3 x5yr21d x6ikm8r x1rife3k xjbqb8w x1ewm37j"and @tabindex="0"]'
            )
            print("Elemen ditemukan.")
            # Scroll ke atas jika ditemukan
            DRIVER.execute_script("arguments[0].scrollTop = 0;", scrollable_div)

        except NoSuchElementException:
            print("Elemen tidak ditemukan. Melakukan refresh halaman...")
            DRIVER.refresh()
            time.sleep(3)
        else:
            for i in range(0,times,1):
                DRIVER.execute_script("arguments[0].scrollTop = 0;", scrollable_div)
    
        
def main_program():
    # First Stage
    WA_API = Whats_API()
    base_url_wa = 'https://' +"web.whatsapp.com"
    if WA_API.check_edge_process():
        WA_API.terminate_edge_process()
    else:
        pass
    DRIVER = WA_API.get_driver()
    DRIVER.get(base_url_wa)
    while True:
        if WA_API.check_login_QR(DRIVER) == 0 and WA_API.check_app_initialize_screen(DRIVER) == 0 and WA_API.check_profile_img(DRIVER)>0:
            time.sleep(10)
            WA_API.button_click(DRIVER)
            break
        else:
            time.sleep(1)
            continue
        
        

    # Open Coresponden Message
    url_mesage = base_url_wa+"/send?phone={}&source=&data=#"
    DRIVER.get(url_mesage.format('6282192362650'))
    while True:
        try:
            name_element = WA_API.get_profile_name_elemen(DRIVER)
        except error:
            DRIVER.refresh()
            time.sleep(15)
            continue

        if len(element)>0:
            profile_name = WA_API.process_profile_name_element(name_element[0])
            del name_element
            break
        else:
            continue
    # Driver wait for
    div_element = WebDriverWait(DRIVER, 10).until(
        EC.visibility_of_element_located((
            By.XPATH,
            '//div[@class="x1n2onr6 x1c9tyrk xeusxvb x1pahc9y x1ertn4p"]'
        ))
    )
    WA_API.button_click(DRIVER)



    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        DRIVER.quit()
        print("\nBrowser closed. Next time you run this script, ")
        print("it should automatically log you in using the saved profile.")

if __name__ == "__main__":
    main_program()