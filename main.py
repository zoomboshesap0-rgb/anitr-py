#!/usr/bin/env python3
"""
anitr-py - Terminalde Türkçe altyazılı anime arama ve izleme aracı
"""

import argparse
import json
import os
import sys
import time
import subprocess
import requests
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
import urllib.parse

# Yapılandırma
CONFIG_DIR = Path.home() / ".anitr-py"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "gecmis.json"
VIDEOS_DIR = Path.home() / "Videolar" / "anitr-py"

# Yapılandırma dizinini oluştur (yoksa)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Varsayılan yapılandırma
DEFAULT_CONFIG = {
    "varsayilan_kaynak": "animecix",
    "gecmis_limiti": 0,
    "rpc_devre_disi": False
}

class Config:
    def __init__(self):
        self.config = self.yukle_config()
    
    def yukle_config(self) -> Dict[str, Any]:
        """Yapılandırmayı dosyadan yükle veya varsayılanları kullan"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                return DEFAULT_CONFIG
        else:
            # Varsayılan yapılandırmayı kaydet
            self.kaydet_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    
    def kaydet_config(self, config: Dict[str, Any]) -> None:
        """Yapılandırmayı dosyaya kaydet"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

class Logger:
    def __init__(self):
        self.log_file = CONFIG_DIR / "anitr-py.log"
    
    def hata_kaydet(self, error: Exception) -> None:
        """Hatayı dosyaya kaydet"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[HATA] {time.strftime('%Y-%m-%d %H:%M:%S')} - {str(error)}\n")
    
    def mesaj_kaydet(self, message: str) -> None:
        """Mesajı dosyaya kaydet"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[BILGI] {time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

