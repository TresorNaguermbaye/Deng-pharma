"""
Génère automatiquement la présentation PowerPoint de soutenance DENG PHARMA
Charte graphique : cyan #0ABAB5 + bleu foncé #0F1A2C
"""
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "presentation"
OUTPUT_DIR.mkdir(exist_ok=True)

PLOTS_DIR = Path(__file__).resolve().parent.parent / "plots"

# Couleurs DENG PHARMA
CYAN = RGBColor(0x0A, 0xBA, 0xB5)
DARK = RGBColor(0x0F, 0x1A, 0x2C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF3, 0xF4, 0xF6)
DANGER = RGBColor(0xFF, 0x6B, 0x6B)
SUCCESS = RGBColor(0x10, 0xB9, 0x81)
WARNING = RGBColor(0xF5, 0x9E, 0x0B)
INFO = RGBColor(0x3B, 0x82, 0xF6)
TEXT_GRAY = RGBColor(0x6B, 0x72, 0x80)

# Dimensions 16:9
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

print("=" * 60)
print("🎨 Génération de la présentation DENG PHARMA")
print("=" * 60)

# ==========================================
# CRÉATION DU PPTX
# ==========================================
prs = Presentation()
prs.slide_width = SLIDE_WIDTH
prs.slide_height = SLIDE_HEIGHT

BLANK_LAYOUT = prs.slide_layouts[6]  # Layout vide


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def add_background(slide, color=DARK):
    """Ajoute un fond coloré à toute la slide."""
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg


def add_gradient_background(slide, color1=CYAN, color2=DARK):
    """Fond dégradé simulé avec 2 rectangles."""
    # Simuler un dégradé avec plusieurs bandes
    steps = 30
    for i in range(steps):
        ratio = i / steps
        r = int(color1[0] + (color2[0] - color1[0]) * ratio) if isinstance(color1, tuple) else color1[0]
        g = int(color1[1] + (color2[1] - color1[1]) * ratio) if isinstance(color1, tuple) else color1[1]
        b = int(color1[2] + (color2[2] - color1[2]) * ratio) if isinstance(color1, tuple) else color1[2]
        band = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Emu(int(SLIDE_HEIGHT * i / steps)),
            SLIDE_WIDTH, Emu(int(SLIDE_HEIGHT / steps) + 1)
        )
        band.fill.solid()
        band.fill.fore_color.rgb = RGBColor(r, g, b)
        band.line.fill.background()


def add_text(slide, text, left, top, width, height,
             font_size=18, bold=False, color=WHITE,
             align=PP_ALIGN.LEFT, font_name="Calibri", italic=False):
    """Ajoute du texte formaté."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)

    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font_name
    run.font.italic = italic
    return tb


def add_multiline_text(slide, lines, left, top, width, height,
                       font_size=14, color=WHITE, spacing=1.5):
    """Ajoute plusieurs lignes de texte."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True

    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(font_size * spacing * 0.3)

        # Détecter gras avec **
        if '**' in line:
            parts = line.split('**')
            for j, part in enumerate(parts):
                if not part:
                    continue
                run = p.add_run()
                run.text = part
                run.font.size = Pt(font_size)
                run.font.bold = (j % 2 == 1)
                run.font.color.rgb = color
                run.font.name = "Calibri"
        else:
            run = p.add_run()
            run.text = line
            run.font.size = Pt(font_size)
            run.font.color.rgb = color
            run.font.name = "Calibri"
    return tb


def add_colored_box(slide, left, top, width, height,
                    color=CYAN, text="", font_size=14,
                    text_color=WHITE, rounded=True):
    """Ajoute un rectangle coloré avec texte."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()

    if text:
        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.15)
        tf.margin_right = Inches(0.15)
        tf.margin_top = Inches(0.1)
        tf.margin_bottom = Inches(0.1)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = text
        run.font.size = Pt(font_size)
        run.font.color.rgb = text_color
        run.font.bold = True
        run.font.name = "Calibri"
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return shape


def add_kpi_card(slide, left, top, width, height,
                 value, label, color=CYAN, value_size=48):
    """Ajoute une carte KPI (valeur + label)."""
    # Carte de fond
    card = add_colored_box(slide, left, top, width, height,
                           color=RGBColor(0xFF, 0xFF, 0xFF),
                           rounded=True)
    card.fill.fore_color.rgb = WHITE

    # Valeur
    add_text(slide, value,
             left, top + Inches(0.1), width, Inches(0.9),
             font_size=value_size, bold=True, color=color,
             align=PP_ALIGN.CENTER)

    # Label
    add_text(slide, label,
             left, top + Inches(1.0), width, Inches(0.4),
             font_size=12, bold=False, color=TEXT_GRAY,
             align=PP_ALIGN.CENTER)


def add_top_accent(slide, text, subtitle=""):
    """Barre d'accent en haut + titre + sous-titre."""
    # Barre cyan horizontale
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, Inches(0.08)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()

    # Titre
    add_text(slide, text,
             Inches(0.5), Inches(0.3),
             SLIDE_WIDTH - Inches(1), Inches(0.7),
             font_size=28, bold=True, color=DARK,
             align=PP_ALIGN.LEFT)

    if subtitle:
        add_text(slide, subtitle,
                 Inches(0.5), Inches(1.0),
                 SLIDE_WIDTH - Inches(1), Inches(0.4),
                 font_size=13, color=TEXT_GRAY,
                 align=PP_ALIGN.LEFT, italic=True)


