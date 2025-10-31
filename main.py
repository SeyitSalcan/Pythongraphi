"""
SQL Panel - Modüler Veritabanı Yönetim Sistemi
Ana Başlatıcı Dosya
"""

import sys
from pathlib import Path

# Modülleri import et
from gui.main_window import MainWindow

def main():
    """Uygulamayı başlat"""
    try:
        app = MainWindow()
        app.run()
    except ImportError as e:
        print("❌ Gerekli kütüphaneler eksik!")
        print("Lütfen şu komutu çalıştırın:")
        print("pip install pandas openpyxl")
        print(f"\nDetaylı hata: {e}")
    except Exception as e:
        print(f"❌ Uygulama başlatılamadı: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()