class AnimeCix:
    """AnimeCix kaynak uygulaması"""
    
    def __init__(self):
        self.base_url = "https://animecix.tv/"
        self.alternative_url = "https://mangacix.net/"
        self.video_players = ["tau-video.xyz", "sibnet"]
        self.http_headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "x-e-h": "=.a"
        }
    
    def kaynak(self) -> str:
        return "AnimeciX"
    
    def arama_verisi_al(self, sorgu: str) -> List[Dict[str, Any]]:
        """Sorgu için arama verilerini al"""
        # Türkçe karakterleri normalize et
        normalize_edilmis_sorgu = self._turkce_normalize(sorgu).replace(" ", "-")
        
        url = f"{self.base_url}secure/search/{normalize_edilmis_sorgu}?type=&limit=20"
        try:
            response = requests.get(url, headers=self.http_headers)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            return_data = []
            
            for item in results:
                return_data.append({
                    "id": item.get("id"),
                    "baslik": item.get("name", ""),
                    "tur": item.get("type", ""),
                    "baslik_turu": item.get("title_type", ""),
                    "gorsel_url": item.get("poster", "")
                })
            
            return return_data
        except Exception as e:
            raise Exception(f"Arama başarısız: {str(e)}")
    
    def id_ile_anime_al(self, anime_id: str) -> Dict[str, Any]:
        """ID ile anime verisini al"""
        try:
            url = f"{self.base_url}secure/titles/{anime_id}?titleId={anime_id}"
            response = requests.get(url, headers=self.http_headers)
            response.raise_for_status()
            data = response.json()
            
            title_data = data.get("title", {})
            return {
                "id": int(anime_id),
                "baslik": title_data.get("name", ""),
                "tur": title_data.get("type", ""),
                "baslik_turu": title_data.get("title_type", ""),
                "gorsel_url": title_data.get("poster", "")
            }
        except Exception as e:
            raise Exception(f"Anime verisi alınamadı: {str(e)}")
    
    def bolumler_verisini_al(self, sezon_id: int) -> List[Dict[str, Any]]:
        """Sezon için bölüm verilerini al"""
        try:
            bolumler_raw = self._anime_bolumleri_verisini_al(sezon_id)
            bolumler = []
            
            for i, item in enumerate(bolumler_raw):
                bolumler.append({
                    "id": item["url"],
                    "baslik": item["name"],
                    "numara": i + 1,
                    "ekstra": {"sezon_num": item["season_num"]}
                })
            
            return bolumler
        except Exception as e:
            raise Exception(f"Bölümler alınamadı: {str(e)}")
    
    def izleme_verisini_al(self, bolum_url: str) -> List[Dict[str, str]]:
        """Bölüm için izleme verisini al"""
        try:
            return self._anime_izle_api_url(bolum_url)
        except Exception as e:
            raise Exception(f"İzleme verisi alınamadı: {str(e)}")
    
    def tr_altyazi_al(self, sezon_indeks: int, bolum_indeks: int, anime_id: int) -> str:
        """Türkçe altyazı URL'sini al"""
        try:
            url = f"{self.alternative_url}secure/related-videos?episode=1&season={sezon_indeks+1}&titleId={anime_id}&videoId=637113"
            response = requests.get(url, headers=self.http_headers)
            response.raise_for_status()
            data = response.json()
            
            videolar = data.get("videos", [])
            if bolum_indeks < len(videolar):
                video = videolar[bolum_indeks]
                altyazilar = video.get("captions", [])
                
                # Türkçe altyazıyı ara
                for altyazi in altyazilar:
                    if altyazi.get("language") == "tr":
                        return altyazi.get("url", "")
                
                # Türkçe altyazı yoksa ilkini döndür
                if altyazilar:
                    return altyazilar[0].get("url", "")
            
            return ""
        except Exception:
            return ""
    
    def _anime_bolumleri_verisini_al(self, anime_id: int) -> List[Dict[str, Any]]:
        """Anime bölümleri verisini al"""
        bolumler = []
        gorulmus_bolumler = set()
        
        try:
            sezonlar = self._anime_sezonlari_verisini_al(anime_id)
            
            for sezon_indeks in sezonlar:
                url = f"{self.alternative_url}secure/related-videos?episode=1&season={sezon_indeks+1}&titleId={anime_id}&videoId=637113"
                response = requests.get(url, headers=self.http_headers)
                response.raise_for_status()
                data = response.json()
                
                videolar = data.get("videos", [])
                for video in videolar:
                    name = video.get("name", "")
                    if name not in gorulmus_bolumler:
                        bolum_url = video.get("url", "")
                        sezon_num = video.get("season_num")
                        bolumler.append({
                            "name": name,
                            "url": bolum_url,
                            "season_num": sezon_num
                        })
                        gorulmus_bolumler.add(name)
            
            return bolumler
        except Exception as e:
            raise Exception(f"Bölümler alınamadı: {str(e)}")
    
    def _anime_sezonlari_verisini_al(self, anime_id: int) -> List[int]:
        """Anime sezonları verisini al"""
        try:
            url = f"{self.alternative_url}secure/related-videos?episode=1&season=1&titleId={anime_id}&videoId=637113"
            response = requests.get(url, headers=self.http_headers)
            response.raise_for_status()
            data = response.json()
            
            videolar = data.get("videos", [])
            if videolar:
                baslik = videolar[0].get("title", {})
                sezonlar = baslik.get("seasons", [])
                return list(range(len(sezonlar)))
            
            return []
        except Exception as e:
            raise Exception(f"Sezonlar alınamadı: {str(e)}")
    
    def _anime_izle_api_url(self, bolum_url: str) -> List[Dict[str, str]]:
        """Bölüm için video URL'lerini al"""
        try:
            izle_url = f"{self.base_url}{bolum_url}"
            response = requests.get(izle_url)
            
            if response.status_code == 422:
                raise Exception("Bölüm verisi beklenen formatta değil")
            
            final_url = response.url
            parsed_url = urllib.parse.urlparse(final_url)
            path_parts = parsed_url.path.split("/")
            
            if len(path_parts) < 3:
                raise Exception("Yol verisi beklenen formatta değil")
            
            embed_id = path_parts[2]
            query_params = urllib.parse.parse_qs(parsed_url.query)
            vid = query_params.get("vid", [""])[0]
            
            api_url = f"https://{self.video_players[0]}/api/video/{embed_id}?vid={vid}"
            api_response = requests.get(api_url)
            api_response.raise_for_status()
            
            video_data = api_response.json()
            urls = video_data.get("urls", [])
            
            results = []
            for item in urls:
                results.append({
                    "etiket": item.get("label", ""),
                    "url": item.get("url", "")
                })
            
            return results
        except Exception as e:
            raise Exception(f"Video URL'leri alınamadı: {str(e)}")
    
    def _turkce_normalize(self, text: str) -> str:
        """Türkçe karakterleri ASCII ile değiştir"""
        replacements = {
            "ö": "o", "ü": "u", "ı": "i", "ç": "c", "ş": "s", "ğ": "g",
            "Ö": "O", "Ü": "U", "İ": "I", "Ç": "C", "Ş": "S", "Ğ": "G"
        }
        
        for turkish, ascii_char in replacements.items():
            text = text.replace(turkish, ascii_char)
        
        return text

