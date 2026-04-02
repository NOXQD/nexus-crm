#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_pdf.py — Генератор PDF документации NexusCRM через ReportLab
Запуск: py make_pdf.py
"""
import sys, os, io
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white, HexColor

import tempfile, atexit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus import Image

_TMP_FILES = []
def _cleanup():
    for f in _TMP_FILES:
        try: os.unlink(f)
        except: pass
atexit.register(_cleanup)

# ── Пути ──────────────────────────────────────────────────────────────────────
DOCS_DIR = Path(__file__).parent
OUT_PDF  = DOCS_DIR / 'NexusCRM_Documentation.pdf'
FONTS_DIR = Path('C:/Windows/Fonts')

# ── Регистрация шрифтов Times New Roman ───────────────────────────────────────
pdfmetrics.registerFont(TTFont('TNR',   str(FONTS_DIR / 'times.ttf')))
pdfmetrics.registerFont(TTFont('TNR-B', str(FONTS_DIR / 'timesbd.ttf')))
pdfmetrics.registerFont(TTFont('TNR-I', str(FONTS_DIR / 'timesi.ttf')))
pdfmetrics.registerFont(TTFont('TNR-BI',str(FONTS_DIR / 'timesbi.ttf')))
pdfmetrics.registerFontFamily(
    'TNR', normal='TNR', bold='TNR-B', italic='TNR-I', boldItalic='TNR-BI'
)

# ── Размеры страницы и поля ────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4                   # 595.27 x 841.89 pt
MAR_T  = 2.0 * cm
MAR_B  = 2.0 * cm
MAR_L  = 3.0 * cm
MAR_R  = 1.5 * cm

# ── Стили ──────────────────────────────────────────────────────────────────────
def S(name, **kw):
    defaults = dict(
        fontName='TNR', fontSize=12, leading=14.4,   # single ≈ 1.2×12
        spaceAfter=0, spaceBefore=0,
        alignment=TA_JUSTIFY,
        firstLineIndent=1.25*cm,
    )
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

sBody     = S('Body')
sBodyNoI  = S('BodyNoI', firstLineIndent=0)
sCenter   = S('Center', alignment=TA_CENTER, firstLineIndent=0)
sLeft     = S('Left',   alignment=TA_LEFT,   firstLineIndent=0)
sRight    = S('Right',  alignment=TA_RIGHT,  firstLineIndent=0)
sH1       = S('H1', fontName='TNR-B', fontSize=12, alignment=TA_CENTER,
              firstLineIndent=0, spaceAfter=0, spaceBefore=0)
sH2       = S('H2', fontName='TNR-B', fontSize=12, alignment=TA_CENTER,
              firstLineIndent=0, spaceAfter=0, spaceBefore=0)
sCapT     = S('CapT', alignment=TA_LEFT, firstLineIndent=0)
sCapF     = S('CapF', alignment=TA_CENTER, firstLineIndent=0)
sCapNote  = S('CapNote', alignment=TA_CENTER, firstLineIndent=0, fontSize=12)
sPageNum  = S('PageNum', fontName='TNR', fontSize=10,
              alignment=TA_CENTER, firstLineIndent=0)
sList     = S('List', firstLineIndent=0, leftIndent=1.25*cm,
              alignment=TA_JUSTIFY)
sTOC      = S('TOC', firstLineIndent=0, alignment=TA_LEFT)
sFooter   = S('Footer', fontName='TNR', fontSize=10, alignment=TA_CENTER,
              firstLineIndent=0)
sCode     = S('Code', fontName='Courier', fontSize=9, alignment=TA_LEFT,
              firstLineIndent=0, leading=11)

BL = Spacer(1, 12)   # одна пустая строка (≈12pt)


def bold(text):
    return f'<font name="TNR-B">{text}</font>'


# ── Нижний колонтитул с номером страницы ──────────────────────────────────────
class DocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_num = 0

    def handle_pageBegin(self):
        self._page_num += 1
        super().handle_pageBegin()

    def afterPage(self):
        page = self.page
        if page <= 1:
            return    # Титул без номера
        canvas = self.canv
        canvas.saveState()
        canvas.setFont('TNR', 10)
        # Центр нижнего колонтитула
        x = PAGE_W / 2
        y = MAR_B - 1.25 * cm
        canvas.drawCentredString(x, y, str(page))
        canvas.restoreState()


# ── Диаграммы ─────────────────────────────────────────────────────────────────
def _fig_save(fig, width_cm=14.0):
    from PIL import Image as PILImage
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp.close()
    _TMP_FILES.append(tmp.name)
    fig.savefig(tmp.name, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    # Calculate proportional height
    pim = PILImage.open(tmp.name)
    px_w, px_h = pim.size
    pim.close()
    w = width_cm * cm
    h = w * (px_h / px_w)
    img = Image(tmp.name, width=w, height=h)
    img.hAlign = 'CENTER'
    return img


def fig_architecture():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_facecolor('white')

    def box(x, y, w, h, color, label, sub='', fs=9):
        r = FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.1',
                           linewidth=1.2, edgecolor='#555', facecolor=color)
        ax.add_patch(r)
        ax.text(x+w/2, y+h/2+(0.12 if sub else 0), label,
                ha='center', va='center', fontsize=fs, fontweight='bold')
        if sub:
            ax.text(x+w/2, y+h/2-0.2, sub, ha='center', va='center',
                    fontsize=7, color='#444')

    def arr(x1,y1,x2,y2):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color='#555', lw=1.4))

    ax.text(0.3, 0.55, 'Хранение', fontsize=7, color='#333', rotation=90, va='center')
    box(0.7, 0.2, 3.2, 0.7, '#fef3c7', 'localStorage', 'nexus_crm_clients')
    ax.text(0.3, 2.5, 'JavaScript ES-модули', fontsize=7, color='#333', rotation=90, va='center')
    box(0.7, 1.4, 1.3, 0.7, '#dbeafe', 'storage.js', 'Данные')
    box(2.1, 1.4, 1.3, 0.7, '#dbeafe', 'utils.js', 'Утилиты')
    box(0.7, 2.3, 1.3, 0.7, '#e0e7ff', 'main.js', 'Главная')
    box(2.1, 2.3, 1.3, 0.7, '#e0e7ff', 'form.js', 'Форма')
    box(3.5, 2.3, 1.3, 0.7, '#e0e7ff', 'stats.js', 'Стат.')
    ax.text(0.3, 4.5, 'HTML + CSS', fontsize=7, color='#333', rotation=90, va='center')
    box(0.7, 3.8, 1.3, 0.7, '#d1fae5', 'index.html', 'Клиенты')
    box(2.1, 3.8, 1.3, 0.7, '#d1fae5', 'form.html', 'Форма')
    box(3.5, 3.8, 1.3, 0.7, '#d1fae5', 'stats.html', 'Стат.')
    box(4.9, 3.8, 1.3, 0.7, '#d1fae5', 'about.html', 'О проекте')
    box(0.7, 4.7, 5.5, 0.6, '#f0fdf4', 'css/style.css', fs=8)
    box(0.7, 5.5, 5.5, 0.4, '#fce7f3', 'Пользователь (браузер)', fs=9)
    arr(1.95, 0.9, 1.35, 1.4)
    arr(1.35, 2.1, 1.35, 2.3)
    arr(2.75, 2.1, 2.75, 2.3)
    arr(1.35, 3.0, 1.35, 3.8)
    arr(2.75, 3.0, 2.75, 3.8)
    arr(4.15, 3.0, 4.15, 3.8)
    arr(3.5, 5.5, 3.5, 4.5)
    legend = [
        mpatches.Patch(facecolor='#fce7f3', edgecolor='#555', label='Пользователь'),
        mpatches.Patch(facecolor='#d1fae5', edgecolor='#555', label='HTML-страницы'),
        mpatches.Patch(facecolor='#e0e7ff', edgecolor='#555', label='Прикладная логика'),
        mpatches.Patch(facecolor='#dbeafe', edgecolor='#555', label='Инфраструктура'),
        mpatches.Patch(facecolor='#fef3c7', edgecolor='#555', label='Хранилище'),
    ]
    ax.legend(handles=legend, loc='center right', fontsize=7,
              framealpha=0.9, bbox_to_anchor=(11.8, 3.0))
    ax.set_title('Архитектура приложения NexusCRM', fontsize=11, pad=10)
    return _fig_save(fig, 12.5)


def fig_navigation():
    fig, ax = plt.subplots(figsize=(10, 4.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.5); ax.axis('off')
    ax.set_facecolor('white')

    def box(x, y, w, h, color, label, sub=''):
        r = FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.15',
                           linewidth=1.3, edgecolor='#444', facecolor=color)
        ax.add_patch(r)
        ax.text(x+w/2, y+h/2+(0.1 if sub else 0), label,
                ha='center', va='center', fontsize=10, fontweight='bold')
        if sub:
            ax.text(x+w/2, y+h/2-0.2, sub, ha='center', va='center',
                    fontsize=7.5, color='#555')

    def arr(x1,y1,x2,y2,label='',col='#555'):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=col, lw=1.4))
        if label:
            ax.text((x1+x2)/2+0.05, (y1+y2)/2, label, fontsize=7.5, color=col)

    box(0.3, 1.5, 2.2, 1.0, '#d1fae5', 'index.html', 'Список клиентов')
    box(3.5, 1.5, 2.2, 1.0, '#e0e7ff', 'form.html', 'Добавить/Редактировать')
    box(7.0, 1.5, 2.2, 1.0, '#fef3c7', 'stats.html', 'Статистика')
    box(3.5, 3.2, 2.2, 1.0, '#fce7f3', 'about.html', 'О проекте')
    box(0.3, 0.1, 2.2, 0.9, '#f0fdf4', 'Браузер', 'Открыть файл / URL')
    arr(1.4, 1.0, 1.4, 1.5)
    arr(2.5, 2.0, 3.5, 2.0, 'Добавить')
    arr(3.5, 2.4, 2.5, 2.4, 'Сохранить')
    arr(2.5, 1.8, 3.5, 1.7, 'Редактировать')
    arr(6.0, 2.0, 7.0, 2.0, 'Статистика', '#888')
    arr(7.0, 2.4, 6.0, 2.4, 'Назад', '#888')
    arr(4.6, 3.2, 4.6, 2.5, 'О проекте', '#888')
    ax.set_title('Схема переходов между страницами NexusCRM', fontsize=11, pad=10)
    return _fig_save(fig, 12.5)


def fig_algorithm():
    fig, ax = plt.subplots(figsize=(7.5, 9))
    ax.set_xlim(0, 7.5); ax.set_ylim(0, 9); ax.axis('off')
    ax.set_facecolor('white')

    def rbox(x, y, w, h, color, text, fs=9):
        r = FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.1',
                           linewidth=1.2, edgecolor='#444', facecolor=color)
        ax.add_patch(r)
        ax.text(x+w/2, y+h/2, text, ha='center', va='center',
                fontsize=fs, multialignment='center')

    def diamond(x, y, w, h, color, text):
        from matplotlib.patches import Polygon
        cx, cy = x+w/2, y+h/2
        pts = [(cx, y+h), (x+w, cy), (cx, y), (x, cy)]
        p = Polygon(pts, closed=True, linewidth=1.2,
                    edgecolor='#444', facecolor=color)
        ax.add_patch(p)
        ax.text(cx, cy, text, ha='center', va='center', fontsize=8,
                multialignment='center')

    def arr(x1,y1,x2,y2,label=''):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=1.3))
        if label:
            ax.text((x1+x2)/2+0.1, (y1+y2)/2, label, fontsize=7.5)

    rbox(2.2, 8.35, 3.0, 0.5, '#fce7f3', 'НАЧАЛО', 10)
    arr(3.7, 8.35, 3.7, 7.8)
    rbox(1.7, 7.3, 4.0, 0.5, '#dbeafe', 'Загрузка index.html в браузере')
    arr(3.7, 7.3, 3.7, 6.8)
    rbox(1.7, 6.3, 4.0, 0.5, '#e0e7ff', 'init(): вызов initClients()')
    arr(3.7, 6.3, 3.7, 5.8)
    diamond(2.2, 5.1, 3.0, 0.7, '#fef3c7', 'localStorage\nпуст?')
    arr(2.2, 5.45, 1.2, 5.45, 'Да')
    rbox(0.1, 5.1, 1.0, 0.7, '#d1fae5', 'Сеять\nдемо\nданные', 7)
    arr(0.6, 5.1, 0.6, 4.4)
    arr(0.6, 4.4, 3.2, 4.4)
    arr(5.2, 5.45, 5.8, 5.45, 'Нет')
    rbox(5.8, 5.1, 1.5, 0.7, '#d1fae5', 'Читать\nclients[]', 7)
    arr(6.55, 5.1, 6.55, 4.4)
    arr(6.55, 4.4, 5.2, 4.4)
    rbox(1.7, 3.8, 4.0, 0.5, '#e0e7ff', 'renderClients(): фильтр + рендер карточек')
    arr(3.7, 3.8, 3.7, 3.3)
    rbox(1.7, 2.8, 4.0, 0.5, '#e0e7ff', 'setupSearch(), setupFilters()')
    arr(3.7, 2.8, 3.7, 2.3)
    diamond(2.2, 1.6, 3.0, 0.65, '#fef3c7', 'pageshow\npersisted?')
    arr(3.7, 1.6, 3.7, 1.0, 'Нет')
    arr(5.2, 1.93, 5.9, 1.93, 'Да')
    rbox(5.9, 1.6, 1.5, 0.65, '#fce7f3', 'reinit()\n(без hook)', 7)
    rbox(2.2, 0.5, 3.0, 0.5, '#fce7f3', 'КОНЕЦ', 10)

    ax.set_title('Алгоритм инициализации главной страницы', fontsize=11, pad=10)
    return _fig_save(fig, 9.0)


def fig_modules():
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 5); ax.axis('off')
    ax.set_facecolor('white')

    def box(x,y,w,h,color,label):
        r = FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.15',
                           linewidth=1.3, edgecolor='#444', facecolor=color)
        ax.add_patch(r)
        ax.text(x+w/2, y+h/2, label, ha='center', va='center',
                fontsize=9, fontweight='bold')

    def arr(x1,y1,x2,y2):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=1.4))

    box(0.5, 0.5, 2.0, 0.8, '#dbeafe', 'storage.js')
    box(3.0, 0.5, 2.0, 0.8, '#dbeafe', 'utils.js')
    box(0.0, 2.5, 2.0, 0.8, '#e0e7ff', 'main.js')
    box(2.5, 2.5, 2.0, 0.8, '#e0e7ff', 'form.js')
    box(5.0, 2.5, 2.0, 0.8, '#e0e7ff', 'stats.js')
    box(0.0, 4.0, 2.0, 0.7, '#d1fae5', 'index.html')
    box(2.5, 4.0, 2.0, 0.7, '#d1fae5', 'form.html')
    box(5.0, 4.0, 2.0, 0.7, '#d1fae5', 'stats.html')
    box(7.5, 4.0, 2.0, 0.7, '#d1fae5', 'about.html')
    arr(1.5, 1.3, 1.0, 2.5)
    arr(1.5, 1.3, 3.5, 2.5)
    arr(1.5, 1.3, 6.0, 2.5)
    arr(4.0, 1.3, 1.0, 2.5)
    arr(4.0, 1.3, 3.5, 2.5)
    arr(4.0, 1.3, 6.0, 2.5)
    arr(1.0, 3.3, 1.0, 4.0)
    arr(3.5, 3.3, 3.5, 4.0)
    arr(6.0, 3.3, 6.0, 4.0)
    legend = [
        mpatches.Patch(facecolor='#d1fae5', edgecolor='#444', label='HTML-страницы'),
        mpatches.Patch(facecolor='#e0e7ff', edgecolor='#444', label='Прикладные модули'),
        mpatches.Patch(facecolor='#dbeafe', edgecolor='#444', label='Инфраструктурные модули'),
    ]
    ax.legend(handles=legend, loc='center right', fontsize=8,
              framealpha=0.9, bbox_to_anchor=(11.0, 2.5))
    ax.set_title('Схема зависимостей JS-модулей NexusCRM', fontsize=11, pad=10)
    return _fig_save(fig, 12.5)


# ══════════════════════════════════════════════════════════════════════════════
# ПОСТРОИТЕЛЬ ДОКУМЕНТА
# ══════════════════════════════════════════════════════════════════════════════

story = []

def P(text, style=None):
    return Paragraph(text, style or sBody)

def add(*items):
    story.extend(items)

def blank():
    story.append(BL)

def pagebreak():
    story.append(PageBreak())

def structural(text):
    blank()
    add(P(f'<b>{text.upper()}</b>', sH1))
    blank()

def section(number, text):
    blank()
    add(P(f'<b>{number} {text.upper()}</b>', sH1))
    blank()

def paragraph_heading(number, title):
    blank(); blank()
    add(P(f'<b>{number} {title}</b>', sH2))
    blank()

def body(text):
    add(P(text, sBody))

def body_noi(text):
    add(P(text, sBodyNoI))

def li(text, prefix='\u2013'):
    add(P(f'{prefix}&nbsp;&nbsp;{text}', sList))

def numbered_li(n, text):
    add(P(f'{n})&nbsp;&nbsp;{text}', sList))

def table_caption(n, title):
    blank()
    add(P(f'Таблица {n} \u2013 {title}', sCapT))

def figure_caption(n, title, note=None):
    add(P(f'Рисунок {n} \u2013 {title}', sCapF))
    if note:
        add(P(f'Примечание \u2013 {note}', sCapNote))
    blank()


# ── Стиль таблиц ──────────────────────────────────────────────────────────────
def tbl_style_base():
    return TableStyle([
        ('FONTNAME',    (0,0), (-1,-1), 'TNR'),
        ('FONTSIZE',    (0,0), (-1,-1), 11),
        ('LEADING',     (0,0), (-1,-1), 13),
        ('GRID',        (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND',  (0,0), (-1, 0), HexColor('#f0f0f0')),
        ('FONTNAME',    (0,0), (-1, 0), 'TNR-B'),
        ('ALIGN',       (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING',(0,0), (-1,-1), 4),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# СОДЕРЖИМОЕ ДОКУМЕНТА
# ══════════════════════════════════════════════════════════════════════════════

def build_title():
    add(
        Spacer(1, 1.0*cm),
        P('ТОО «Колледж Хекслет»', sCenter),
        BL,
        P('Направление подготовки: Информационные системы', sCenter),
        Spacer(1, 3.0*cm),
        P('<b>ПРОЕКТНАЯ РАБОТА</b>', ParagraphStyle('T14', fontName='TNR-B',
           fontSize=14, leading=17, alignment=TA_CENTER, firstLineIndent=0)),
        Spacer(1, 1.0*cm),
        P('Тема: «Разработка веб-приложения NexusCRM\nдля управления базой клиентов малого бизнеса»',
          sCenter),
        Spacer(1, 4.0*cm),
        P('Выполнил: студент 2 курса,', sRight),
        P('группа 13 ТИС', sRight),
        P('Шафиев Артём', sRight),
        BL,
        P('Руководитель:', sRight),
        P('преподаватель Колледжа Хекслет', sRight),
        Spacer(1, 5.0*cm),
        P('Алматы 2026', sCenter),
    )
    pagebreak()


def build_toc():
    structural('СОДЕРЖАНИЕ')

    toc_data = [
        ('ВВЕДЕНИЕ', '3'),
        ('1  АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ', '4'),
        ('   1.1  Актуальность разработки', '4'),
        ('   1.2  Анализ существующих CRM-решений', '5'),
        ('   1.3  Цель и задачи проекта', '6'),
        ('2  ПРОЕКТИРОВАНИЕ СИСТЕМЫ', '7'),
        ('   2.1  Концептуальная архитектура приложения', '7'),
        ('   2.2  Модель данных клиента', '9'),
        ('   2.3  Структура файлов проекта', '10'),
        ('3  РЕАЛИЗАЦИЯ', '11'),
        ('   3.1  Стек технологий', '11'),
        ('   3.2  Описание программных модулей', '12'),
        ('   3.3  Пользовательский интерфейс', '14'),
        ('   3.4  Алгоритм работы приложения', '16'),
        ('4  РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ', '18'),
        ('   4.1  Требования к запуску и установке', '18'),
        ('   4.2  Основные сценарии использования', '19'),
        ('   4.3  Ограничения и перспективы развития', '21'),
        ('ЗАКЛЮЧЕНИЕ', '22'),
        ('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', '23'),
        ('Приложение 1', '25'),
        ('Приложение 2', '26'),
    ]

    usable_w = PAGE_W - MAR_L - MAR_R

    for title, page in toc_data:
        tbl = Table(
            [[P(title, sLeft), P(page, sRight)]],
            colWidths=[usable_w - 1.2*cm, 1.2*cm]
        )
        tbl.setStyle(TableStyle([
            ('FONTNAME',  (0,0), (-1,-1), 'TNR'),
            ('FONTSIZE',  (0,0), (-1,-1), 12),
            ('LEADING',   (0,0), (-1,-1), 14.4),
            ('TOPPADDING',(0,0), (-1,-1), 1),
            ('BOTTOMPADDING',(0,0),(-1,-1), 1),
            ('LINEBELOW', (0,0), (0,0), 0.3, colors.grey),
        ]))
        story.append(tbl)

    pagebreak()


def build_introduction():
    structural('ВВЕДЕНИЕ')

    body('В современных условиях развития малого бизнеса одним из ключевых '
         'инструментов повышения эффективности работы с клиентами является система '
         'управления взаимоотношениями с клиентами (CRM, от англ. Customer Relationship '
         'Management). CRM-системы позволяют структурировать информацию о клиентах, '
         'отслеживать статусы сделок, вести историю взаимодействий и анализировать '
         'ключевые показатели работы команды продаж [1].')

    body('Вместе с тем существующие на рынке CRM-решения — Bitrix24, AmoCRM, Salesforce — '
         'обладают рядом существенных недостатков для субъектов малого бизнеса: высокая '
         'стоимость лицензии или подписки, избыточный функционал, обязательное наличие '
         'серверной инфраструктуры и постоянного интернет-соединения, а также сложность '
         'первоначальной настройки. Нередко предприниматели и небольшие команды ведут '
         'клиентскую базу в таблицах Microsoft Excel или Google Sheets, что не обеспечивает '
         'должного уровня удобства, статусной модели и аналитических инструментов [2].')

    body('Данная проектная работа посвящена разработке клиентского веб-приложения '
         'NexusCRM — системы управления базой клиентов для малого бизнеса, реализованной '
         'на нативных технологиях HTML5, CSS3 и JavaScript с применением ES-модулей. '
         'Приложение функционирует полностью в браузере без необходимости развёртывания '
         'серверной части и подключения к интернету при работе с данными.')

    body('Целью проекта является разработка функционального веб-приложения для ведения '
         'базы клиентов с реализацией операций добавления, редактирования, удаления, '
         'поиска и фильтрации записей, а также модуля статистической аналитики.')

    body('Для достижения поставленной цели были определены следующие задачи:')
    li('провести анализ предметной области и существующих CRM-решений;')
    li('спроектировать архитектуру клиентского веб-приложения;')
    li('реализовать слой хранения данных на основе localStorage браузера;')
    li('разработать пользовательский интерфейс с тёмной цветовой схемой и адаптивной вёрсткой;')
    li('реализовать полный набор операций управления клиентскими данными;')
    li('разработать модуль статистики и аналитики по клиентской базе;')
    li('обеспечить защиту от XSS-атак и устойчивость к ошибкам хранилища данных.')

    body('Объектом исследования являются процессы управления клиентскими данными '
         'в условиях малого бизнеса.')
    body('Предметом исследования служат технологии разработки клиентских веб-приложений '
         'для автоматизации CRM-процессов.')
    body('Практическая значимость работы определяется готовностью разработанного '
         'приложения к применению в реальных условиях: оно не требует установки '
         'дополнительного программного обеспечения, функционирует без подключения к '
         'интернету и может быть развёрнуто на любом статическом хостинге.')
    pagebreak()


def build_section1():
    section('1', 'АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ')

    paragraph_heading('1.1', 'Актуальность разработки')
    body('В условиях цифровизации экономики управление взаимоотношениями с клиентами '
         'становится критически важным элементом успешной деятельности предприятий любого '
         'масштаба. По данным аналитических агентств, использование CRM-систем повышает '
         'производительность менеджеров по продажам на 26–34%, увеличивает конверсию '
         'лидов в сделки и обеспечивает систематизацию клиентской базы [3].')
    body('Субъекты малого бизнеса — индивидуальные предприниматели, небольшие команды '
         'продаж, фриланс-студии и агентства — нередко сталкиваются с проблемой '
         'отсутствия доступного инструмента для ведения клиентской базы. Корпоративные '
         'CRM-решения предъявляют высокие требования к инфраструктуре, требуют '
         'постоянного интернет-соединения и обладают избыточным функционалом, '
         'не востребованным малым бизнесом.')
    body('Специфика работы небольших команд предполагает необходимость простого и '
         'быстрого инструмента, не требующего дополнительных затрат на инфраструктуру '
         'и администрирование. Внедрение клиентского веб-приложения, функционирующего '
         'непосредственно в браузере и хранящего данные локально, позволяет решить '
         'указанные проблемы при нулевых затратах на развёртывание.')
    body('Описанная проблема определяет актуальность настоящего проекта: разработка '
         'NexusCRM ориентирована именно на нишу лёгких клиентских CRM-инструментов, '
         'доступных без сторонней инфраструктуры.')

    paragraph_heading('1.2', 'Анализ существующих CRM-решений')
    body('В целях обоснования подхода к разработке авторами проекта был проведён '
         'сравнительный анализ существующих CRM-систем по критериям, наиболее значимым '
         'для субъектов малого бизнеса. Ниже в таблице 1 представлены результаты анализа.')

    usable_w = PAGE_W - MAR_L - MAR_R
    table_caption(1, 'Сравнительный анализ существующих CRM-решений')
    data = [
        ['Критерий', 'Bitrix24', 'AmoCRM', 'Salesforce', 'NexusCRM'],
        ['1', '2', '3', '4', '5'],
        ['Тип размещения', 'Облачный SaaS', 'Облачный SaaS', 'Облачный SaaS', 'Клиентский (браузер)'],
        ['Серверная часть', 'Обязательна', 'Обязательна', 'Обязательна', 'Не требуется'],
        ['Интернет для работы', 'Обязателен', 'Обязателен', 'Обязателен', 'Не требуется'],
        ['Бесплатный план', 'Ограниченный', 'Отсутствует', 'Отсутствует', 'Полный'],
        ['Сложность освоения', 'Высокая', 'Средняя', 'Высокая', 'Низкая'],
        ['Кастомизация', 'Высокая', 'Средняя', 'Высокая', 'Ограниченная'],
        ['Экспорт данных', 'Есть', 'Есть', 'Есть', 'Не реализован'],
        ['Примечание – составлено автором на основании проведённого исследования', '', '', '', ''],
    ]
    cws = [usable_w*0.26, usable_w*0.19, usable_w*0.19, usable_w*0.19, usable_w*0.17]

    tbl_data = []
    for row in data:
        tbl_data.append([P(cell, ParagraphStyle('TC', fontName='TNR', fontSize=11,
                           leading=13, firstLineIndent=0)) for cell in row])

    tbl = Table(tbl_data, colWidths=cws, repeatRows=2)
    ts = tbl_style_base()
    ts.add('SPAN',    (0,-1), (-1,-1))
    ts.add('ALIGN',   (0,-1), (-1,-1), 'LEFT')
    ts.add('FONTSIZE',(0,-1), (-1,-1), 10)
    ts.add('ITALIC',  (0, 1), (-1,  1), 1)  # нумерация строки
    ts.add('ALIGN',   (0, 1), (-1,  1), 'CENTER')
    ts.add('ALIGN',   (1, 2), (-1, -2), 'CENTER')
    tbl.setStyle(ts)
    story.append(tbl)
    blank()

    body('Анализ, приведённый в таблице 1, показывает, что ни одно из рассмотренных '
         'корпоративных CRM-приложений не обеспечивает возможности работы без '
         'интернет-соединения и без серверной инфраструктуры при полной функциональности. '
         'Разрабатываемый проект NexusCRM занимает нишу лёгкого клиентского инструмента '
         'с нулевой стоимостью и минимальными требованиями к окружению.')

    paragraph_heading('1.3', 'Цель и задачи проекта')
    body('Целью проекта является разработка веб-приложения NexusCRM, обеспечивающего '
         'управление базой клиентов малого бизнеса с набором базовых CRM-функций: ведение '
         'записей, статусная модель, поиск, фильтрация и аналитика — без необходимости '
         'серверной части и постоянного интернет-соединения.')
    body('Для достижения цели авторами проекта были сформулированы следующие задачи:')
    for i, t in enumerate([
        'Провести анализ предметной области и требований к системе.',
        'Спроектировать многостраничную архитектуру клиентского приложения.',
        'Реализовать слой хранения данных на основе Web Storage API (localStorage).',
        'Разработать компонентную структуру JavaScript-логики с применением ES-модулей.',
        'Создать пользовательский интерфейс с тёмной цветовой схемой и адаптивной вёрсткой.',
        'Разработать модуль статистики с KPI-метриками и визуализацией данных.',
        'Провести тестирование и сформировать пользовательскую документацию.',
    ], 1):
        numbered_li(i, t)
    pagebreak()


def build_section2():
    section('2', 'ПРОЕКТИРОВАНИЕ СИСТЕМЫ')

    paragraph_heading('2.1', 'Концептуальная архитектура приложения')
    body('NexusCRM представляет собой клиентское многостраничное веб-приложение '
         '(Multi-Page Application, MPA), построенное на нативных веб-технологиях без '
         'применения клиентских фреймворков. Архитектура реализована по принципу '
         'разделения ответственности: каждая HTML-страница отвечает за отдельную область '
         'функциональности, а JavaScript-файлы разделены по назначению и взаимодействуют '
         'посредством стандартного механизма ES-модулей (import/export).')
    body('На рисунке 1 представлена концептуальная архитектура приложения NexusCRM '
         'с разбивкой на три функциональных слоя.')
    story.append(fig_architecture())
    blank()
    figure_caption(1, 'Концептуальная архитектура приложения NexusCRM',
                   'составлено автором на основании проведённого исследования')
    body('Приложение состоит из трёх функциональных слоёв:')
    li('слой представления — четыре HTML-страницы и единая таблица стилей css/style.css;')
    li('слой бизнес-логики — пять JavaScript ES-модулей, реализующих прикладные '
       'операции и инфраструктурные функции;')
    li('слой хранения данных — Web Storage API браузера (localStorage), предоставляющий '
       'персистентное хранилище без серверной части.')
    body('Все операции записи и чтения данных клиентов инкапсулированы в storage.js '
         'и не дублируются в прикладной логике. Такое разделение обеспечивает '
         'поддерживаемость и расширяемость кода.')

    paragraph_heading('2.2', 'Модель данных клиента')
    body('Каждый клиент в системе NexusCRM представлен JavaScript-объектом, '
         'хранящимся в виде элемента массива в localStorage браузера под ключом '
         '«nexus_crm_clients». В таблице 2 описана полная структура объекта клиента.')

    usable_w = PAGE_W - MAR_L - MAR_R
    table_caption(2, 'Поля объекта клиента в хранилище данных')
    data2 = [
        ['Поле', 'Тип данных', 'Обязательное', 'Описание'],
        ['1', '2', '3', '4'],
        ['id', 'string', 'Да', 'Уникальный идентификатор: метка времени + случайное число'],
        ['fullName', 'string', 'Да', 'Полное имя клиента'],
        ['phone', 'string', 'Да', 'Номер телефона'],
        ['email', 'string', 'Да', 'Адрес электронной почты (валидируется по формату)'],
        ['status', 'string', 'Да', 'Статус сделки: new, active или completed'],
        ['comment', 'string', 'Нет', 'Текстовый комментарий, до 500 символов'],
        ['createdAt', 'string', 'Да', 'Дата создания в формате ISO 8601'],
        ['Примечание – составлено автором на основании проведённого исследования', '', '', ''],
    ]
    cws2 = [usable_w*0.17, usable_w*0.16, usable_w*0.18, usable_w*0.49]
    tbl2_data = [[P(c, ParagraphStyle('TC2', fontName='TNR', fontSize=11,
                    leading=13, firstLineIndent=0)) for c in row] for row in data2]
    tbl2 = Table(tbl2_data, colWidths=cws2, repeatRows=2)
    ts2 = tbl_style_base()
    ts2.add('SPAN', (0,-1), (-1,-1))
    ts2.add('ITALIC', (0,1), (-1,1), 1)
    ts2.add('ALIGN', (0,1), (-1,1), 'CENTER')
    ts2.add('ALIGN', (1,2), (2,-2), 'CENTER')
    tbl2.setStyle(ts2)
    story.append(tbl2)
    blank()

    body('Статусная модель клиента предполагает три состояния:')
    li('«Новый» (new) — клиент только добавлен в систему, работа с ним не начата;')
    li('«В работе» (active) — ведётся активная работа с клиентом;')
    li('«Завершён» (completed) — сделка закрыта, работа завершена.')
    body('Переход между статусами осуществляется свободно, без ограничений на порядок: '
         'пользователь может в любой момент установить любой из трёх статусов '
         'через выпадающий список непосредственно в карточке клиента.')

    paragraph_heading('2.3', 'Структура файлов проекта')
    body('Файловая структура проекта NexusCRM построена по принципу разделения статических '
         'ресурсов по типу: HTML-страницы расположены в корневой директории, таблицы '
         'стилей — в поддиректории css/, JavaScript-модули — в поддиректории js/. '
         'В таблице 3 представлены все файлы проекта с описанием их назначения.')

    table_caption(3, 'Файловая структура проекта NexusCRM')
    data3 = [
        ['Файл / директория', 'Назначение'],
        ['1', '2'],
        ['index.html', 'Главная страница: отображение списка клиентов'],
        ['form.html', 'Форма добавления и редактирования клиента'],
        ['stats.html', 'Страница статистики и аналитики по базе клиентов'],
        ['about.html', 'Информационная страница о проекте'],
        ['css/style.css', 'Основная таблица стилей: тёмная тема, переменные, адаптивность'],
        ['js/main.js', 'Логика главной страницы: рендер, поиск, фильтр, CRUD'],
        ['js/storage.js', 'Слой хранения данных: операции с localStorage'],
        ['js/form.js', 'Логика формы: валидация, добавление, редактирование'],
        ['js/stats.js', 'Расчёт и отображение статистических показателей'],
        ['js/utils.js', 'Общие вспомогательные функции для всех модулей'],
        ['Примечание – составлено автором на основании проведённого исследования', ''],
    ]
    cws3 = [usable_w*0.30, usable_w*0.70]
    tbl3_d = [[P(c, ParagraphStyle('TC3', fontName='TNR', fontSize=11,
                  leading=13, firstLineIndent=0)) for c in row] for row in data3]
    tbl3 = Table(tbl3_d, colWidths=cws3, repeatRows=2)
    ts3 = tbl_style_base()
    ts3.add('SPAN', (0,-1), (-1,-1))
    ts3.add('ITALIC', (0,1), (-1,1), 1)
    ts3.add('ALIGN', (0,1), (-1,1), 'CENTER')
    tbl3.setStyle(ts3)
    story.append(tbl3)
    blank()
    body('Полная структура файлов проекта также приведена в Приложении 1.')
    pagebreak()


def build_section3():
    section('3', 'РЕАЛИЗАЦИЯ')

    paragraph_heading('3.1', 'Стек технологий')
    body('Разработка приложения NexusCRM выполнена исключительно на нативных '
         'веб-технологиях без привлечения сторонних фреймворков, библиотек или систем '
         'сборки. Такой подход обеспечивает нулевое количество зависимостей, отсутствие '
         'необходимости в npm-пакетах и максимальную переносимость приложения. '
         'В таблице 4 представлен применяемый стек технологий.')

    usable_w = PAGE_W - MAR_L - MAR_R
    table_caption(4, 'Стек технологий проекта NexusCRM')
    data4 = [
        ['Технология', 'Версия', 'Назначение'],
        ['1', '2', '3'],
        ['HTML5', '—', 'Структура страниц, семантическая разметка'],
        ['CSS3', '—', 'Стилизация, тёмная цветовая схема, адаптивная вёрстка'],
        ['JavaScript (ES2020+)', '—', 'Бизнес-логика, ES-модули (import/export)'],
        ['Web Storage API', '—', 'Персистентное хранение данных в localStorage'],
        ['Google Fonts API', '—', 'Подключение шрифта Inter для интерфейса'],
        ['Примечание – составлено автором на основании проведённого исследования', '', ''],
    ]
    cws4 = [usable_w*0.27, usable_w*0.16, usable_w*0.57]
    tbl4_d = [[P(c, ParagraphStyle('TC4', fontName='TNR', fontSize=11,
                  leading=13, firstLineIndent=0)) for c in row] for row in data4]
    tbl4 = Table(tbl4_d, colWidths=cws4, repeatRows=2)
    ts4 = tbl_style_base()
    ts4.add('SPAN', (0,-1), (-1,-1))
    ts4.add('ITALIC', (0,1), (-1,1), 1)
    ts4.add('ALIGN', (0,1), (-1,1), 'CENTER')
    ts4.add('ALIGN', (1,2), (1,-2), 'CENTER')
    tbl4.setStyle(ts4)
    story.append(tbl4)
    blank()

    body('Ключевой особенностью реализации является использование механизма ES-модулей '
         '(ECMAScript Modules), появившегося в стандарте ES2015 и поддерживаемого всеми '
         'современными браузерами без транспиляции. Это позволяет организовать код в '
         'отдельные файлы с явным описанием зависимостей через директивы import и export, '
         'аналогично модульным системам серверных платформ [4].')
    body('Данные приложения хранятся в localStorage — частном случае Web Storage API, '
         'предоставляемого браузером. localStorage обеспечивает персистентное '
         '(сохраняющееся между сессиями) хранение пар ключ–значение с квотой обычно '
         '5–10 МБ на домен [5].')

    paragraph_heading('3.2', 'Описание программных модулей')
    body('Программный код приложения разделён на пять JavaScript-модулей в директории '
         'js/, каждый из которых выполняет строго определённые функции. '
         'Схема зависимостей модулей приведена в Приложении 2.')

    body('Модуль storage.js реализует слой доступа к данным. Он экспортирует '
         'следующие функции:')
    li('getClients() — чтение массива клиентов из localStorage с валидацией структуры; '
       'при повреждении хранилища автоматически восстанавливает демо-данные;')
    li('saveClients(clients) — сохранение массива клиентов в localStorage в формате JSON;')
    li('initClients() — инициализация хранилища; при первом запуске заполняет его '
       'шестью демонстрационными записями;')
    li('addClient(client) — добавление нового объекта клиента в конец массива;')
    li('updateClient(id, updates) — частичное обновление полей клиента по идентификатору;')
    li('deleteClient(id) — удаление клиента по идентификатору;')
    li('getClientById(id) — поиск и возврат клиента по идентификатору или null;')
    li('resetToDefaults() — служебная функция сброса хранилища к демо-данным.')

    body('Модуль utils.js содержит общие вспомогательные функции:')
    li('generateId() — генерация уникального строкового идентификатора;')
    li('formatDate(isoString) — преобразование ISO-даты в формат ДД.ММ.ГГГГ;')
    li('getInitials(fullName) — извлечение двух заглавных инициалов из полного имени;')
    li('getStatusLabel(status) / getStatusClass(status) — русскоязычный текст и CSS-класс статуса;')
    li('getAvatarColor(name) — детерминированный цвет аватара из палитры;')
    li('escapeHtml(str) — экранирование HTML-спецсимволов для защиты от XSS-атак [6];')
    li('showToast(message, type, duration) — всплывающее уведомление с автозакрытием;')
    li('debounce(fn, delay) — создание отложенной версии функции;')
    li('setActiveNav() — подсветка активного пункта навигации по текущему URL.')

    body('Модуль main.js содержит логику главной страницы (index.html). Он реализует '
         'рендеринг карточек клиентов, применение фильтров и поиска, обработку '
         'изменения статуса и удаления клиентов. Поиск реализован с задержкой 280 мс '
         'посредством функции debounce(). Модуль поддерживает восстановление страницы '
         'из кэша браузера (bfcache): при событии pageshow с persisted=true вызывается '
         'облегчённая функция reinit() без повторной привязки обработчиков.')

    body('Модуль form.js отвечает за логику страницы form.html. Он поддерживает два '
         'режима: создание нового клиента и редактирование существующего. '
         'Режим редактирования определяется по параметру URL «edit=<id>». '
         'Реализована клиентская валидация обязательных полей и формата email.')

    body('Модуль stats.js формирует данные для страницы статистики: рассчитывает '
         'пять KPI-показателей, формирует разбивку по статусам с анимированными '
         'прогресс-барами и строит столбчатую диаграмму активности за последние '
         'шесть месяцев на основе поля createdAt.')

    paragraph_heading('3.3', 'Пользовательский интерфейс')
    body('Приложение NexusCRM включает четыре страницы с единой навигацией и общей '
         'таблицей стилей. Интерфейс выполнен в тёмной цветовой схеме с акцентным '
         'фиолетово-синим цветом (#6366f1).')

    body('Страница «Клиенты» (index.html) — главная страница приложения. '
         'Она содержит секцию-hero с заголовком и счётчиками, панель инструментов '
         'с полем поиска и фильтрами по статусу, а также сетку карточек клиентов. '
         'Каждая карточка отображает аватар с инициалами, имя, email, статус-значок, '
         'телефон, комментарий и дату. В подвале карточки — выпадающий список '
         'смены статуса, кнопки редактирования и удаления.')

    body('Страница «Добавить клиента» (form.html) реализует форму с полями: '
         'полное имя, телефон, email (все три обязательны), статус, дата и '
         'текстовый комментарий (до 500 символов). Поддерживает режимы '
         'создания и редактирования.')

    body('Страница «Статистика» (stats.html) отображает: пять KPI-карточек '
         '(всего, новые, в работе, завершённые, конверсия), разбивку по статусам '
         'с прогресс-барами и столбчатую диаграмму активности по месяцам.')

    body('Страница «О проекте» (about.html) содержит описание возможностей, '
         'пошаговую инструкцию и блок с информацией об авторе.')

    body('На рисунке 2 представлена схема навигационных переходов между страницами.')
    story.append(fig_navigation())
    figure_caption(2, 'Схема переходов между страницами приложения NexusCRM',
                   'составлено автором на основании проведённого исследования')

    body('Все страницы адаптированы для мобильных устройств: при ширине экрана '
         'менее 768 пикселей навигационное меню преобразуется в выпадающее, '
         'активируемое кнопкой-гамбургером. Сетка карточек перестраивается '
         'с трёх столбцов до одного.')

    paragraph_heading('3.4', 'Алгоритм работы приложения')
    body('На рисунке 3 представлен алгоритм инициализации и работы главной страницы.')
    story.append(fig_algorithm())
    figure_caption(3, 'Алгоритм инициализации главной страницы приложения',
                   'составлено автором на основании проведённого исследования')

    body('Работа приложения начинается с загрузки index.html. Поскольку JS-модули '
         'подключаются с атрибутом type="module" и являются отложенными (deferred), '
         'к моменту выполнения скрипта DOM уже полностью разобран. '
         'Функция init() последовательно выполняет следующие действия:')
    numbered_li(1, 'вызывает initClients() для инициализации хранилища данных '
                   '(при пустом хранилище — автоматическое заполнение демо-данными);')
    numbered_li(2, 'вызывает setActiveNav() для подсветки активного пункта навигации;')
    numbered_li(3, 'вызывает renderClients() для отображения карточек клиентов '
                   'с учётом текущего фильтра и строки поиска;')
    numbered_li(4, 'выполняет однократную привязку обработчиков событий '
                   'через флаг listenersAttached.')

    body('При восстановлении страницы из кэша браузера (событие pageshow с '
         'persisted=true) вызывается облегчённая функция reinit(), которая обновляет '
         'отображение без повторной привязки обработчиков.')
    body('Функция filterClients() применяет текущий фильтр статуса и строку поиска. '
         'Поиск выполняется по полям fullName, email и phone с использованием метода '
         'String.includes() после приведения к нижнему регистру.')
    pagebreak()


def build_section4():
    section('4', 'РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ')

    paragraph_heading('4.1', 'Требования к запуску и установке')
    body('NexusCRM не требует установки программного обеспечения, настройки серверного '
         'окружения или постоянного подключения к интернету. Данные хранятся локально.')
    body('Минимальные системные требования:')
    li('современный веб-браузер с поддержкой ES-модулей (type="module") и Web Storage API;')
    li('операционная система: Windows 10+, macOS 10.14+, Linux (любой актуальный дистрибутив);')
    li('минимальная версия браузера: Google Chrome 80+, Mozilla Firefox 80+, '
       'Microsoft Edge 80+, Safari 14+.')
    body('Порядок запуска приложения:')
    numbered_li(1, 'Скачать или клонировать репозиторий проекта на локальный диск.')
    numbered_li(2, 'Открыть файл index.html в поддерживаемом веб-браузере.')
    numbered_li(3, 'При первом запуске хранилище автоматически заполнится шестью '
                   'демонстрационными записями клиентов.')
    body('В некоторых конфигурациях браузера при открытии файла по протоколу file:// '
         'ES-модули могут быть заблокированы политикой CORS. В этом случае '
         'рекомендуется запустить локальный HTTP-сервер командой '
         'python -m http.server 8000 в директории проекта, '
         'после чего открыть адрес http://localhost:8000 в браузере.')

    paragraph_heading('4.2', 'Основные сценарии использования')
    body('Ниже описаны основные сценарии работы с приложением NexusCRM.')
    body('Сценарий 1. Просмотр базы клиентов. '
         'Пользователь открывает index.html. При первом запуске загружаются '
         'шесть демо-записей. Отображается сетка карточек с двумя счётчиками.')
    body('Сценарий 2. Добавление нового клиента. '
         'Пользователь нажимает «Добавить клиента», заполняет форму '
         '(имя, телефон и email обязательны), нажимает «Сохранить клиента». '
         'После сохранения — уведомление-тост и возврат на главную страницу.')
    body('Сценарий 3. Поиск и фильтрация клиентов. '
         'Пользователь вводит текст в поле поиска (по имени, email или телефону, '
         'задержка 280 мс) и/или выбирает фильтр статуса. '
         'Оба условия применяются одновременно.')
    body('Сценарий 4. Изменение статуса клиента. '
         'В карточке клиента пользователь выбирает новый статус из выпадающего списка. '
         'Изменение немедленно сохраняется в localStorage. '
         'Значок статуса в карточке обновляется без перезагрузки.')
    body('Сценарий 5. Редактирование данных клиента. '
         'Пользователь нажимает кнопку редактирования (иконка карандаша). '
         'Открывается form.html с параметром ?edit=<id>. '
         'Форма заполняется текущими данными. После сохранения — обновление в localStorage.')
    body('Сценарий 6. Удаление клиента. '
         'Пользователь нажимает кнопку удаления (иконка корзины). '
         'Отображается диалог подтверждения. '
         'После подтверждения — удаление с анимацией и уведомление-тост.')
    body('Сценарий 7. Просмотр статистики. '
         'На странице stats.html отображаются: пять KPI-карточек, разбивка по статусам '
         'с прогресс-барами и гистограмма активности за последние шесть месяцев.')

    paragraph_heading('4.3', 'Ограничения и перспективы развития')
    body('К текущим ограничениям системы относятся следующие:')
    li('данные хранятся только в localStorage конкретного браузера и не синхронизируются;')
    li('объём хранимых данных ограничен квотой localStorage (5–10 МБ);')
    li('отсутствует разграничение прав доступа пользователей;')
    li('система не поддерживает экспорт данных в форматы CSV и XLSX;')
    li('аналитический модуль не поддерживает произвольный выбор периода наблюдения.')

    body('В качестве перспектив развития проекта авторами проекта предлагаются:')
    li('реализация синхронизации данных через Firebase Realtime Database или Supabase;')
    li('добавление экспорта клиентской базы в форматы CSV и XLSX;')
    li('разработка серверной части на Node.js или Python для многопользовательского режима;')
    li('реализация режима Progressive Web App (PWA);')
    li('добавление системы тегов, расширенных полей профиля и напоминаний.')
    pagebreak()


def build_conclusion():
    structural('ЗАКЛЮЧЕНИЕ')
    body('В ходе настоящей проектной работы было разработано клиентское веб-приложение '
         'NexusCRM — система управления базой клиентов для малого бизнеса, реализованная '
         'на нативных технологиях HTML5, CSS3 и JavaScript с применением ES-модулей.')
    body('В процессе работы были решены все поставленные задачи: проведён анализ '
         'предметной области и существующих CRM-решений, спроектирована и реализована '
         'многостраничная архитектура приложения, разработан слой хранения данных на '
         'основе Web Storage API, создан адаптивный пользовательский интерфейс с тёмной '
         'цветовой схемой, реализованы все операции управления клиентскими данными, '
         'а также модуль статистики и аналитики.')
    body('Разработанное приложение обладает следующими достоинствами: полная '
         'независимость от серверной инфраструктуры и интернет-соединения, отсутствие '
         'зависимостей от сторонних библиотек, поддержка мобильных устройств, '
         'защита от XSS-атак, автоматическое восстановление данных при повреждении '
         'хранилища, а также поддержка кэширования страниц браузером (bfcache).')
    body('Практическая значимость проекта определяется его готовностью к применению '
         'в реальных условиях малого бизнеса без дополнительных затрат на инфраструктуру.')
    body('Перспективы развития проекта связаны с добавлением серверной части, облачной '
         'синхронизацией данных, функциональностью экспорта и расширенными '
         'аналитическими инструментами.')
    pagebreak()


def build_references():
    structural('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ')
    refs = [
        'Buttle F., Maklan S. (2019). Customer Relationship Management: Concepts and Technologies. '
        'Routledge. 448 p.',
        'MDN Web Docs. (2024). Using the Web Storage API. Mozilla. '
        'https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API',
        'Salesforce Research. (2022). State of Sales Report (5th ed.). Salesforce. '
        'https://www.salesforce.com/resources/research-reports/state-of-sales/',
        'MDN Web Docs. (2024). JavaScript modules. Mozilla. '
        'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules',
        'MDN Web Docs. (2024). Window.localStorage. Mozilla. '
        'https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage',
        'OWASP. (2024). Cross Site Scripting (XSS). OWASP Foundation. '
        'https://owasp.org/www-community/attacks/xss/',
        'Simpson K. (2020). You Don\'t Know JS Yet: Get Started. Independently published. 143 p.',
        'Frain B. (2022). Responsive Web Design with HTML5 and CSS. Packt Publishing. 476 p.',
        'MDN Web Docs. (2024). Page lifecycle API: bfcache. Mozilla. '
        'https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/bfcache',
        'Google Developers. (2024). Google Fonts API v1. Google. '
        'https://developers.google.com/fonts/docs/getting_started',
    ]
    for i, ref in enumerate(refs, 1):
        story.append(P(f'{i}&nbsp;&nbsp;{ref}', sBody))
    pagebreak()


def build_appendices():
    # Приложение 1
    story.append(P('Приложение 1', sRight))
    blank()
    story.append(P('<b>Полная файловая структура проекта NexusCRM</b>', sCenter))
    blank()
    tree_lines = [
        'meneger/',
        '├── about.html',
        '├── css/',
        '│   └── style.css',
        '├── docs/',
        '│   ├── generate_doc.py',
        '│   ├── make_pdf.py',
        '│   ├── NexusCRM_Documentation.docx',
        '│   └── NexusCRM_Documentation.pdf',
        '├── form.html',
        '├── index.html',
        '├── js/',
        '│   ├── form.js',
        '│   ├── main.js',
        '│   ├── stats.js',
        '│   ├── storage.js',
        '│   └── utils.js',
        '├── README.md',
        '└── stats.html',
    ]
    for line in tree_lines:
        story.append(P(line, ParagraphStyle(
            'Code', fontName='Courier', fontSize=9, leading=11,
            firstLineIndent=0, alignment=TA_LEFT)))
    pagebreak()

    # Приложение 2
    story.append(P('Приложение 2', sRight))
    blank()
    story.append(P('<b>Схема зависимостей JavaScript-модулей</b>', sCenter))
    blank()
    story.append(fig_modules())
    blank()
    story.append(P('Примечание – составлено автором на основании проведённого исследования',
                   sCapNote))


# ══════════════════════════════════════════════════════════════════════════════
# СБОРКА PDF
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print('[1/3] Генерация содержимого...')
    build_title()
    build_toc()
    build_introduction()
    build_section1()
    build_section2()
    build_section3()
    build_section4()
    build_conclusion()
    build_references()
    build_appendices()

    print(f'[2/3] Создание PDF -> {OUT_PDF}')

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        topMargin=MAR_T,
        bottomMargin=MAR_B,
        leftMargin=MAR_L,
        rightMargin=MAR_R,
        title='Проектная работа: NexusCRM',
        author='Шафиев Артём, группа 13 ТИС',
        subject='Разработка веб-приложения NexusCRM',
    )

    # Нижний колонтитул с номером страницы
    page_num_counter = [0]

    def on_page(canvas, doc):
        page_num_counter[0] += 1
        page = page_num_counter[0]
        if page <= 1:
            return  # Титул без номера
        canvas.saveState()
        canvas.setFont('TNR', 10)
        canvas.drawCentredString(PAGE_W / 2, MAR_B - 1.0 * cm, str(page))
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    print(f'[3/3] OK: {OUT_PDF}')
    print('\nГотово! PDF создан.')


if __name__ == '__main__':
    main()
