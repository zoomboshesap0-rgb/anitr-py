#!/usr/bin/env python3
"""
anitr-py kurulum betiği
"""

import os
import sys
import subprocess
from pathlib import Path

def bagimliliklari_kontrol_et():
    """Gerekli sistem bağımlılıklarının yüklü olup olmadığını kontrol eder"""
    bagimliliklar = ["mpv"]
    
    eksikler = []
    for bagimlilik in bagimliliklar:
        try:
            subprocess.run(["which", bagimlilik], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            eksikler.append(bagimlilik)
    
    if eksikler:
        print("Eksik sistem bağımlılıkları:")
        for bagimlilik in eksikler:
            print(f"  - {bagimlilik}")
        print("\nLütfen bu bağımlılıkları yükleyip tekrar deneyin.")
        return False
    
    return True

def python_bagimliliklarini_yukle():
    """Python bağımlılıklarını yükler"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Python bağımlılıkları yüklenemedi")
        return False

def calistirilabilir_yap():
    """main.py dosyasını çalıştırılabilir yapar"""
    try:
        main_py = Path("main.py")
        if main_py.exists():
            main_py.chmod(0o755)
        return True
    except Exception as e:
        print(f"main.py çalıştırılabilir yapılamadı: {e}")
        return False

def sembolik_baglanti_olustur():
    """/usr/local/bin dizininde sembolik bağlantı oluşturur"""
    try:
        # /usr/local/bin dizininde sembolik bağlantı oluşturmaya çalış
        hedef = Path("/usr/local/bin/anitr-py")
        kaynak = Path(os.getcwd()) / "main.py"
        
        # Mevcut sembolik bağlantıyı kaldır (varsa)
        if hedef.exists():
            hedef.unlink()
        
        # Yeni sembolik bağlantı oluştur
        hedef.symlink_to(kaynak)
        print("anitr-py başarıyla kuruldu")
        print("Artık her yerden 'anitr-py' komutuyla çalıştırabilirsiniz")
        return True
    except PermissionError:
        print("İzin reddedildi. sudo ile çalıştırmayı deneyin:")
        print("  sudo python3 setup.py")
        return False
    except Exception as e:
        print(f"Sembolik bağlantı oluşturulamadı: {e}")
        return False

def main():
    print("anitr-py kuruluyor...")
    
    # Sistem bağımlılıklarını kontrol et
    if not bagimliliklari_kontrol_et():
        sys.exit(1)
    
    # Python bağımlılıklarını yükle
    if not python_bagimliliklarini_yukle():
        sys.exit(1)
    
    # Çalıştırılabilir yap
    if not calistirilabilir_yap():
        sys.exit(1)
    
    # Sembolik bağlantı oluştur
    if not sembolik_baglanti_olustur():
        sys.exit(1)

if __name__ == "__main__":
    main()