def add_footer(slide, page_num, total_pages=18):
    """Ajoute le pied de page."""
    add_text(slide, "DENG PHARMA — Soutenance PFE 2025-2026",
             Inches(0.5), SLIDE_HEIGHT - Inches(0.4),
             Inches(6), Inches(0.3),
             font_size=9, color=TEXT_GRAY)
    add_text(slide, f"{page_num} / {total_pages}",
             SLIDE_WIDTH - Inches(1.5), SLIDE_HEIGHT - Inches(0.4),
             Inches(1), Inches(0.3),
             font_size=9, color=TEXT_GRAY,
             align=PP_ALIGN.RIGHT)


# ==========================================
# SLIDE 1 — PAGE DE GARDE
# ==========================================
print("📄 Slide 1/18 — Page de garde")
slide = prs.slides.add_slide(BLANK_LAYOUT)

# Fond bleu foncé
add_background(slide, DARK)

# Bande cyan à gauche
accent = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.3), SLIDE_HEIGHT
)
accent.fill.solid()
accent.fill.fore_color.rgb = CYAN
accent.line.fill.background()

# Logo DENG PHARMA (cercle stylisé)
logo_circle = slide.shapes.add_shape(
    MSO_SHAPE.OVAL, Inches(0.7), Inches(0.6), Inches(1), Inches(1)
)
logo_circle.fill.solid()
logo_circle.fill.fore_color.rgb = CYAN
logo_circle.line.fill.background()
add_text(slide, "D", Inches(0.7), Inches(0.75), Inches(1), Inches(0.7),
         font_size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_text(slide, "DENG PHARMA",
         Inches(1.9), Inches(0.75), Inches(4), Inches(0.5),
         font_size=24, bold=True, color=WHITE)
add_text(slide, "Système intelligent de gestion pharmaceutique",
         Inches(1.9), Inches(1.2), Inches(6), Inches(0.4),
         font_size=12, color=CYAN)

# Titre principal
add_text(slide, "CONCEPTION ET DÉVELOPPEMENT D'UN",
         Inches(0.7), Inches(2.3), SLIDE_WIDTH - Inches(1.4), Inches(0.5),
         font_size=20, bold=False, color=WHITE)
add_text(slide, "SYSTÈME INTELLIGENT D'AIDE À LA DÉCISION",
         Inches(0.7), Inches(2.75), SLIDE_WIDTH - Inches(1.4), Inches(0.7),
         font_size=28, bold=True, color=CYAN)
add_text(slide, "POUR L'OPTIMISATION DES STOCKS PHARMACEUTIQUES",
         Inches(0.7), Inches(3.5), SLIDE_WIDTH - Inches(1.4), Inches(0.6),
         font_size=22, bold=True, color=WHITE)
add_text(slide, "BASÉ SUR LE MACHINE LEARNING",
         Inches(0.7), Inches(4.1), SLIDE_WIDTH - Inches(1.4), Inches(0.5),
         font_size=16, bold=False, color=WHITE)

# Ligne séparatrice
line = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(4.85), Inches(4), Inches(0.03)
)
line.fill.solid()
line.fill.fore_color.rgb = CYAN
line.line.fill.background()

# Informations
add_text(slide, "Présenté par :", Inches(0.7), Inches(5.1), Inches(3), Inches(0.3),
         font_size=11, color=CYAN, italic=True)
add_text(slide, "NAGUERMBAYE TRESOR", Inches(0.7), Inches(5.4), Inches(4), Inches(0.4),
         font_size=16, bold=True, color=WHITE)

add_text(slide, "Sous la direction de :", Inches(6.5), Inches(5.1), Inches(3), Inches(0.3),
         font_size=11, color=CYAN, italic=True)
add_text(slide, "M. BRAHIM ISSA HASSABALAH", Inches(6.5), Inches(5.4), Inches(5), Inches(0.4),
         font_size=14, bold=True, color=WHITE)

# Pied
add_text(slide, "ENASTIC  •  Année universitaire 2025-2026",
         Inches(0.7), Inches(6.3), Inches(6), Inches(0.3),
         font_size=11, color=WHITE)
add_text(slide, "Licence en Informatique",
         Inches(0.7), Inches(6.6), Inches(6), Inches(0.3),
         font_size=10, color=TEXT_GRAY, italic=True)


# ==========================================
# SLIDE 2 — PLAN
# ==========================================
print("📄 Slide 2/18 — Plan")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Plan de la présentation", "6 parties — 15 minutes")

# Grille 2x3
items = [
    ("❶", "CONTEXTE & PROBLÉMATIQUE", "Enjeu de santé publique au Tchad", CYAN),
    ("❷", "SOLUTION PROPOSÉE", "Architecture et technologies", INFO),
    ("❸", "DÉMONSTRATION LIVE", "Application en direct", DANGER),
    ("❹", "RÉSULTATS EXPÉRIMENTAUX", "Performance du modèle ML", SUCCESS),
    ("❺", "LIMITES & PERSPECTIVES", "Analyse critique", WARNING),
    ("❻", "CONCLUSION", "Bilan et impact", DARK),
]

card_w = Inches(3.9)
card_h = Inches(2.2)
start_x = Inches(0.6)
start_y = Inches(1.7)
gap_x = Inches(0.3)
gap_y = Inches(0.3)

