# WhatsAPI Automation for WhatsApp Web (Microsoft Edge)

Script ini adalah modul otomatisasi WhatsApp Web menggunakan **Selenium WebDriver** dan browser **Microsoft Edge**, untuk keperluan seperti mengirim pesan otomatis, membaca pesan masuk, dan mengelola sesi login menggunakan profil pengguna.

---

## 📦 Fitur Utama

- Cek dan terminasi proses Microsoft Edge.
- Otomatis membuka WhatsApp Web dengan profil pengguna yang telah login.
- Deteksi status login (QR Code / Layar inisialisasi / Ikon chat).
- Ambil nama profil dan teks pesan masuk.
- Scroll chat secara otomatis.
- Kirim pesan permintaan secara otomatis.
- Deteksi pesan baru berdasarkan waktu.
- Deteksi elemen tombol dan klik otomatis.
- Menunggu kestabilan DOM sebelum interaksi.

---

## 🚀 Persyaratan

- Python 3.7+
- WebDriver Microsoft Edge (`msedgedriver.exe`)
- Browser Microsoft Edge terinstal
- Profil pengguna sudah login ke WhatsApp Web

### 📚 Library Python

Instal pustaka yang dibutuhkan:

```bash
pip install selenium beautifulsoup4 psutil
```

---

## 🔧 Konfigurasi

Sunting path di `__init__()` agar sesuai dengan sistem lokal Anda:

```python
self.driver_path = r'edge web driver\msedgedriver.exe'
self.binary_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
self.user_data_dir = r'C:\Users\<NAMA_USER>\AppData\Local\Microsoft\Edge\User Data'
self.profile_directory = 'Default'
```

---

## ⚙️ Cara Menggunakan

### 1. Inisialisasi dan Buka WhatsApp Web

```python
api = WhatsAPI()

if api.check_edge_process():
    api.terminate_edge_process()

driver = api.get_driver()
```

### 2. Cek Status Login WhatsApp

```python
if api.check_login_QR(driver):
    print("Silakan scan QR code WhatsApp Web.")
elif api.check_app_initialize_screen(driver):
    print("WhatsApp Web sedang dalam proses inisialisasi.")
elif api.check_chat_icon(driver):
    print("✅ Berhasil login ke WhatsApp Web.")
```

### 3. Kirim Pesan Otomatis

```python
pesan = "Halo, mohon kirimkan data konsumsi ikan hari ini."
api.kirim_pesan_permintaan(driver, pesan)
```

### 4. Ambil Data Teks

```python
data = api.get_text_data(driver)
print(data)
```

### 5. Cek Respon Baru Berdasarkan Waktu

```python
from datetime import datetime, timedelta
last_sent_time = datetime.now() - timedelta(minutes=5)
respon_baru = api.check_new_respon(driver, last_sent_time)
```

---

## 🧪 Struktur Fungsi

| Fungsi | Deskripsi |
|--------|-----------|
| `get_driver()` | Inisialisasi Selenium WebDriver dengan profil pengguna Edge |
| `check_login_QR()` | Cek apakah QR Code muncul |
| `check_chat_icon()` | Cek apakah sudah login dan ikon chat muncul |
| `scroll_message(times)` | Scroll ke atas untuk memuat pesan lama |
| `get_text_data()` | Ambil semua pesan masuk sebagai dictionary |
| `kirim_pesan_permintaan(pesan)` | Kirim teks ke kontak saat ini |
| `check_new_respon(waktu)` | Cek apakah ada respon baru lebih baru dari waktu tertentu |
| `tunggu_dan_klik_button()` | Klik tombol berdasarkan class tertentu (dengan timeout) |
| `wait_for_dom_stable()` | Tunggu hingga DOM stabil (tidak berubah) |
| `process_profile_name_element()` | Ekstrak nama dari elemen HTML menggunakan BeautifulSoup |

---

## ⚠️ Catatan Penting

- Script ini tidak menggunakan API resmi WhatsApp (seperti WhatsApp Business API) dan bergantung pada elemen DOM, yang bisa berubah sewaktu-waktu.
- Gunakan hanya untuk keperluan pribadi atau edukasi.
- Jangan gunakan untuk spam atau kegiatan ilegal lainnya.

---

## 🧑‍💻 Kontributor

Developed by Eka Agung  
Tanya jawab atau saran? Silakan kirim pesan langsung.

---

## 📝 Lisensi

MIT License — bebas digunakan, modifikasi, dan distribusi dengan menyertakan atribusi.