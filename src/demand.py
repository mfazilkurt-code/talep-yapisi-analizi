"""Satış verisi okuma, kontrol ve SBC tipi ADI–CV² talep sınıflandırması.

Bu modülde herhangi bir tahmin veya model eğitimi yapılmaz.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
import re
import unicodedata

import numpy as np
import pandas as pd

ADI_LIMIT = 1.32
CV2_LIMIT = 0.49


class DataValidationError(ValueError):
    """Kullanıcı tarafından düzeltilebilir girdi hatası."""


def _normalize(value: object) -> str:
    text = str(value).strip().replace('İ', 'I').replace('ı', 'i')
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '', text.lower())


def _month_col_name(value: object) -> pd.Timestamp | None:
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(value).to_period('M').to_timestamp()
    s = str(value).strip()
    if re.fullmatch(r'20\d{2}[-./](0?[1-9]|1[0-2])', s):
        return pd.to_datetime(s.replace('.', '-').replace('/', '-') + ('-01' if len(s.split('-')) == 2 else ''), errors='coerce')
    if re.fullmatch(r'20\d{2}[-./](0?[1-9]|1[0-2])[-./]\d{1,2}(?:\s+.*)?', s):
        ts = pd.to_datetime(s, errors='coerce')
        return ts.to_period('M').to_timestamp() if pd.notna(ts) else None
    return None


def _parse_sales(value: object) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, str):
        s = value.strip().replace('\u00a0', '').replace(' ', '')
        if not s:
            return 0.0
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
        elif ',' in s:
            s = s.replace(',', '.')
        try:
            v = float(s)
        except ValueError as exc:
            raise ValueError(f'geçersiz satış: {value!r}') from exc
    else:
        try:
            v = float(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'geçersiz satış: {value!r}') from exc
    if not np.isfinite(v):
        raise ValueError('sonlu olmayan satış')
    if v < 0:
        raise ValueError(f'negatif satış: {v:g}')
    return v


def _parse_month(value: object) -> pd.Timestamp:
    if pd.isna(value) or str(value).strip() == '':
        raise ValueError('eksik ay')
    if isinstance(value, (datetime, date, pd.Timestamp)):
        ts = pd.Timestamp(value)
    else:
        s = str(value).strip()
        if re.fullmatch(r'\d{4}[-./]\d{1,2}', s):
            a, b = re.split(r'[-./]', s)
            s = f'{a}-{int(b):02d}-01'
        try:
            ts = pd.Timestamp(pd.to_datetime(s, errors='raise', dayfirst=False))
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError(f'geçersiz ay: {value!r}') from exc
    if pd.isna(ts):
        raise ValueError('geçersiz ay')
    return ts.to_period('M').to_timestamp()


def _column_role(columns: list[object], options: set[str]) -> object | None:
    for col in columns:
        if _normalize(col) in options:
            return col
    return None


def read_sales_file(uploaded, filename: str, fill_missing_months: bool = False) -> tuple[pd.DataFrame, dict]:
    """Uzun (Malzeme Kodu, Ay, Satis) veya geniş (ay sütunları) Excel/CSV.

    Boş satış hücreleri=0. Kayıp ay satırları varsayılan olarak HATA.
    """
    ext = filename.lower().rsplit('.', 1)[-1]
    try:
        if hasattr(uploaded, 'seek'):
            uploaded.seek(0)
        if ext in ('xlsx', 'xls'):
            raw = pd.read_excel(uploaded, sheet_name=0, dtype=object)
        elif ext == 'csv':
            if hasattr(uploaded, 'seek'):
                uploaded.seek(0)
            raw = pd.read_csv(uploaded, sep=None, engine='python', dtype=object, encoding='utf-8-sig')
        else:
            raise DataValidationError('Yalnızca .xlsx, .xls ve .csv dosyaları destekleniyor.')
    except DataValidationError:
        raise
    except Exception as exc:
        raise DataValidationError(f'Dosya okunamadı: {exc}') from exc
    if raw.empty:
        raise DataValidationError('Dosya boş.')

    columns = list(raw.columns)
    sku_col = _column_role(columns, {'malzemekodu', 'malzeme', 'urunkodu', 'urun', 'sku', 'product', 'productcode', 'material', 'materialcode', 'stok_kodu', 'stokkodu'})
    ay_col = _column_role(columns, {'ay', 'tarih', 'date', 'month', 'donem', 'period'})
    sale_col = _column_role(columns, {'satis', 'satismiktari', 'sales', 'demand', 'talep', 'miktar', 'quantity', 'qty', 'adetsatis'})
    if sku_col is None:
        raise DataValidationError("'Malzeme Kodu' veya 'Malzeme' sütunu bulunamadı.")
    if ay_col is not None and sale_col is not None:
        rows = raw[[sku_col, ay_col, sale_col]].copy()
        rows.columns = ['Malzeme', 'Ay', 'Satis']
        rows['_Satir'] = np.arange(len(rows)) + 2
        mode = 'uzun'
    else:
        month_columns = [(c, _month_col_name(c)) for c in columns if c != sku_col]
        month_columns = [(c, m) for c, m in month_columns if m is not None and pd.notna(m)]
        if not month_columns:
            raise DataValidationError("'Ay' + 'Satis' sütunları veya YYYY-MM biçiminde aylık sütunlar gerekli.")
        rows = raw.melt(id_vars=[sku_col], value_vars=[c for c, _ in month_columns],
                        var_name='_AyBasligi', value_name='Satis')
        rows['Ay'] = rows['_AyBasligi'].map(dict(month_columns))
        rows.rename(columns={sku_col: 'Malzeme'}, inplace=True)
        rows['_Satir'] = 'geniş format'
        rows = rows[['Malzeme', 'Ay', 'Satis', '_Satir']]
        mode = 'geniş'

    cleaned = []
    errors = []
    blanks = 0
    for r in rows.itertuples(index=False):
        sku, ay, sales, row = r
        key = str(sku).strip() if pd.notna(sku) else ''
        if not key or key.lower() == 'nan':
            errors.append(f'Satır {row}: boş malzeme kodu')
            continue
        try:
            month = _parse_month(ay)
            value = _parse_sales(sales)
        except ValueError as exc:
            errors.append(f'Satır {row}, malzeme {key}, ay {ay}: {exc}')
            continue
        if pd.isna(sales) or (isinstance(sales, str) and not sales.strip()):
            blanks += 1
        cleaned.append((key, month, value))
    if errors:
        raise DataValidationError(f'{len(errors)} sorunlu hücre/satır bulundu:\n' + '\n'.join(errors[:12]) +
                                  ('\n…' if len(errors) > 12 else ''))
    df = pd.DataFrame(cleaned, columns=['Malzeme', 'Ay', 'Satis'])
    if df.empty:
        raise DataValidationError('Kullanılabilir satış verisi yok.')
    duplicates = df.duplicated(['Malzeme', 'Ay'], keep=False)
    if duplicates.any():
        cases = df.loc[duplicates, ['Malzeme', 'Ay']].head(8)
        msg = ', '.join(f"{r.Malzeme} ({r.Ay:%Y-%m})" for r in cases.itertuples())
        raise DataValidationError(f'Aynı malzeme-ay birden fazla kez bulunuyor: {msg}. Önce kayıtları birleştirin.')
    df = df.sort_values(['Malzeme','Ay']).reset_index(drop=True)
    gaps = []
    filled_count = 0
    chunks = []
    for sku, gr in df.groupby('Malzeme', sort=True):
        dates = pd.date_range(gr['Ay'].min(), gr['Ay'].max(), freq='MS')
        missing = dates.difference(pd.DatetimeIndex(gr['Ay']))
        if len(missing):
            gaps.extend((sku, d.strftime('%Y-%m')) for d in missing)
        if len(missing) and fill_missing_months:
            gr = gr.set_index('Ay').reindex(dates).rename_axis('Ay').reset_index()
            gr['Malzeme'] = sku
            gr['Satis'] = gr['Satis'].fillna(0.0)
            filled_count += len(missing)
        chunks.append(gr[['Malzeme','Ay','Satis']])
    if gaps and not fill_missing_months:
        detail = '; '.join(f'{k} {d}' for k, d in gaps[:9])
        raise DataValidationError(f'{len(gaps)} eksik ay satırı var: {detail}. '
                                  'Eksik ay satırı, boş satış hücresi değildir. '
                                  'Gerçekten 0 kabul edecekseniz yan menüdeki seçeneği açın.')
    data = pd.concat(chunks, ignore_index=True).sort_values(['Malzeme','Ay']).reset_index(drop=True)
    return data, {'format': mode, 'bos_hucre': blanks, 'eklenen_ay': filled_count, 'urun': data['Malzeme'].nunique(), 'gozlem': len(data)}


@dataclass(frozen=True)
class DemandStats:
    malzeme: str
    sinif: str
    adi: float | None
    cv2: float | None
    ay: int
    pozitif_ay: int
    sifir_ay: int
    satis_toplam: float
    pozitif_ortalama: float | None
    guven: str


def classify_group(group: pd.DataFrame, sku: str) -> DemandStats:
    v = group.sort_values('Ay')['Satis'].to_numpy(dtype=float)
    if not len(v) or np.any(v < 0) or not np.all(np.isfinite(v)):
        raise ValueError('Satış değerleri sonlu ve negatif olmayan sayılar olmalıdır.')
    positive = v[v > 0]
    n, k = len(v), len(positive)
    if k == 0:
        return DemandStats(sku, 'Talep yok', None, None, n, 0, n, 0.0, None, 'Tanımlanamaz')
    adi = float(n / k)
    mean = float(positive.mean())
    if k < 2:
        return DemandStats(sku, 'Yetersiz pozitif veri', adi, None, n, k, n-k, float(v.sum()), mean, 'Tanımlanamaz')
    # ddof=0: mevcut pozitif satışların betimsel/popülasyon varyansı.
    cv2 = float(np.mean((positive - mean)**2) / (mean**2))
    if adi < ADI_LIMIT:
        demand_type = 'Smooth' if cv2 < CV2_LIMIT else 'Erratic'
    else:
        demand_type = 'Intermittent' if cv2 < CV2_LIMIT else 'Lumpy'
    confidence = 'Sınırlı gözlem' if (n < 24 or k < 6) else 'Betimsel sınıflandırma'
    return DemandStats(sku, demand_type, adi, cv2, n, k, n-k, float(v.sum()), mean, confidence)


def classify_all(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for sku, group in df.groupby('Malzeme', sort=True):
        s = classify_group(group, str(sku))
        out.append({'Malzeme': s.malzeme, 'Talep sınıfı': s.sinif,
                    'ADI': s.adi, 'CV²': s.cv2, 'Ay sayısı': s.ay,
                    'Pozitif ay': s.pozitif_ay, 'Sıfır ay': s.sifir_ay,
                    'Sıfır oranı (%)': round(100 * s.sifir_ay / s.ay, 2),
                    'Toplam satış': s.satis_toplam, 'Pozitif ay ortalaması': s.pozitif_ortalama,
                    'Değerlendirme': s.guven})
    return pd.DataFrame(out)