for i, (num, title, sub, color) in enumerate(items):
    row = i // 3
    col = i % 3
    x = start_x + col * (card_w + gap_x)
    y = start_y + row * (card_h + gap_y)

    # Carte
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2)

    # Bande gauche colorée
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, x, y + Inches(0.5), Inches(0.1), card_h - Inches(1)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = color
    band.line.fill.background()

    # Numéro
    add_text(slide, num, x + Inches(0.2), y + Inches(0.15), card_w, Inches(0.5),
             font_size=26, bold=True, color=color, align=PP_ALIGN.LEFT)

    # Titre
    add_text(slide, title, x + Inches(0.2), y + Inches(0.75), card_w - Inches(0.3), Inches(0.5),
             font_size=14, bold=True, color=DARK, align=PP_ALIGN.LEFT)

    # Sous-titre
    add_text(slide, sub, x + Inches(0.2), y + Inches(1.3), card_w - Inches(0.3), Inches(0.6),
             font_size=11, color=TEXT_GRAY, align=PP_ALIGN.LEFT, italic=True)

add_footer(slide, 2)


# ==========================================
# SLIDE 3 — CONTEXTE (problème)
# ==========================================
print("📄 Slide 3/18 — Contexte")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Le problème au Tchad",
               "Disponibilité des médicaments essentiels — Rapport OMS/MSP 2023")

# 2 grandes cartes KPI
add_kpi_card(slide, Inches(0.8), Inches(1.9), Inches(3.5), Inches(1.7),
             "52,6%", "Secteur public", CYAN, value_size=54)
add_kpi_card(slide, Inches(4.8), Inches(1.9), Inches(3.5), Inches(1.7),
             "48%", "Pharmacies privées", DANGER, value_size=54)

# Encadré d'alerte
alert_box = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9), Inches(1.9), Inches(3.7), Inches(1.7)
)
alert_box.fill.solid()
alert_box.fill.fore_color.rgb = RGBColor(0xFE, 0xF3, 0xC7)
alert_box.line.color.rgb = WARNING
alert_box.line.width = Pt(1.5)

add_text(slide, "⚠️", Inches(9.2), Inches(2.0), Inches(0.6), Inches(0.5),
         font_size=28, color=WARNING, align=PP_ALIGN.LEFT)
add_text(slide, "Sur 10 médicaments", Inches(9.9), Inches(2.05), Inches(2.6), Inches(0.4),
         font_size=13, bold=True, color=DARK)
add_text(slide, "essentiels, seulement", Inches(9.9), Inches(2.4), Inches(2.6), Inches(0.4),
         font_size=12, color=DARK)
add_text(slide, "5 sont disponibles", Inches(9.9), Inches(2.75), Inches(2.6), Inches(0.4),
         font_size=14, bold=True, color=DANGER)
add_text(slide, "soit 1 patient sur 2 pénalisé", Inches(9.9), Inches(3.1), Inches(2.6), Inches(0.4),
         font_size=10, color=TEXT_GRAY, italic=True)

# Section causes
add_text(slide, "CAUSES PRINCIPALES",
         Inches(0.8), Inches(4.0), Inches(6), Inches(0.4),
         font_size=16, bold=True, color=DARK)

causes = [
    ("🌍", "Circuits d'approvisionnement", "instables"),
    ("⏱️", "Délais de livraison", "très longs"),
    ("📦", "Capacité de stockage", "limitée"),
    ("📊", "Gestion empirique", "non automatisée"),
]

cause_w = Inches(2.9)
cause_h = Inches(1.7)
for i, (icon, title, sub) in enumerate(causes):
    x = Inches(0.8) + i * (cause_w + Inches(0.15))
    y = Inches(4.5)

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, cause_w, cause_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = LIGHT_GRAY
    card.line.fill.background()

    add_text(slide, icon, x, y + Inches(0.15), cause_w, Inches(0.6),
             font_size=32, color=DARK, align=PP_ALIGN.CENTER)
    add_text(slide, title, x + Inches(0.1), y + Inches(0.85), cause_w - Inches(0.2), Inches(0.4),
             font_size=11, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    add_text(slide, sub, x + Inches(0.1), y + Inches(1.2), cause_w - Inches(0.2), Inches(0.4),
             font_size=10, color=TEXT_GRAY, align=PP_ALIGN.CENTER)

add_footer(slide, 3)


# ==========================================
# SLIDE 4 — PROBLÉMATIQUE & OBJECTIFS
# ==========================================
print("📄 Slide 4/18 — Problématique")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Problématique & Objectifs")

# Encadré problématique
prob_box = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.5)
)
prob_box.fill.solid()
prob_box.fill.fore_color.rgb = DARK
prob_box.line.fill.background()

add_text(slide, "❓  PROBLÉMATIQUE",
         Inches(1), Inches(1.85), Inches(5), Inches(0.4),
         font_size=13, bold=True, color=CYAN)

add_text(slide, "Comment exploiter le Machine Learning pour optimiser\nles stocks pharmaceutiques au Tchad ?",
         Inches(1), Inches(2.25), Inches(11), Inches(0.9),
         font_size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# 4 objectifs
add_text(slide, "4 OBJECTIFS SPÉCIFIQUES",
         Inches(0.8), Inches(3.6), Inches(6), Inches(0.4),
         font_size=16, bold=True, color=DARK)

objectifs = [
    ("📉", "Réduire", "les pertes économiques\nliées au surstockage", DANGER),
    ("💊", "Garantir", "la disponibilité\ndes médicaments", CYAN),
    ("🎯", "Recommander", "les quantités optimales\nà commander", INFO),
    ("📱", "Développer", "une application de\nvisualisation", SUCCESS),
]

obj_w = Inches(2.9)
obj_h = Inches(2.2)
for i, (icon, title, sub, color) in enumerate(objectifs):
    x = Inches(0.8) + i * (obj_w + Inches(0.15))
    y = Inches(4.1)

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, obj_w, obj_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2)

    # Cercle avec icône
    circle = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, x + Inches(1.15), y + Inches(0.2), Inches(0.7), Inches(0.7)
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()

    add_text(slide, icon, x + Inches(1.15), y + Inches(0.28), Inches(0.7), Inches(0.55),
             font_size=22, color=WHITE, align=PP_ALIGN.CENTER)

    add_text(slide, title, x + Inches(0.1), y + Inches(1.05), obj_w - Inches(0.2), Inches(0.4),
             font_size=14, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    add_text(slide, sub, x + Inches(0.1), y + Inches(1.45), obj_w - Inches(0.2), Inches(0.7),
             font_size=10, color=TEXT_GRAY, align=PP_ALIGN.CENTER)

add_footer(slide, 4)


# ==========================================
# SLIDE 5 — ÉTAT DE L'ART
# ==========================================
print("📄 Slide 5/18 — État de l'art")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Comparaison des solutions existantes",
               "Aucune solution ne couvre tous les besoins identifiés")

