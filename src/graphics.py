"""Plotly görünümleri: satış serisi, aylık dağılım, yıllık toplam, ADI–CV²."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .demand import ADI_LIMIT, CV2_LIMIT

THEME = {
    'bg': '#171217',
    'panel': '#241b22',
    'border': '#44303b',
    'text': '#f8edf2',
    'muted': '#c5acb7',
    'primary': '#efaab9',
    'secondary': '#dab3dd',
    'green': '#a7cfbc',
    'orange': '#edc0a6',
    'pink': '#eaa6ae',
}
CATEGORIES = {
    'Smooth': THEME['green'],
    'Erratic': THEME['orange'],
    'Intermittent': THEME['primary'],
    'Lumpy': THEME['secondary'],
    'Talep yok': THEME['muted'],
    'Yetersiz pozitif veri': THEME['orange'],
}


def frame(height=525) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=height, autosize=True,
        paper_bgcolor=THEME['bg'], plot_bgcolor=THEME['bg'],
        font=dict(family='Manrope, Trebuchet MS, sans-serif', color=THEME['text'], size=13),
        margin=dict(l=54, r=24, t=50, b=53),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#372630', bordercolor=THEME['border'],
                        font=dict(color=THEME['text'], size=13)),
        legend=dict(orientation='h', yanchor='bottom', y=1.01, x=0, font=dict(size=12)),
        xaxis=dict(showgrid=False, showline=True, linecolor=THEME['border'],
                   zeroline=False, tickfont=dict(color=THEME['muted'], size=12)),
        yaxis=dict(showgrid=True, gridcolor='#382832', zeroline=False,
                   tickfont=dict(color=THEME['muted'], size=12), rangemode='tozero'),
        transition=dict(duration=460, easing='cubic-in-out'),
    )
    return fig


def sales_series(df: pd.DataFrame, chart_type: str = 'Çizgi', smooth: bool = True) -> go.Figure:
    fig = frame(560)
    if chart_type == 'Sütun':
        fig.add_trace(go.Bar(
            x=df['Ay'], y=df['Satis'], name='Satış',
            marker=dict(color=THEME['primary'], line=dict(color=THEME['panel'], width=0.3)),
            hovertemplate='%{x|%B %Y}<br>Satış: %{y:,.0f} adet<extra></extra>',
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df['Ay'], y=df['Satis'], mode='lines+markers', name='Satış',
            line=dict(color=THEME['primary'], width=3.0,
                      shape='spline' if smooth else 'linear', smoothing=0.45 if smooth else 0),
            marker=dict(size=6, color=THEME['primary'], line=dict(color=THEME['bg'], width=1.2)),
            hovertemplate='%{x|%B %Y}<br>Satış: %{y:,.0f} adet<extra></extra>',
        ))
    fig.update_layout(hovermode='closest', yaxis_title='Satış (adet)',
                      xaxis=dict(rangeslider=dict(visible=False)))
    return fig


def monthly_distribution(df: pd.DataFrame) -> go.Figure:
    fig = frame(535)
    names = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
    months = df['Ay'].dt.month
    for month_id, month_name in enumerate(names, 1):
        vals = df.loc[months == month_id, 'Satis'].to_numpy(dtype=float)
        if not len(vals):
            continue
        fig.add_trace(go.Box(
            y=vals, x=[month_name] * len(vals), name=month_name,
            marker=dict(color=THEME['primary'], size=6),
            line=dict(color=THEME['primary'], width=1.7),
            fillcolor='rgba(239,170,185,.17)',
            boxpoints='all', jitter=0.28, pointpos=0, showlegend=False,
            hovertemplate=f'{month_name}<br>Satış: '+'%{y:,.0f} adet<extra></extra>',
        ))
    fig.update_layout(xaxis_title='Ay', yaxis_title='Satış (adet)', hovermode='closest')
    return fig


def yearly_totals(df: pd.DataFrame) -> go.Figure:
    tbl = (df.assign(Yil=df['Ay'].dt.year)
           .groupby('Yil', as_index=False).agg(Toplam=('Satis', 'sum'), Kayit=('Satis', 'size')))
    fig = frame(535)
    fig.add_trace(go.Bar(
        x=tbl['Yil'].astype(str), y=tbl['Toplam'],
        name='Toplam satış', marker=dict(color=THEME['primary']),
        text=[f'{v:,.0f}' for v in tbl['Toplam']], textposition='outside',
        customdata=tbl['Kayit'],
        hovertemplate='Yıl: %{x}<br>Toplam satış: %{y:,.0f} adet<br>Veri bulunan ay: %{customdata}<extra></extra>',
    ))
    fig.update_layout(yaxis_title='Toplam satış (adet)', hovermode='closest')
    return fig


def category_map(summary: pd.DataFrame, selected: str) -> go.Figure:
    d = summary.dropna(subset=['ADI', 'CV²']).copy()
    fig = frame(555)
    max_x = max(2.6, float(d['ADI'].max() * 1.16)) if len(d) else 2.6
    max_y = max(1.2, float(d['CV²'].max() * 1.16)) if len(d) else 1.2
    # Çok uç değerli serilerde sınıfların bölünmesi grafik sınırına kadar korunur.
    regions = [
        (0, ADI_LIMIT, 0, CV2_LIMIT, 'rgba(167,207,188,.09)'),
        (ADI_LIMIT, max_x, 0, CV2_LIMIT, 'rgba(239,170,185,.07)'),
        (0, ADI_LIMIT, CV2_LIMIT, max_y, 'rgba(237,192,166,.08)'),
        (ADI_LIMIT, max_x, CV2_LIMIT, max_y, 'rgba(218,179,221,.09)'),
    ]
    for x0, x1, y0, y1, color in regions:
        fig.add_shape(type='rect', x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line_width=0, layer='below')
    fig.add_vline(x=ADI_LIMIT, line=dict(color=THEME['muted'], width=1.5, dash='dash'))
    fig.add_hline(y=CV2_LIMIT, line=dict(color=THEME['muted'], width=1.5, dash='dash'))
    for cat, grp in d.groupby('Talep sınıfı'):
        fig.add_trace(go.Scatter(
            x=grp['ADI'], y=grp['CV²'], name=cat, mode='markers',
            customdata=grp[['Malzeme', 'Pozitif ay', 'Ay sayısı']].to_numpy(),
            marker=dict(
                size=[19 if sku == selected else 11 for sku in grp['Malzeme']],
                color=CATEGORIES.get(cat, THEME['orange']), opacity=0.95,
                line=dict(color=[THEME['text'] if sku == selected else THEME['bg']
                                 for sku in grp['Malzeme']], width=1.8)),
            hovertemplate='Malzeme: %{customdata[0]}<br>ADI: %{x:.3f}<br>CV²: %{y:.3f}'
                          '<br>Pozitif ay: %{customdata[1]}/%{customdata[2]}<extra></extra>',
        ))
    fig.update_layout(xaxis_title='ADI · Ortalama talep aralığı',
                      yaxis_title='CV² · Pozitif talep değişkenliği',
                      xaxis_range=[0, max_x], yaxis_range=[0, max_y], hovermode='closest')
    return fig
