from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def get_previous_month_date(today):
    """Mendapatkan tanggal bulan sebelumnya."""
    return (today.replace(day=1) - relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0)

def get_next_month_date(tanggal_data):
    """Mendapatkan tanggal bulan berikutnya."""
    return (tanggal_data + relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0)

def get_data_deadline(tanggal_data):
    """Mendapatkan batas pengambilan data (2 bulan setelah tanggal data)."""
    return (tanggal_data + relativedelta(months=2)).replace(hour=0, minute=0, second=0, microsecond=0)

def is_time_for_reminder(today, reminder_date):
    """Memeriksa apakah sudah waktunya untuk mengirim reminder."""
    return today >= reminder_date