# Tableau
rows = [
    ["Critère", "Odoo", "SAP S/4", "NetSuite", "DENG PHARMA"],
    ["Gestion des stocks", "✓", "✓", "✓", "✓"],
    ["Gestion des ventes", "✓", "✓", "✓", "✓"],
    ["Prévision IA", "✗", "~", "~", "✓"],
    ["Détection ruptures", "~", "✓", "~", "✓"],
    ["Score de criticité", "✗", "✗", "✗", "✓"],
    ["Recommandation auto", "✗", "✗", "✗", "✓"],
    ["Adapté au Tchad", "✗", "✗", "✗", "✓"],
]

table_shape = slide.shapes.add_table(
    len(rows), 5,
    Inches(0.8), Inches(1.9),
    Inches(11.7), Inches(4.3)
)
table = table_shape.table

# Largeurs colonnes
table.columns[0].width = Inches(3.3)
table.columns[1].width = Inches(2.1)
table.columns[2].width = Inches(2.1)
table.columns[3].width = Inches(2.1)
table.columns[4].width = Inches(2.1)

# Remplir
for i, row in enumerate(rows):
    for j, val in enumerate(row):
        cell = table.cell(i, j)
        cell.text = val

        # Style
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            for run in p.runs:
                run.font.size = Pt(12)
                run.font.name = "Calibri"

                if i == 0:
                    run.font.bold = True
                    run.font.color.rgb = WHITE
                elif j == 4:
                    run.font.bold = True
                    run.font.color.rgb = CYAN
                else:
                    run.font.color.rgb = DARK

        # Fond
        if i == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = DARK
        elif j == 4:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xE0, 0xF7, 0xF6)
        else:
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 1 else LIGHT_GRAY

add_footer(slide, 5)


# ==========================================
# SLIDE 6 — ARCHITECTURE
# ==========================================
print("📄 Slide 6/18 — Architecture")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Architecture du système",
               "Microservices • Séparation des responsabilités")

# Blocs architecture
layers = [
    ("🎨  FRONTEND", "Next.js + React + Tailwind CSS", INFO, "Interface utilisateur moderne"),
    ("⚙️  BACKEND", "Django + DRF", DARK, "Logique métier & API REST"),
    ("🤖  SERVICE IA", "FastAPI + XGBoost", CYAN, "Prédictions & recommandations"),
    ("💾  DONNÉES", "PostgreSQL + Redis", SUCCESS, "Persistance & cache"),
    ("⏱️  ASYNCHRONE", "Celery + Redis", WARNING, "Traitements en arrière-plan"),
]

y = Inches(1.9)
for i, (title, tech, color, desc) in enumerate(layers):
    # Carte
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.8), y, Inches(11.7), Inches(0.85)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2)

    # Bande gauche
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), y, Inches(0.15), Inches(0.85)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = color
    band.line.fill.background()

    add_text(slide, title, Inches(1.15), y + Inches(0.1), Inches(3.5), Inches(0.35),
             font_size=14, bold=True, color=color)
    add_text(slide, tech, Inches(1.15), y + Inches(0.45), Inches(4), Inches(0.35),
             font_size=11, color=DARK)
    add_text(slide, desc, Inches(5.5), y + Inches(0.25), Inches(6.8), Inches(0.4),
             font_size=11, color=TEXT_GRAY, italic=True)

    y += Inches(0.95)

add_footer(slide, 6)


# ==========================================
# SLIDE 7 — MODÈLE ML
# ==========================================
print("📄 Slide 7/18 — Modèle ML")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Choix du modèle de Machine Learning",
               "Comparaison de 4 algorithmes")

# 4 cartes modèles
models = [
    ("📈", "Régression\nLinéaire", "Simple, baseline", "Linéaire uniquement", DANGER),
    ("🌲", "Random\nForest", "Robuste, non-linéaire", "Lourd, boîte noire", WARNING),
    ("🏆", "XGBoost", "Précis (R²>0.95), rapide", "Standard de l'industrie", CYAN),
    ("📊", "Prophet", "Saisonnalité auto", "Séries temporelles", INFO),
]

