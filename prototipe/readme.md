# WhatsApp Automated Data Collection System

Sistem ini adalah aplikasi otomatisasi berbasis Python yang mengirim dan memproses pesan WhatsApp Web melalui browser Microsoft Edge menggunakan Selenium. Sistem ini terintegrasi dengan MySQL untuk pencatatan pesan, penjadwalan ulang permintaan data, dan pelacakan respons pengguna.

---

## 📦 Fitur Utama

- Mengambil dan memformat data koresponden dari database MySQL.
- Menginisialisasi sesi WhatsApp Web dengan profil pengguna.
- Mengirim pesan otomatis berdasarkan jadwal atau kondisi tertentu.
- Mengecek balasan pesan dan menyimpan ke dalam database.
- Mengelola jadwal pengiriman pesan berdasarkan respon atau tidaknya penerima.
- Sistem penjadwalan adaptif: normal vs. eskalasi.

---

## 🚀 Persyaratan

- Python 3.7+
- WebDriver Microsoft Edge (`msedgedriver.exe`)
- Edge Browser terinstal dan login ke WhatsApp Web
- Database MySQL aktif
- File `.env` untuk konfigurasi

---

## 🗂️ Struktur Folder

```
project/
├── utils/
│   └── wa_api.py
├── .env
├── main_script.py
└── README.md
```
[Lihat SISTEM MANAJEMEN](https://github.com/ekasetyo090/dkp_project_cakalang/blob/main/prototipe/prototipe.py)
[Lihat API `WhatsApp API()`](https://github.com/ekasetyo090/dkp_project_cakalang/tree/main/prototipe/utils)
---

## 🔧 Konfigurasi `.env`

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=nama_database
MYSQL_PORT=3306
SCAN_TIMEOUT=10
```

---

## ⚙️ Cara Menjalankan

1. **Pastikan environment sudah diatur dengan benar**:
   - Sudah login ke WhatsApp Web menggunakan profil Edge
   - `.env` sudah diisi
   - Struktur database sudah siap

2. **Jalankan program**:

```bash
python main_script.py
```

3. **Proses**:
   - Sistem akan membuka WhatsApp Web
   - Mengambil koresponden berdasarkan ID dari database
   - Mengirim pesan otomatis jika jadwal pengiriman terpenuhi
   - Mengecek apakah sudah ada respon
   - Menyimpan data respon ke tabel
   - Memperbarui log dan jadwal pengiriman berikutnya

---

## 🧠 Logika Penjadwalan

- `normal`: Jika belum pernah mengirim pesan atau tidak ada respon sebelumnya.
- `eskalasi`: Jika sudah mengirim tapi belum ada respon.

Parameter waktu diatur melalui:

```python
JADWAL_SWITCH_PARAM = {
    'prototipe': {'normal': timedelta(minutes=0.3), 'eskalasi': timedelta(minutes=0.1)},
    'production': {'normal': timedelta(days=7), 'eskalasi': timedelta(days=3)}
}
```

---

## 🗃️ Struktur Tabel MySQL

- `data_koresponden` – informasi kontak dan metadata.
- `log_pengiriman_permintaan` – menyimpan waktu pengiriman dan status respon.
- `jadwal_pengiriman_pesan_selanjutnya` – jadwal pengiriman berikutnya per nomor.
- `respon_koresponden` & `text_respon` – menyimpan respon teks terstruktur.

---

## ⚠️ Catatan

- Tidak menerima pesan dalam bentuk gambar, video, dan suara.
- Sistem hanya memproses **teks** dan link akan diabaikan.
- Hanya untuk keperluan internal atau edukatif.

---

## 👨‍💻 Pengembang

Dikembangkan oleh: Eka Agung  
Kontak: [Hubungi melalui WhatsApp] atau email sesuai kebutuhan proyek.

---

## 📝 Lisensi

MIT License — bebas digunakan, dimodifikasi, dan disebarkan dengan menyertakan atribusi.