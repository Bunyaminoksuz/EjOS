#!/bin/bash
# Dosya: 01_Lenovo-Ollama-Server/setup-ollama.sh
# Açıklama: Lenovo sunucusunda gerekli tüm bağımlılıkları (Ollama, htop, sensors) kurar ve ejos-ai modelini hazırlar.
# KULLANMADAN ÖNCE MUTLAKA CHMOD YAPIMIZ!!! chmod +x setup-ollama.sh
# --- 1. SİSTEM GÜNCELLEME VE TEMEL ARAÇLARI KURMA ---
echo "--- 1/4: Temel Sistem Güncelleme ve İzleme Araçları Kurulumu ---"
sudo apt update
sudo apt upgrade -y

# İzleme ve Yönetim Araçları: htop (süreç izleme) ve lm-sensors (sıcaklık izleme)
sudo apt install htop lm-sensors -y

# Sensors ayarlarını yap (Gerekirse)
echo "Sıcaklık sensörlerini otomatik algılama başlatılıyor (sensors-detect)..."
sudo sensors-detect --auto
echo "Sensör bilgileri: "
sensors

# --- 2. OLLAMA KURULUMU ---
echo "--- 2/4: Ollama Kurulumu ---"

# Resmi Ollama kurulum komutu
curl -fsSL https://ollama.com/install.sh | sh

if [ $? -ne 0 ]; then
    echo "HATA: Ollama kurulumu başarısız oldu. Lütfen internet bağlantınızı kontrol edin."
    exit 1
fi
echo "Ollama başarıyla kuruldu."

# --- 3. MODELİ ÇEKME VE ÖZELLEŞTİRME (ejos-ai) ---
echo "--- 3/4: ejos-ai Modelinin Hazırlanması ---"

# Önce temel llama3 modelini çekelim
ollama pull llama3:8b

# Modelfile kullanarak özel ejos-ai modelini oluşturalım.
# Modelfile'ın bu script ile aynı klasörde olması gerekir.
if [ -f "Modelfile" ]; then
    echo "Modelfile bulundu. ejos-ai modeli oluşturuluyor..."
    # Eğer model adınız "ejos-v1-llama3" ise, Modelfile içinde FROM llama3:8b yazısı olmalıdır.
    ollama create ejos-ai -f Modelfile
    
    if [ $? -ne 0 ]; then
        echo "HATA: ejos-ai modeli oluşturulamadı. Modelfile içeriğini kontrol edin."
    else
        echo "ejos-ai modeli başarıyla oluşturuldu."
    fi
else
    echo "UYARI: Modelfile bulunamadı. Sadece temel llama3 modeli kullanılabilir."
fi

# --- 4. OLLAMA'YI BAŞLATMA ---
echo "--- 4/4: Ollama Sunucusu Başlatılıyor ---"

# Ollama genellikle systemd servisi olarak kurulur ve otomatik başlar.
# Ancak bazen yeniden başlatmak gerekir.
sudo systemctl restart ollama
sudo systemctl status ollama

echo "--- KURULUM TAMAMLANDI ---"
echo "Ollama sunucusu artık 'ejos-ai' modelini dinliyor olmalıdır."
echo "Durum kontrolü için: 'sudo systemctl status ollama'"
echo "Çalışan süreçleri izlemek için: 'htop'"
echo "Sıcaklıkları izlemek için: 'watch -n 2 sensors'"