card_w = Inches(2.9)
card_h = Inches(3.5)
for i, (icon, name, pro, con, color) in enumerate(models):
    x = Inches(0.8) + i * (card_w + Inches(0.15))
    y = Inches(1.9)

    # Carte
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2.5) if name == "XGBoost" else Pt(1.5)

    # Icône
    add_text(slide, icon, x, y + Inches(0.2), card_w, Inches(0.8),
             font_size=44, color=color, align=PP_ALIGN.CENTER)

    # Nom
    add_text(slide, name, x + Inches(0.1), y + Inches(1.0), card_w - Inches(0.2), Inches(0.8),
             font_size=16, bold=True, color=DARK, align=PP_ALIGN.CENTER)

    # Avantage
    add_text(slide, "✅ " + pro, x + Inches(0.15), y + Inches(1.9), card_w - Inches(0.3), Inches(0.5),
             font_size=10, color=SUCCESS, align=PP_ALIGN.CENTER)

    # Limite
    add_text(slide, "⚠️ " + con, x + Inches(0.15), y + Inches(2.4), card_w - Inches(0.3), Inches(0.5),
             font_size=10, color=DANGER, align=PP_ALIGN.CENTER)

    # Badge "CHOIX" pour XGBoost
    if name == "XGBoost":
        badge = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            x + Inches(0.7), y + Inches(2.9), Inches(1.5), Inches(0.35)
        )
        badge.fill.solid()
        badge.fill.fore_color.rgb = CYAN
        badge.line.fill.background()
        add_text(slide, "CHOIX RETENU", x + Inches(0.7), y + Inches(2.95), Inches(1.5), Inches(0.3),
                 font_size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_footer(slide, 7)


# ==========================================
# SLIDE 8 — DATASET
# ==========================================
print("📄 Slide 8/18 — Dataset")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Dataset et entraînement",
               "Pipeline MLOps complet")

# 3 KPI cards
add_kpi_card(slide, Inches(0.8), Inches(1.9), Inches(3.9), Inches(1.5),
             "10 950", "lignes de données", CYAN, value_size=48)
add_kpi_card(slide, Inches(4.85), Inches(1.9), Inches(3.9), Inches(1.5),
             "15", "médicaments", INFO, value_size=48)
add_kpi_card(slide, Inches(8.9), Inches(1.9), Inches(3.6), Inches(1.5),
             "2 ans", "de période", SUCCESS, value_size=48)

# Features section
add_text(slide, "32 FEATURES ENGINEERÉES",
         Inches(0.8), Inches(3.7), Inches(6), Inches(0.4),
         font_size=15, bold=True, color=DARK)

features = [
    "Lags (1, 2, 3, ..., 30 jours)",
    "Rolling stats (moyennes, écart-types)",
    "Saisonnalité Tchad (saison des pluies)",
    "Contexte métier (prix, criticité, stock)",
]

y = Inches(4.2)
for f in features:
    add_text(slide, "•  " + f, Inches(1.0), y, Inches(5.5), Inches(0.35),
             font_size=12, color=DARK)
    y += Inches(0.4)

# Split diagram
add_text(slide, "SPLIT 70 / 15 / 15",
         Inches(7), Inches(3.7), Inches(5), Inches(0.4),
         font_size=15, bold=True, color=DARK)

# Barre de split
split_bar = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(7.2), Inches(4.2), Inches(5.5), Inches(0.6)
)
split_bar.fill.solid()
split_bar.fill.fore_color.rgb = LIGHT_GRAY
split_bar.line.fill.background()

# 3 segments
seg1 = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(7.2), Inches(4.2), Inches(3.85), Inches(0.6)
)
seg1.fill.solid()
seg1.fill.fore_color.rgb = CYAN
seg1.line.fill.background()
add_text(slide, "TRAIN 70%", Inches(7.2), Inches(4.3), Inches(3.85), Inches(0.4),
         font_size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

seg2 = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(11.05), Inches(4.2), Inches(0.825), Inches(0.6)
)
seg2.fill.solid()
seg2.fill.fore_color.rgb = INFO
seg2.line.fill.background()
add_text(slide, "VAL\n15%", Inches(11.05), Inches(4.28), Inches(0.825), Inches(0.5),
         font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

seg3 = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(11.875), Inches(4.2), Inches(0.825), Inches(0.6)
)
seg3.fill.solid()
seg3.fill.fore_color.rgb = DANGER
seg3.line.fill.background()
add_text(slide, "TEST\n15%", Inches(11.875), Inches(4.28), Inches(0.825), Inches(0.5),
         font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Optuna
optuna_box = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(0.8), Inches(5.7), Inches(11.7), Inches(0.8)
)
optuna_box.fill.solid()
optuna_box.fill.fore_color.rgb = RGBColor(0xFF, 0xF4, 0xE1)
optuna_box.line.color.rgb = WARNING
optuna_box.line.width = Pt(1.5)
add_text(slide, "🎯  Optimisation Optuna : 30 trials hyperparamètres",
         Inches(1), Inches(5.9), Inches(11.5), Inches(0.4),
         font_size=13, bold=True, color=DARK, align=PP_ALIGN.CENTER)

add_footer(slide, 8)


# ==========================================
# SLIDE 9 — DÉMO LIVE
# ==========================================
print("📄 Slide 9/18 — Démo live")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, DARK)

# Bande déco
for i in range(3):
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(i * 4.44), 0, Inches(4.44), Inches(0.1)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = [CYAN, INFO, DANGER][i]
    band.line.fill.background()

add_text(slide, "🎬", Inches(5.5), Inches(1.5), Inches(2.3), Inches(1.5),
         font_size=120, color=CYAN, align=PP_ALIGN.CENTER)

add_text(slide, "DÉMONSTRATION EN DIRECT",
         Inches(0), Inches(3.2), SLIDE_WIDTH, Inches(1),
         font_size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_text(slide, "Application DENG PHARMA",
         Inches(0), Inches(4.2), SLIDE_WIDTH, Inches(0.5),
         font_size=20, color=CYAN, align=PP_ALIGN.CENTER)

# Bloc URL
url_box = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(4), Inches(5.2), Inches(5.3), Inches(0.9)
)
url_box.fill.solid()
url_box.fill.fore_color.rgb = RGBColor(0x1A, 0x2A, 0x3C)
url_box.line.color.rgb = CYAN
url_box.line.width = Pt(1)

