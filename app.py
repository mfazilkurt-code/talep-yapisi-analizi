"""Talep yapısı inceleme: sınıflandırma, satış grafikleri ve model seçenekleri."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.demand import (
    ADI_LIMIT, CV2_LIMIT, DataValidationError, classify_all, read_sales_file,
)
from src.graphics import category_map, monthly_distribution, sales_series, yearly_totals
from src.recommendations import CLASS_DESCRIPTIONS, POOLS, REFERENCES

PROJECT_DIR = Path(__file__).resolve().parent
st.set_page_config(
    page_title='Talep Yapısı Analizi', page_icon='◉',
    layout='wide', initial_sidebar_state='expanded',
)

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
:root {--ink:#f8edf2;--mute:#c5acb7;--border:#44303b;--card:#241b22;--accent:#efaab9}
html,body,.stApp,button,input,textarea,select,
[data-testid="stMarkdownContainer"], [data-testid="stMetric"],
[data-baseweb="tab"], [data-baseweb="select"] {
  font-family:'Manrope','Trebuchet MS',Arial,sans-serif!important;
}
.stApp {
  color:var(--ink);
  background:radial-gradient(ellipse 75% 42% at 95% 0%,rgba(132,48,69,.17),transparent 68%),
             linear-gradient(175deg,#20171d 0%,#171217 42%,#171217 100%);
}
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#271b24,#1e171e 75%)!important;
  border-right:1px solid var(--border);
}
[data-testid="stMainBlockContainer"] {
  max-width:1500px!important;
  padding-top:1.15rem!important;
  padding-bottom:2.4rem!important;
}
[data-testid="stVerticalBlock"] {gap:.7rem!important}
h1,h2,h3 {font-weight:800!important;letter-spacing:-.033em!important;color:var(--ink)!important}
h1 {font-size:1.7rem!important;line-height:1.25!important;margin:.15rem 0 .22rem!important}
h2 {font-size:1.12rem!important;margin:.2rem 0!important}
h3 {font-size:1.01rem!important}
[data-testid="stMarkdownContainer"] p {line-height:1.58}
[data-testid="stMetric"] {
  border:1px solid var(--border);background:rgba(45,31,41,.7);
  border-radius:12px;padding:.72rem .95rem!important;min-height:83px;
}
[data-testid="stMetricLabel"] {font-size:.74rem!important;color:var(--mute)!important}
[data-testid="stMetricValue"] {font-size:1.17rem!important;font-weight:800!important;color:var(--ink)!important}
[data-testid="stTabs"] [data-baseweb="tab"] {
  font-weight:700!important;font-size:.86rem!important;padding:.55rem .82rem!important;
}
[data-testid="stTabs"] [aria-selected="true"] {color:var(--accent)!important}
[data-testid="stPlotlyChart"] {
  border:1px solid var(--border);background:#171217;
  border-radius:15px;overflow:hidden;
}
[data-testid="stExpander"],div[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color:var(--border)!important;border-radius:12px!important;
}
[data-testid="stAlert"] {border-radius:12px!important}
.st-key-short-table {opacity:.98}
.section-label {color:var(--mute);font-size:.79rem;font-weight:600;margin-bottom:.4rem}
.subtitle {color:var(--mute);font-size:.86rem;margin:.05rem 0 .95rem}
.headline-rule {height:2px;width:49px;border-radius:3px;
  background:linear-gradient(90deg,#df819d,#dfb9be);margin:.55rem 0 .7rem}
.endnote {color:var(--mute);font-size:.75rem;margin-top:1.2rem}
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
  border-color:var(--border)!important;
}
</style>
''', unsafe_allow_html=True)


def fmt(value, digits=2):
    if value is None or pd.isna(value):
        return '—'
    return f'{value:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


with st.sidebar:
    st.markdown('### Veri Seçimi')
    uploaded = st.file_uploader('Satış dosyası', type=['xlsx', 'xls', 'csv'])
    with st.expander('Dosya seçenekleri', expanded=False):
        fill_missing = st.checkbox(
            'Eksik ayları sıfırla', value=False,
            help='Satırı mevcut olup satış hücresi boş olan değerler zaten 0 kabul edilir. '
                 'Bu seçim, veri içinde hiç bulunmayan ay satırlarını da ekler.',
        )
    st.caption('Boş satış hücresi = 0. Negatif satışlar kabul edilmez.')

try:
    if uploaded is None:
        source = PROJECT_DIR / 'data' / 'ornek_satis.csv'
        with source.open('rb') as f:
            sales, file_info = read_sales_file(f, source.name, fill_missing_months=fill_missing)
        is_sample = True
    else:
        sales, file_info = read_sales_file(
            uploaded, uploaded.name, fill_missing_months=fill_missing,
        )
        is_sample = False
except DataValidationError as exc:
    st.error('Dosya kontrolünde sorun bulundu.')
    st.code(str(exc))
    st.stop()

summary = classify_all(sales)
with st.sidebar:
    selected_sku = st.selectbox('Malzeme', summary['Malzeme'].to_list())
    st.caption(f'{file_info["urun"]} malzeme · {file_info["gozlem"]} aylık kayıt')
    if is_sample:
        st.caption('Örnek veri gösteriliyor.')

selected_sales = sales.loc[sales['Malzeme'] == selected_sku].sort_values('Ay')
selected_summary = summary.loc[summary['Malzeme'] == selected_sku].iloc[0]
selected_class = str(selected_summary['Talep sınıfı'])

st.title('Talep Yapısı Analizi')
st.markdown('<div class="subtitle">Satış hareketleri ve talep sınıfları</div>', unsafe_allow_html=True)
st.markdown('<div class="headline-rule"></div>', unsafe_allow_html=True)

if file_info['bos_hucre'] or file_info['eklenen_ay']:
    st.caption(
        f'İçe aktarma: {file_info["bos_hucre"]} boş satış hücresi, '
        f'{file_info["eklenen_ay"]} tamamlanan ay.'
    )

kpi = st.columns(5, gap='small')
kpi[0].metric('Malzeme', selected_sku)
kpi[1].metric('Talep sınıfı', selected_class)
kpi[2].metric('ADI', fmt(selected_summary['ADI'], 3))
kpi[3].metric('CV²', fmt(selected_summary['CV²'], 3))
kpi[4].metric('Sıfır ay', f'{fmt(selected_summary["Sıfır oranı (%)"], 1)}%')

st.markdown(
    '<div class="section-label">'+CLASS_DESCRIPTIONS.get(selected_class, '')+'</div>',
    unsafe_allow_html=True,
)

tab_graph, tab_map, tab_models, tab_data = st.tabs([
    'Satış Grafikleri', 'Talep Sınıfları', 'Model Seçenekleri', 'Veri ve Hesaplama',
])

PLOT_CONFIG = {'displaylogo': False, 'scrollZoom': True, 'responsive': True}

with tab_graph:
    col_graph, col_options = st.columns([3.25, 1.0], gap='large')
    with col_graph:
        view = st.radio(
            'Görünüm', ['Aylık satış', 'Mevsimsel dağılım', 'Yıllık toplam'],
            horizontal=True, label_visibility='collapsed',
        )
    with col_options:
        if view == 'Aylık satış':
            series_type = st.selectbox('Grafik türü', ['Çizgi', 'Sütun'], label_visibility='collapsed')
        else:
            series_type = 'Çizgi'
    if view == 'Aylık satış':
        if series_type == 'Çizgi':
            smooth = st.toggle('Yumuşak çizgi', value=True)
        else:
            smooth = False
        plot = sales_series(selected_sales, series_type, smooth)
    elif view == 'Mevsimsel dağılım':
        plot = monthly_distribution(selected_sales)
    else:
        plot = yearly_totals(selected_sales)

    st.plotly_chart(plot, use_container_width=True, config=PLOT_CONFIG)
    notes = {
        'Aylık satış': 'Grafik üzerinde gezerek ay ve satış değerini görebilir, yakınlaştırabilirsiniz.',
        'Mevsimsel dağılım': 'Aynı takvim ayının farklı yıllardaki satış dağılımı. '
                               'Görünen desen tek başına mevsimsellik kanıtı değildir.',
        'Yıllık toplam': 'Eksik takvim yılı ile tam yıl aynı kapsamda değildir. '
                        'Fareyi sütuna getirerek kayıtlı ay sayısını kontrol edin.',
    }
    st.caption(notes[view])
    with st.expander('Aylık satış tablosu', expanded=False):
        table = selected_sales.copy()
        table['Ay'] = table['Ay'].dt.strftime('%Y-%m')
        st.dataframe(table.rename(columns={'Satis': 'Satış'}),
                     use_container_width=True, hide_index=True, height=300)

with tab_map:
    st.plotly_chart(category_map(summary, selected_sku),
                    use_container_width=True, config=PLOT_CONFIG)
    st.caption(
        'Kesikli çizgiler: ADI = 1,32 ve CV² = 0,49. '
        'En az iki pozitif satış ayı bulunmayan ürünler haritada yer almaz.'
    )
    with st.expander('Tüm malzemeler', expanded=False):
        st.dataframe(summary, use_container_width=True, hide_index=True, height=340)
        st.download_button(
            'CSV indir', summary.to_csv(index=False).encode('utf-8-sig'),
            file_name='talep_siniflari.csv', mime='text/csv',
        )

with tab_models:
    st.subheader(f'{selected_class} · İncelenebilecek modeller')
    models = POOLS.get(selected_class, [])
    if not models:
        st.info('Bu talep yapısında model önerisi için yeterli bilgi bulunmuyor.')
    for idx, (model, rationale, _) in enumerate(models, 1):
        with st.container(border=True):
            c1, c2 = st.columns([1.55, 3.4], gap='medium')
            with c1:
                st.markdown(f'**{idx:02d} / {model}**')
            with c2:
                st.write(rationale)
    st.caption('Bu liste bir model sıralaması değildir. Tahmin başarısı ayrı bir testle ölçülmelidir.')

with tab_data:
    with st.expander('Sınıflandırma hesapları', expanded=True):
        st.latex(r'ADI=\frac{N}{N_+}')
        st.latex(r'CV^2=\frac{\frac{1}{N_+}\sum_{i=1}^{N_+}(z_i-\bar z)^2}{\bar z^2}')
        st.write('N: toplam ay sayısı. N₊: pozitif satış bulunan ay sayısı. '
                 'zᵢ: pozitif aydaki satış. CV², pozitif satışların betimsel varyansıyla hesaplanır.')
        st.write(f'Sınıf eşikleri: ADI = {str(ADI_LIMIT).replace(".", ",")}; '
                 f'CV² = {str(CV2_LIMIT).replace(".", ",")}. '
                 'Eşiklerin altı düşük, eşit ve üstü yüksek kabul edilir.')
        st.write('Tamamı sıfır olan serilerde ADI ve CV²; yalnızca bir pozitif satış ayı bulunan '
                 'serilerde CV² üzerinden dört sınıflı değerlendirme yapılmaz.')
    with st.expander('Dosya düzeni', expanded=False):
        st.code(
            'Uzun biçim:\nMalzeme Kodu,Ay,Satis\nP-101,2024-01,18\nP-101,2024-02,0\n\n'
            'Geniş biçim:\nMalzeme Kodu,2024-01,2024-02\nP-101,18,0',
            language='text',
        )
        st.write('Boş satış hücreleri 0 kabul edilir. '
                 'Tamamen eksik ay satırları varsayılan olarak eklenmez. '
                 'Negatif satış miktarları ayrıca kontrol edilmelidir.')
    with st.expander('İlgili yayınlar', expanded=False):
        for reference in REFERENCES.values():
            st.markdown(f"[{reference['name']}]({reference['url']})")

st.markdown('<div class="endnote">Talep Yapısı Analizi</div>', unsafe_allow_html=True)
