"""Talep türlerine göre denenebilecek tahmin yöntemleri."""
from __future__ import annotations

REFERENCES = {
    'SBC2005': {
        'name': 'Syntetos, Boylan & Croston (2005) — On the categorization of demand patterns',
        'url': 'https://doi.org/10.1057/palgrave.jors.2601841',
        'note': 'ADI–CV² sınıflandırması ve Croston/SBA/üstel düzeltme karşılaştırması.'
    },
    'BS6': {
        'name': 'Boylan & Syntetos (2021), Intermittent Demand Forecasting — Bölüm 6',
        'url': 'https://doi.org/10.1002/9781119135289.ch6',
        'note': 'SES, Croston, SBA ve zamansal toplulaştırma.'
    },
    'BS11': {
        'name': 'Boylan & Syntetos (2021) — Bölüm 11: Classification Methods',
        'url': 'https://doi.org/10.1002/9781119135289.ch11',
        'note': 'Sınıflandırmanın amaca bağlı olması ve sınırların dikkatle yorumlanması.'
    },
    'TSB2011': {
        'name': 'Teunter, Syntetos & Babai (2011) — Intermittent demand: Linking forecasting to inventory obsolescence',
        'url': 'https://doi.org/10.1016/j.ejor.2011.05.018',
        'note': 'Talep oluşum olasılığına dayalı TSB ve eskime riski.'
    },
    'ADIDA2011': {
        'name': 'Nikolopoulos vd. (2011) — ADIDA',
        'url': 'https://doi.org/10.1057/jors.2010.32',
        'note': 'Zamansal toplulaştırma ile aralıklı talep tahmini.'
    },
    'PK2015': {
        'name': 'Petropoulos & Kourentzes (2015) — Forecast combinations for intermittent demand',
        'url': 'https://doi.org/10.1057/jors.2014.62',
        'note': 'Yöntem ve zaman düzeyleri arasında tahmin kombinasyonu.'
    },
    'PINCE2021': {
        'name': 'Pinçe, Turrini & Meissner (2021) — A Critical Review',
        'url': 'https://doi.org/10.1016/j.omega.2021.102513',
        'note': 'Yöntemlerin koşullara ve ölçütlere göre değişen üstünlükleri.'
    },
}

# Kategoriler, karşılaştırmalı analiz için başlangıç model seçeneklerini belirler.
POOLS = {
    'Smooth': [
        ('SES (Tek Üstel Düzeltme)', 'Daha düzenli satışta seviyeyi izlemek için yalın başlangıç modeli.', ['BS6', 'SBC2005']),
        ('Croston (karşılaştırma)', 'Özgün SBC sınıflandırmasındaki karşılaştırma yöntemlerinden biridir; bu sınıfta da benchmark olabilir.', ['SBC2005', 'BS6']),
        ('Holt / ETS', 'Trend gözlenirse seviyeye ek olarak trend bileşenini sınamak için.', ['PINCE2021']),
        ('Mevsimsel Naive / ETS', 'En az iki yıl veri ve açık mevsimsellik varsa ek aday; sınıf etiketi tek başına mevsimsellik kanıtı değildir.', ['PINCE2021']),
    ],
    'Erratic': [
        ('SBA', 'SBC çalışmasındaki Croston yanlılık düzeltmesi, yüksek büyüklük değişkenliğinde karşılaştırılabilir.', ['SBC2005','BS6']),
        ('SES / ETS', 'Sık gelen fakat büyüklüğü oynak talepte seviyeyi veya trendi sınamak için.', ['BS6','PINCE2021']),
        ('Naive / hareketli ortalama', 'Basit referanslarla kıyaslama; güçlü sonuç varsayılmaz.', ['SBC2005','PINCE2021']),
        ('Zamansal kombinasyon', 'Tek model seçimine bağımlılığı azaltmak için araştırılabilecek ek aday.', ['PK2015']),
    ],
    'Intermittent': [
        ('SBA', 'Croston tahminindeki yanlılığı azaltan uzmanlaşmış yaklaşım.', ['SBC2005','BS6']),
        ('Croston', 'Pozitif satış büyüklüğü ve satış aralıklarını ayrı izleyen klasik yöntem.', ['BS6']),
        ('TSB', 'Talebin gerçekleşme olasılığını izler; talebin sönümlenmesi olasılığında değerlidir.', ['TSB2011']),
        ('ADIDA', 'Talebi daha geniş zaman dilimlerinde toplulaştırarak sıfırların etkisini incelemek için.', ['ADIDA2011', 'BS6']),
        ('Forecast combination', 'Yöntem/zaman toplulaştırma seviyelerini birleştirmek için araştırma adayı.', ['PK2015']),
    ],
    'Lumpy': [
        ('SBA', 'Seyrek geliş ve yüksek büyüklük değişkenliği için temel uzmanlaşmış benchmark.', ['SBC2005','BS6']),
        ('TSB', 'Düşen talep gerçekleşme olasılığını ve eskime riskini incelemek için.', ['TSB2011']),
        ('ADIDA', 'Seyrek ve oynak satışları farklı zaman ölçeklerinde analiz etmek için.', ['ADIDA2011']),
        ('Forecast combination', 'Tek bir yöntem yerine alternatif toplulaştırma ve yöntemleri deneyerek kıyaslamak için.', ['PK2015']),
    ],
    'Talep yok': [],
    'Yetersiz pozitif veri': [
        ('Ek veri / uzman görüşü', 'Bir pozitif satış gözlemi CV² hesaplamaya yetmez; önce veri kapsamı genişletilmeli.', ['BS11']),
    ],
}

CLASS_DESCRIPTIONS = {
    'Smooth': 'Talep sık oluşuyor ve pozitif satış büyüklükleri göreli olarak düzenli.',
    'Erratic': 'Talep sık oluşuyor; gerçekleşen satış miktarları belirgin dalgalanıyor.',
    'Intermittent': 'Sıfır aylar görece sık; pozitif satış büyüklükleri daha düzenli.',
    'Lumpy': 'Sıfır aylar görece sık ve pozitif satış miktarları yüksek değişkenlik gösteriyor.',
    'Talep yok': 'İncelenen bütün aylarda satış sıfır. ADI ve CV² hesaplanamaz.',
    'Yetersiz pozitif veri': 'Pozitif satış tek bir ayda var. CV² güvenilir biçimde hesaplanamaz.',
}