add_text(slide, "→  http://localhost:3000",
         Inches(4.2), Inches(5.35), Inches(5), Inches(0.4),
         font_size=14, bold=True, color=CYAN, align=PP_ALIGN.CENTER)
add_text(slide, "Login : admin  •  Mot de passe : ••••••••",
         Inches(4.2), Inches(5.75), Inches(5), Inches(0.3),
         font_size=11, color=WHITE, align=PP_ALIGN.CENTER)

add_footer(slide, 9)


# ==========================================
# SLIDE 10 — RÉSULTATS (KPI + Figure 1)
# ==========================================
print("📄 Slide 10/18 — Résultats")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Performances du modèle XGBoost",
               "Évaluation sur 1 590 observations du jeu de test")

# 4 KPI cards
add_kpi_card(slide, Inches(0.4), Inches(1.8), Inches(3.05), Inches(1.4),
             "0,959", "R²", CYAN, value_size=42)
add_kpi_card(slide, Inches(3.6), Inches(1.8), Inches(3.05), Inches(1.4),
             "7,55", "MAE (unités)", INFO, value_size=42)
add_kpi_card(slide, Inches(6.8), Inches(1.8), Inches(3.05), Inches(1.4),
             "19,22", "RMSE (unités)", WARNING, value_size=42)
add_kpi_card(slide, Inches(10.0), Inches(1.8), Inches(3.05), Inches(1.4),
             "12,25%", "MAPE", DANGER, value_size=42)

# Insérer Figure 1 si elle existe
fig1_path = PLOTS_DIR / "01_reel_vs_predit_global.png"
if fig1_path.exists():
    slide.shapes.add_picture(
        str(fig1_path),
        Inches(0.5), Inches(3.4),
        width=Inches(12.3)
    )
else:
    # Placeholder
    placeholder = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.5), Inches(3.4), Inches(12.3), Inches(3.7)
    )
    placeholder.fill.solid()
    placeholder.fill.fore_color.rgb = LIGHT_GRAY
    placeholder.line.color.rgb = TEXT_GRAY
    add_text(slide, "[Insérer ici : Figure 1 — Réel vs Prédit]",
             Inches(0.5), Inches(5.1), Inches(12.3), Inches(0.5),
             font_size=16, color=TEXT_GRAY, align=PP_ALIGN.CENTER)

add_footer(slide, 10)


# ==========================================
# SLIDE 11 — ANALYSE DES ERREURS
# ==========================================
print("📄 Slide 11/18 — Analyse des erreurs")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Analyse des erreurs de prédiction")

# Insérer Figure 5
fig5_path = PLOTS_DIR / "05_distribution_erreurs.png"
if fig5_path.exists():
    slide.shapes.add_picture(
        str(fig5_path),
        Inches(0.5), Inches(1.7),
        width=Inches(12.3)
    )
else:
    placeholder = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.5), Inches(1.7), Inches(12.3), Inches(4)
    )
    placeholder.fill.solid()
    placeholder.fill.fore_color.rgb = LIGHT_GRAY
    add_text(slide, "[Insérer ici : Figure 5 — Distribution des erreurs]",
             Inches(0.5), Inches(3.5), Inches(12.3), Inches(0.5),
             font_size=16, color=TEXT_GRAY, align=PP_ALIGN.CENTER)

# 3 KPIs en bas
kpis = [
    ("52%", "des prédictions\n< 10% d'erreur", SUCCESS),
    ("83%", "des prédictions\n< 20% d'erreur", WARNING),
    ("94%", "des prédictions\n< 30% d'erreur", CYAN),
]

card_w = Inches(3.9)
for i, (val, label, color) in enumerate(kpis):
    x = Inches(0.8) + i * (card_w + Inches(0.15))
    y = Inches(5.9)

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, Inches(1.2)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = color
    card.line.fill.background()

    add_text(slide, val, x + Inches(0.2), y + Inches(0.1), Inches(1.5), Inches(0.7),
             font_size=32, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, label, x + Inches(1.8), y + Inches(0.15), card_w - Inches(2), Inches(0.9),
             font_size=11, color=WHITE, align=PP_ALIGN.LEFT)

add_footer(slide, 11)


# ==========================================
# SLIDE 12 — DASHBOARD RÉCAP
# ==========================================
print("📄 Slide 12/18 — Dashboard récapitulatif")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Synthèse des performances du modèle",
               "Vue d'ensemble en une image")

# Insérer Figure 6 (dashboard)
fig6_path = PLOTS_DIR / "06_dashboard_performance.png"
if fig6_path.exists():
    slide.shapes.add_picture(
        str(fig6_path),
        Inches(0.4), Inches(1.7),
        width=Inches(12.5)
    )
else:
    placeholder = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.4), Inches(1.7), Inches(12.5), Inches(5.3)
    )
    placeholder.fill.solid()
    placeholder.fill.fore_color.rgb = LIGHT_GRAY
    add_text(slide, "[Insérer ici : Figure 6 — Dashboard récapitulatif]",
             Inches(0.4), Inches(4), Inches(12.5), Inches(0.6),
             font_size=18, color=TEXT_GRAY, align=PP_ALIGN.CENTER)

add_footer(slide, 12)


