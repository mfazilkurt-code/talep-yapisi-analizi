# Talep Yapısı Analizi

Excel veya CSV satış verileri üzerinden malzeme bazında ADI–CV² sınıflandırması yapan, etkileşimli grafikler ve incelenebilecek tahmin modelleri sunan Streamlit uygulaması. **Tahmin üretmez.**

## Kurulum — Windows / VS Code

1. ZIP dosyasını ayıklayın. VS Code'da **File → Open Folder** menüsünden doğrudan `Talep_Yapisi_Sade` klasörünü açın.
2. `Terminal → New Terminal` açın.
3. Sırayla aşağıdaki komutları çalıştırın:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

`py` komutunun Windows'ta bulunması gerekmez. `requirements.txt` görülemiyorsa terminalin `app.py` bulunan klasörde olduğundan emin olun. Sanal ortam kurmak istemiyorsanız:

```powershell
python -m pip install "streamlit>=1.40,<2" "pandas>=2.1,<3" "numpy>=1.26,<3" "plotly>=5.20,<7" "openpyxl>=3.1,<4"
python -m streamlit run app.py
```

Yerel erişim: `http://localhost:8501`. Durdurmak için terminalde `Ctrl + C`.

## Grafikler

- Aylık satış (çizgi/sütun; çizgi görünümünde yumuşak geçiş)
- Mevsimsel dağılım (aylara göre kutu grafiği)
- Yıllık toplam (yıllık sütun grafiği)
- ADI–CV² sınıflandırma haritası

Grafiklerde fareyle değer görüntüleme ve yakınlaştırma bulunur.

## Veri ve yorum

İki dosya düzeni desteklenir: `Malzeme Kodu, Ay, Satis` ve `Malzeme Kodu, 2024-01, 2024-02, ...`. Mevcut satırdaki boş satış hücresi 0 olur; tamamen bulunmayan ay satırları, seçilmedikçe tamamlanmaz. Negatif değerlerde işlem durdurulur.

Eşikler ADI 1,32 ve CV² 0,49. Pozitif satış yoksa veya yalnızca bir ayda varsa dört sınıflı etiket zorlanmaz. Model seçenekleri araştırma adaylarıdır, tahmin başarısı sonucuna dayanmaz.

## GitHub ve Streamlit Community Cloud

Deponun kök dizininde aşağıdaki yapı bulunmalıdır:

```text
app.py
requirements.txt
src/
  __init__.py
  demand.py
  recommendations.py
  graphics.py
data/
  ornek_satis.csv
.streamlit/
  config.toml
README.md
```

GitHub'da yeni bir depo açıp bu dosyaları ve klasörleri **iç yapılarıyla** yükleyin. `https://share.streamlit.io/` üzerinden depo ve `main` dalını seçin; ana dosya yolu `app.py` olacaktır. Gerçek şirket verilerini herkese açık depoya koymayın.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