class GecmisYonetici:
    """Anime izleme geçmişi yöneticisi"""
    
    def __init__(self):
        self.gecmis_dosya = HISTORY_FILE
        self.gecmis = self._gecmis_yukle()
    
    def _gecmis_yukle(self) -> Dict[str, Any]:
        """Geçmişi dosyadan yükle"""
        if self.gecmis_dosya.exists():
            try:
                with open(self.gecmis_dosya, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def gecmis_kaydet(self) -> None:
        """Geçmişi dosyaya kaydet"""
        try:
            with open(self.gecmis_dosya, 'w', encoding='utf-8') as f:
                json.dump(self.gecmis, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Geçmiş kaydedilemedi: {e}")
    
    def gecmis_guncelle(self, kaynak: str, anime_adi: str, bolum_adi: str, anime_id: str, bolum_indeks: int) -> None:
        """Geçmişi izlenen bölümle güncelle"""
        try:
            if kaynak not in self.gecmis:
                self.gecmis[kaynak] = {}
            
            self.gecmis[kaynak][anime_adi] = {
                "son_bolum_adi": bolum_adi,
                "son_bolum_indeks": bolum_indeks,
                "anime_id": anime_id,
                "son_izlenme": time.time()
            }
            
            self.gecmis_kaydet()
        except Exception as e:
            print(f"Geçmiş güncellenemedi: {e}")

class MPVOynatici:
    """MPV oynatıcı denetleyicisi"""
    
    def __init__(self):
        self.socket_path = f"/tmp/anitr-py-{int(time.time())}.sock"
    
    def yuklu_mu(self) -> bool:
        """MPV'nin yüklü olup olmadığını kontrol et"""
        try:
            subprocess.run(["mpv", "--version"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False
    
    def oynat(self, url: str, altyazi_url: Optional[str], baslik: str) -> subprocess.Popen:
        """Videoyu MPV ile oynat"""
        if not self.yuklu_mu():
            raise Exception("Sisteminizde MPV yüklü değil")
        
        args = [
            "mpv",
            "--fullscreen",
            "--save-position-on-quit",
            f"--title={baslik}",
            f"--force-media-title={baslik}",
            "--idle=once",
            "--really-quiet",
            "--no-terminal",
            f"--input-ipc-server={self.socket_path}",
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/137.0.0.0 Safari/537.36",
            "--referrer=https://yeshi.eu.org/"
        ]
        
        if altyazi_url and altyazi_url.strip():
            args.extend(["--sub-file", altyazi_url])
        
        args.append(url)
        
        return subprocess.Popen(args)

class TUI:
    """Terminal Kullanıcı Arayüzü"""
    
    def __init__(self):
        self.ekran_temizle()
    
    def ekran_temizle(self) -> None:
        """Terminal ekranını temizle"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def yukleniyor_goster(self, mesaj: str) -> None:
        """Yükleniyor mesajını göster"""
        print(f"⏳ {mesaj}")
    
    def yukleniyor_gizle(self) -> None:
        """Yükleniyor mesajını gizle"""
        pass  # Gerçek uygulamada bu mesajı temizlerdi
    
    def hata_goster(self, mesaj: str) -> None:
        """Hata mesajını göster"""
        print(f"❌ Hata: {mesaj}")
    
    def kullanici_girdisi_al(self, prompt: str) -> str:
        """Kullanıcıdan girdi al"""
        return input(f"🔍 {prompt}: ").strip()
    
    def secim_listesi(self, secenekler: List[str], baslik: str) -> str:
        """Seçim listesini göster ve kullanıcı seçimini al"""
        self.ekran_temizle()
        print(f"\n{baslik}\n")
        
        for i, secenek in enumerate(secenekler, 1):
            print(f"  {i}. {secenek}")
        
        print("\n0. Geri dön")
        
        while True:
            try:
                secim = int(input("\nBir seçenek seçin: "))
                if secim == 0:
                    raise KeyboardInterrupt("Kullanıcı iptal etti")
                if 1 <= secim <= len(secenekler):
                    return secenekler[secim - 1]
                else:
                    print("Geçersiz seçim. Lütfen tekrar deneyin.")
            except ValueError:
                print("Lütfen geçerli bir sayı girin.")

class AnimeCLI:
    """Ana CLI uygulaması"""
    
    def __init__(self, rpc_devre_disi: bool = False):
        self.config = Config()
        self.logger = Logger()
        self.gecmis = GecmisYonetici()
        self.anime_kaynak = AnimeCix()
        self.oynatici = MPVOynatici()
        self.tui = TUI()
        self.rpc_devre_disi = rpc_devre_disi or self.config.config.get("rpc_devre_disi", False)
    
    def calistir(self) -> None:
        """Ana uygulama döngüsünü çalıştır"""
        while True:
            try:
                self.ana_menu()
            except KeyboardInterrupt:
                print("\n👋 Görüşürüz!")
                sys.exit(0)
            except Exception as e:
                self.logger.hata_kaydet(e)
                self.tui.hata_goster(str(e))
                input("Devam etmek için Enter'a basın...")
    
    def ana_menu(self) -> None:
        """Ana menüyü göster"""
        secenekler = ["Anime Ara", "Geçmiş", "Çıkış"]
        secim = self.tui.secim_listesi(secenekler, "Ana Menü")
        
        if secim == "Anime Ara":
            self.ara_ve_oynat()
        elif secim == "Geçmiş":
            self.gecmis_goster()
        elif secim == "Çıkış":
            print("👋 Görüşürüz!")
            sys.exit(0)
    
    def ara_ve_oynat(self) -> None:
        """Anime ara ve seçilen bölümü oynat"""
        try:
            # Arama sorgusu al
            sorgu = self.tui.kullanici_girdisi_al("Anime adı girin")
            if not sorgu:
                return
            
            # Yükleniyor göster
            self.tui.yukleniyor_goster("Aranıyor...")
            
            # Anime ara
            arama_sonuclari = self.anime_kaynak.arama_verisi_al(sorgu)
            self.tui.yukleniyor_gizle()
            
            if not arama_sonuclari:
                self.tui.hata_goster("Sonuç bulunamadı")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Anime seç
            anime_basliklari = [anime["baslik"] for anime in arama_sonuclari]
            secilen_baslik = self.tui.secim_listesi(anime_basliklari, "Anime Seçin")
            
            # Seçilen animeyi bul
            secilen_anime = None
            for anime in arama_sonuclari:
                if anime["baslik"] == secilen_baslik:
                    secilen_anime = anime
                    break
            
            if not secilen_anime:
                return
            
            # Anime detaylarını al
            self.tui.yukleniyor_goster("Anime detayları yükleniyor...")
            anime_detaylari = self.anime_kaynak.id_ile_anime_al(str(secilen_anime["id"]))
            
            # Bölümleri al
            bolumler = self.anime_kaynak.bolumler_verisini_al(secilen_anime["id"])
            self.tui.yukleniyor_gizle()
            
            if not bolumler:
                self.tui.hata_goster("Bölüm bulunamadı")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Bölüm seç
            bolum_basliklari = [bolum["baslik"] for bolum in bolumler]
            secilen_bolum_baslik = self.tui.secim_listesi(bolum_basliklari, "Bölüm Seçin")
            
            # Seçilen bölümü bul
            secilen_bolum = None
            secilen_bolum_indeks = -1
            for i, bolum in enumerate(bolumler):
                if bolum["baslik"] == secilen_bolum_baslik:
                    secilen_bolum = bolum
                    secilen_bolum_indeks = i
                    break
            
            if not secilen_bolum:
                return
            
            # Bölümü oynat
            self.bolum_oynat(
                anime_detaylari,
                secilen_bolum,
                secilen_bolum_indeks,
                len(bolumler)
            )
            
        except KeyboardInterrupt:
            return
        except Exception as e:
            self.logger.hata_kaydet(e)
            self.tui.hata_goster(str(e))
            input("Devam etmek için Enter'a basın...")
    
    def bolum_oynat(self, anime: Dict[str, Any], bolum: Dict[str, Any], bolum_indeks: int, toplam_bolumler: int) -> None:
        """Seçilen bölümü oynat"""
        try:
            # Yükleniyor göster
            self.tui.yukleniyor_goster("Oynatılmaya hazırlanıyor...")
            
            # İzleme verisini al
            izleme_verisi = self.anime_kaynak.izleme_verisini_al(bolum["id"])
            
            if not izleme_verisi:
                self.tui.yukleniyor_gizle()
                self.tui.hata_goster("Video kaynağı bulunamadı")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Türkçe altyazıyı al (varsa)
            sezon_num = bolum["ekstra"].get("sezon_num", 1)
            altyazi_url = self.anime_kaynak.tr_altyazi_al(
                sezon_num - 1, 
                bolum_indeks, 
                anime["id"]
            )
            
            # Kaliteye göre sırala (en yüksek önce)
            izleme_verisi.sort(key=lambda x: self._kalite_cikar(x["etiket"]), reverse=True)
            
            # Kalite seç (varsayılan olarak en yüksek)
            secilen_kalite = izleme_verisi[0]
            
            self.tui.yukleniyor_gizle()
            
            # MPV ile oynat
            baslik = f"{anime['baslik']} - {bolum['baslik']}"
            process = self.oynatici.oynat(
                secilen_kalite["url"],
                altyazi_url,
                baslik
            )
            
            # Geçmişi güncelle
            self.gecmis.gecmis_guncelle(
                "animecix",
                anime["baslik"],
                bolum["baslik"],
                str(anime["id"]),
                bolum_indeks
            )
            
            # Oynatımın bitmesini bekle
            process.wait()
            
        except Exception as e:
            self.logger.hata_kaydet(e)
            self.tui.hata_goster(str(e))
            input("Devam etmek için Enter'a basın...")
    
    def gecmis_goster(self) -> None:
        """İzleme geçmişini göster"""
        try:
            kaynak_gecmis = self.gecmis.gecmis.get("animecix", {})
            
            if not kaynak_gecmis:
                self.tui.hata_goster("Geçmiş bulunamadı")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Son izlenme zamanına göre sırala
            sirali_gecmis = sorted(
                kaynak_gecmis.items(),
                key=lambda x: x[1].get("son_izlenme", 0),
                reverse=True
            )
            
            # Limiti uygula (yapılandırıldıysa)
            gecmis_limiti = self.config.config.get("gecmis_limiti", 0)
            if gecmis_limiti > 0:
                sirali_gecmis = sirali_gecmis[:gecmis_limiti]
            
            if not sirali_gecmis:
                self.tui.hata_goster("Geçmiş bulunamadı")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Geçmiş girişlerini biçimlendir
            gecmis_girisleri = []
            for anime_adi, veri in sirali_gecmis:
                son_bolum = veri.get("son_bolum_adi", "Bilinmiyor")
                gecmis_girisleri.append(f"{anime_adi} - {son_bolum}")
            
            # Geçmişten seçim yap
            secilen_giris = self.tui.secim_listesi(gecmis_girisleri, "İzleme Geçmişi")
            
            # Seçilen animeyi geçmişte bul
            secilen_anime_adi = None
            for anime_adi, veri in sirali_gecmis:
                son_bolum = veri.get("son_bolum_adi", "Bilinmiyor")
                if f"{anime_adi} - {son_bolum}" == secilen_giris:
                    secilen_anime_adi = anime_adi
                    break
            
            if not secilen_anime_adi:
                return
            
            # Geçmişten anime detaylarını al
            anime_veri = kaynak_gecmis[secilen_anime_adi]
            anime_id = anime_veri.get("anime_id")
            
            if not anime_id:
                self.tui.hata_goster("Geçersiz geçmiş girişi")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Anime detaylarını yükle
            self.tui.yukleniyor_goster("Anime yükleniyor...")
            anime_detaylari = self.anime_kaynak.id_ile_anime_al(anime_id)
            
            # Bölümleri al
            bolumler = self.anime_kaynak.bolumler_verisini_al(int(anime_id))
            self.tui.yukleniyor_gizle()
            
            if not bolumler:
                self.tui.hata_goster("Bölüm bulunamadı")
                input("Devam etmek için Enter'a basın...")
                return
            
            # Bölüm seç
            bolum_basliklari = [bolum["baslik"] for bolum in bolumler]
            secilen_bolum_baslik = self.tui.secim_listesi(bolum_basliklari, "Bölüm Seçin")
            
            # Seçilen bölümü bul
            secilen_bolum = None
            secilen_bolum_indeks = -1
            for i, bolum in enumerate(bolumler):
                if bolum["baslik"] == secilen_bolum_baslik:
                    secilen_bolum = bolum
                    secilen_bolum_indeks = i
                    break
            
            if not secilen_bolum:
                return
            
            # Bölümü oynat
            self.bolum_oynat(
                anime_detaylari,
                secilen_bolum,
                secilen_bolum_indeks,
                len(bolumler)
            )
            
        except KeyboardInterrupt:
            return
        except Exception as e:
            self.logger.hata_kaydet(e)
            self.tui.hata_goster(str(e))
            input("Devam etmek için Enter'a basın...")
    
    def _kalite_cikar(self, etiket: str) -> int:
        """Etiketten kalite numarasını çıkar (örn: '1080p' -> 1080)"""
        try:
            # 'p'yi kaldır ve int'e çevir
            return int(etiket.rstrip('p'))
        except ValueError:
            return 0

def main():
    """Ana giriş noktası"""
    parser = argparse.ArgumentParser(description="Terminalde Türkçe altyazılı anime arama ve izleme aracı")
    parser.add_argument("--rpc-devre-disi", action="store_true", help="Discord Rich Presence özelliğini kapatır")
    parser.add_argument("--surum", "-v", action="version", version="anitr-py 1.0.0")
    
    args = parser.parse_args()
    
    # CLI uygulamasını oluştur ve çalıştır
    cli = AnimeCLI(rpc_devre_disi=args.rpc_devre_disi)
    cli.calistir()

if __name__ == "__main__":
    main()