# ==========================================
# SLIDE 13 — XGBOOST VS LIGHTGBM
# ==========================================
print("📄 Slide 13/18 — Comparaison XGBoost vs LightGBM")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "XGBoost vs LightGBM", "Comparaison des deux meilleurs modèles")

rows = [
    ["Métrique", "XGBoost", "LightGBM", "Gagnant"],
    ["MAE", "7,55", "7,71", "🏆 XGBoost"],
    ["RMSE", "19,22", "18,27", "🏆 LightGBM"],
    ["MAPE", "12,25%", "13,92%", "🏆 XGBoost"],
    ["R²", "0,959", "0,963", "🏆 LightGBM"],
    ["Vitesse", "Moyenne", "Rapide", "🏆 LightGBM"],
    ["Mémoire", "Élevée", "Faible", "🏆 LightGBM"],
    ["Maturité", "★★★★★", "★★★★", "🏆 XGBoost"],
]

table_shape = slide.shapes.add_table(
    len(rows), 4,
    Inches(1.5), Inches(1.9),
    Inches(10), Inches(4.3)
)
table = table_shape.table

table.columns[0].width = Inches(2.5)
table.columns[1].width = Inches(2.5)
table.columns[2].width = Inches(2.5)
table.columns[3].width = Inches(2.5)

for i, row in enumerate(rows):
    for j, val in enumerate(row):
        cell = table.cell(i, j)
        cell.text = val

        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for run in p.runs:
                run.font.size = Pt(13)
                run.font.name = "Calibri"

                if i == 0:
                    run.font.bold = True
                    run.font.color.rgb = WHITE
                elif j == 3:
                    run.font.bold = True
                    run.font.color.rgb = SUCCESS
                else:
                    run.font.color.rgb = DARK

        if i == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = DARK
        elif j == 3 and i > 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xE0, 0xF7, 0xF6)
        else:
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 1 else LIGHT_GRAY

# Verdict
verdict = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(1.5), Inches(6.4), Inches(10), Inches(0.6)
)
verdict.fill.solid()
verdict.fill.fore_color.rgb = CYAN
verdict.line.fill.background()

add_text(slide, "✅  CHOIX FINAL : XGBoost  —  meilleur MAPE + maturité industrielle",
         Inches(1.5), Inches(6.5), Inches(10), Inches(0.4),
         font_size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_footer(slide, 13)


# ==========================================
# SLIDE 14 — FONCTIONNALITÉS CLÉS
# ==========================================
print("📄 Slide 14/18 — Fonctionnalités clés")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Fonctionnalités clés du système")

features = [
    ("💬", "Chat IA", "Assistant conversationnel\navec mémoire"),
    ("📈", "Prédictions", "Prévisions à 7 jours\navec bornes"),
    ("🚨", "Alertes", "Ruptures et expirations\ndétectées"),
    ("📦", "Recommandations", "Quantités optimales\nà commander"),
    ("🎯", "Score de criticité", "Priorisation des\nmédicaments"),
    ("📊", "Explicabilité SHAP", "Interprétation des\nprédictions"),
]

card_w = Inches(3.9)
card_h = Inches(2.2)
for i, (icon, title, sub) in enumerate(features):
    row = i // 3
    col = i % 3
    x = Inches(0.6) + col * (card_w + Inches(0.15))
    y = Inches(1.8) + row * (card_h + Inches(0.2))

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = CYAN
    card.line.width = Pt(1.5)

    add_text(slide, icon, x, y + Inches(0.2), card_w, Inches(0.7),
             font_size=40, color=CYAN, align=PP_ALIGN.CENTER)
    add_text(slide, title, x + Inches(0.1), y + Inches(1.05), card_w - Inches(0.2), Inches(0.4),
             font_size=15, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    add_text(slide, sub, x + Inches(0.1), y + Inches(1.5), card_w - Inches(0.2), Inches(0.6),
             font_size=10, color=TEXT_GRAY, align=PP_ALIGN.CENTER)

add_footer(slide, 14)


# ==========================================
# SLIDE 15 — LIMITES
# ==========================================
print("📄 Slide 15/18 — Limites")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Limites identifiées",
               "Analyse critique et transparente du système")

limites = [
    ("🌍", "Saisonnalité Tchad",
     "Non validée sur le dataset Kaggle — origine géographique non documentée", WARNING),
    ("🌐", "Dépendance réseau",
     "Le LLM (chat IA) nécessite une connexion Internet stable", DANGER),
    ("📊", "Volume de données",
     "Limité à 2 ans d'historique — pourrait être étendu", INFO),
    ("🧪", "Validation terrain",
     "Pas encore testé en conditions réelles de pharmacie", WARNING),
]

y = Inches(1.9)
for icon, title, desc, color in limites:
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.5), y, Inches(10.3), Inches(1.05)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2)

    # Bande latérale
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.5), y, Inches(0.15), Inches(1.05)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = color
    band.line.fill.background()

    add_text(slide, icon, Inches(1.8), y + Inches(0.25), Inches(0.7), Inches(0.6),
             font_size=28, color=color, align=PP_ALIGN.CENTER)
    add_text(slide, title, Inches(2.7), y + Inches(0.15), Inches(3), Inches(0.4),
             font_size=15, bold=True, color=DARK)
    add_text(slide, desc, Inches(2.7), y + Inches(0.55), Inches(8.8), Inches(0.4),
             font_size=11, color=TEXT_GRAY)

    y += Inches(1.15)

add_footer(slide, 15)


# ==========================================
# SLIDE 16 — PERSPECTIVES
# ==========================================
print("📄 Slide 16/18 — Perspectives")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Perspectives d'amélioration",
               "Roadmap à court, moyen et long terme")

