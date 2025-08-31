# anitr-py

Terminalde Türkçe altyazılı anime arama ve izleme aracı 🚀

Bu uygulama, orijinal [anitr-cli](https://github.com/axrona/anitr-cli) uygulamasının sadece AnimeCix kaynağını kullanan Python sürümüdür.

## 🎬 Özellikler

- **AnimeCix Entegrasyonu**: AnimeCix'ten anime arama ve izleme
- **İzleme Geçmişi**: İzleme geçmişini kaydetme
- **Terminal tabanlı arayüz**: Basit metin tabanlı kullanıcı arayüzü
- **MPV Oynatıcı**: Video oynatımı için MPV kullanır
- **Türkçe Altyazı**: Müsait olduğunda otomatik olarak Türkçe altyazı yükler

## ⚡ Kurulum

### 🐧 Linux

1. Sistem bağımlılıklarını yükleyin:
   ```bash
   # Ubuntu/Debian
   sudo apt install mpv python3 python3-pip
   
   # Arch/Manjaro
   sudo pacman -S mpv python3 python-pip
   
   # Fedora
   sudo dnf install mpv python3 python3-pip
   ```

2. Klonlayın ve kurun:
   ```bash
   git clone https://github.com/your-username/anitr-py.git
   cd anitr-py
   python3 setup.py
   ```

### 🪟 Windows

1. [MPV](https://sourceforge.net/projects/mpv-player-windows/files/) yükleyin
2. [Python 3](https://www.python.org/downloads/) yükleyin
3. Klonlayın ve kurun:
   ```cmd
   git clone https://github.com/your-username/anitr-py.git
   cd anitr-py
   pip install -r requirements.txt
   ```

### 💻 MacOS

1. Bağımlılıkları yükleyin:
   ```bash
   brew install mpv python3
   ```

2. Klonlayın ve kurun:
   ```bash
   git clone https://github.com/your-username/anitr-py.git
   cd anitr-py
   python3 setup.py
   ```

## 🚀 Kullanım

```bash
anitr-py [bayraklar]
```

Bayraklar:
  `--rpc-devre-disi`      Discord Rich Presence özelliğini kapatır
  `--surum`, `-v`         Sürüm bilgisini gösterir
  `--help`, `-h`          Yardım menüsünü gösterir

## ⚙️ Yapılandırma

Yapılandırma dosyası şu konumdadır:
- **Linux / macOS:** `~/.anitr-py/config.json`
- **Windows:** `%APPDATA%\AnitrPy\config.json`

```json
{
  "varsayilan_kaynak": "animecix",
  "gecmis_limiti": 0,
  "rpc_devre_disi": false
}
```

## 📜 Lisans

Bu proje GNU GPLv3 Lisansı altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın.