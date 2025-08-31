# anitr-py için Makefile

.PHONY: kur bagimliliklar temizle

# Uygulamayı kur
kur: bagimliliklar
	python3 setup.py

# Bağımlılıkları yükle
bagimliliklar:
	pip install -r requirements.txt

# Derleme artıklarını temizle
temizle:
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Uygulamayı doğrudan çalıştır
calistir:
	python3 main.py

# Geliştirme modunda kur (sembolik bağlantı oluşturur)
gelistir-kur: bagimliliklar
	chmod +x main.py
	sudo ln -sf $(PWD)/main.py /usr/local/bin/anitr-py

# Kaldır
kaldir:
	sudo rm -f /usr/local/bin/anitr-py
	rm -rf ~/.anitr-py