horizons = [
    ("📱  COURT TERME", "3 mois", [
        "Application mobile React Native",
        "Validation terrain en pharmacie pilote",
        "Tableau de bord enrichi",
    ], CYAN),
    ("📡  MOYEN TERME", "6-12 mois", [
        "Capteurs IoT (température, humidité)",
        "Intégration fournisseurs",
        "Notifications SMS et push",
    ], INFO),
    ("🏥  LONG TERME", "1-2 ans", [
        "Extension aux structures publiques",
        "Réseau multi-pharmacies",
        "Intégration ministère de la santé",
    ], DARK),
]

card_w = Inches(3.9)
card_h = Inches(4.4)
for i, (title, period, items, color) in enumerate(horizons):
    x = Inches(0.6) + i * (card_w + Inches(0.15))
    y = Inches(1.9)

    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2)

    # Header coloré
    header = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, Inches(1.1)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = color
    header.line.fill.background()

    add_text(slide, title, x + Inches(0.15), y + Inches(0.15), card_w - Inches(0.3), Inches(0.5),
             font_size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, period, x + Inches(0.15), y + Inches(0.65), card_w - Inches(0.3), Inches(0.4),
             font_size=11, color=WHITE, align=PP_ALIGN.CENTER, italic=True)

    # Items
    item_y = y + Inches(1.4)
    for item in items:
        add_text(slide, "• " + item, x + Inches(0.2), item_y, card_w - Inches(0.4), Inches(0.9),
                 font_size=11, color=DARK)
        item_y += Inches(0.9)

add_footer(slide, 16)


# ==========================================
# SLIDE 17 — CONCLUSION
# ==========================================
print("📄 Slide 17/18 — Conclusion")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, WHITE)
add_top_accent(slide, "Conclusion")

# 3 blocs
blocks = [
    ("🎯", "PROBLÉMATIQUE RÉSOLUE",
     "Système intelligent d'aide à la décision\nbasé sur le Machine Learning", CYAN),
    ("📊", "RÉSULTATS CLÉS",
     "MAPE 12,25%  •  R² 0,959\n94% des prédictions < 30% d'erreur", SUCCESS),
    ("🚀", "IMPACT ATTENDU",
     "Amélioration de la disponibilité\ndes médicaments au Tchad", INFO),
]

y = Inches(1.9)
for icon, title, desc, color in blocks:
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1), y, Inches(11.3), Inches(1.5)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = color
    card.line.width = Pt(2)

    # Bande
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1), y, Inches(0.15), Inches(1.5)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = color
    band.line.fill.background()

    add_text(slide, icon, Inches(1.4), y + Inches(0.35), Inches(0.9), Inches(0.8),
             font_size=42, color=color, align=PP_ALIGN.CENTER)
    add_text(slide, title, Inches(2.5), y + Inches(0.2), Inches(9), Inches(0.4),
             font_size=14, bold=True, color=color)
    add_text(slide, desc, Inches(2.5), y + Inches(0.7), Inches(9.5), Inches(0.7),
             font_size=13, color=DARK)

    y += Inches(1.6)

add_footer(slide, 17)


# ==========================================
# SLIDE 18 — MERCI
# ==========================================
print("📄 Slide 18/18 — Merci")
slide = prs.slides.add_slide(BLANK_LAYOUT)
add_background(slide, DARK)

# Bande cyan
band = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, 0, Inches(3.7), SLIDE_WIDTH, Inches(0.08)
)
band.fill.solid()
band.fill.fore_color.rgb = CYAN
band.line.fill.background()

add_text(slide, "🙏", Inches(5.5), Inches(1.2), Inches(2.3), Inches(1.5),
         font_size=110, color=CYAN, align=PP_ALIGN.CENTER)

add_text(slide, "MERCI DE VOTRE ATTENTION",
         Inches(0), Inches(3.9), SLIDE_WIDTH, Inches(1),
         font_size=42, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Questions
q_box = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(5), Inches(5.2), Inches(3.3), Inches(0.8)
)
q_box.fill.solid()
q_box.fill.fore_color.rgb = CYAN
q_box.line.fill.background()
add_text(slide, "Questions ?", Inches(5), Inches(5.4), Inches(3.3), Inches(0.4),
         font_size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Logo DENG PHARMA
add_text(slide, "🏥  DENG PHARMA",
         Inches(0), Inches(6.5), SLIDE_WIDTH, Inches(0.5),
         font_size=16, bold=True, color=CYAN, align=PP_ALIGN.CENTER)


# ==========================================
# SAUVEGARDE
# ==========================================
output_file = OUTPUT_DIR / "DENG_PHARMA_Soutenance.pptx"
prs.save(str(output_file))

print("\n" + "=" * 60)
print("✅ PRÉSENTATION GÉNÉRÉE !")
print("=" * 60)
print(f"\n📁 Fichier : {output_file}")
print(f"📊 Nombre de slides : {len(prs.slides)}")
print(f"🎨 Charte : DENG PHARMA (cyan #0ABAB5)")
print("\n📌 INSTRUCTIONS :")
print("   1. Ouvre le fichier dans PowerPoint ou LibreOffice")
print("   2. Slides 10, 11, 12 → les images matplotlib sont insérées automatiquement")
print("   3. Slides 9 et 14 → ajoute tes captures d'écran de l'app")
print("   4. Personnalise les textes si besoin")
print("\n💡 Astuce : pour les slides 10/11/12, tu dois d'abord")
print("   avoir lancé plot_predictions.py pour générer les PNG.")
print("=" * 60)
