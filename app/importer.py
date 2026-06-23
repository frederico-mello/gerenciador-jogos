"""Importador: normaliza jogos das pastas Downloads para data/ + SQLite."""

import re
import shutil
import unicodedata
from pathlib import Path

from PIL import Image
from docx import Document

from . import models

AREAS = {
    "anatomia": "Fotos anatomia",
    "histologia": "Fotos Histologia",
    "microbiologia": "Fotos microbiologia",
}

MAX_IMG_SIZE = 1600
JPEG_QUALITY = 85


def slugify(nome):
    """Converte um nome em slug ASCII-safe."""
    nfkd = unicodedata.normalize("NFKD", nome)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    lower = ascii_str.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lower)
    return slug.strip("-")


def classify_file(filename):
    """Classifica um arquivo por substring no nome. Retorna categoria ou None.

    Categorias: 'componentes', 'manual', 'perfil', 'descricao'.
    """
    name_lower = filename.lower()
    ext = Path(filename).suffix.lower()

    if ext == ".docx":
        return "descricao"

    if ext not in (".jpg", ".jpeg", ".png"):
        return None

    if "manual" in name_lower:
        return "manual"
    if "perfil" in name_lower or "foto perfil" in name_lower:
        return "perfil"
    if "componente" in name_lower or "conteudo" in name_lower or "conteúdo" in name_lower:
        return "componentes"
    if "caixa" in name_lower:
        return "componentes"

    return None


def _extract_manual_order(filename):
    """Extrai número de ordem de um manual (ex.: 'Manual parte 2.jpg' → 2)."""
    m = re.search(r"(\d+)", filename)
    return int(m.group(1)) if m else 0


def resize_image(src_path, dst_path):
    """Redimensiona e salva imagem em dst_path (max 1600px, JPEG q=85)."""
    with Image.open(src_path) as img:
        img = img.convert("RGB")
        if max(img.size) > MAX_IMG_SIZE:
            img.thumbnail((MAX_IMG_SIZE, MAX_IMG_SIZE), Image.LANCZOS)
        dst_path = Path(dst_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst_path, "JPEG", quality=JPEG_QUALITY, optimize=True)


def convert_docx_to_md(docx_path):
    """Converte um DOCX para Markdown (parágrafos separados por linha em branco)."""
    doc = Document(str(docx_path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def import_game(origem_dir, area, nome_jogo, data_dir):
    """Importa um único jogo: classifica, copia+redimensiona, converte DOCX,
    faz upsert no DB. Retorna o game_id.
    """
    origem_dir = Path(origem_dir)
    slug = slugify(nome_jogo)
    dest_dir = Path(data_dir) / area / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(origem_dir.iterdir())
    buckets = {"componentes": [], "manual": [], "perfil": [], "descricao": []}

    for f in files:
        if not f.is_file():
            continue
        cat = classify_file(f.name)
        if cat:
            buckets[cat].append(f)

    game_data = {}
    manual_paths = []

    if buckets["componentes"]:
        src = buckets["componentes"][0]
        dst = dest_dir / "componentes.jpg"
        resize_image(src, dst)
        game_data["imagem_componentes"] = f"{area}/{slug}/componentes.jpg"

    if buckets["perfil"]:
        src = buckets["perfil"][0]
        dst = dest_dir / "perfil.jpg"
        resize_image(src, dst)
        game_data["imagem_perfil"] = f"{area}/{slug}/perfil.jpg"
    elif buckets["componentes"] and len(buckets["componentes"]) > 1:
        # fallback: usar segunda "caixa/conteudo" como perfil se houver
        src = buckets["componentes"][1]
        dst = dest_dir / "perfil.jpg"
        resize_image(src, dst)
        game_data["imagem_perfil"] = f"{area}/{slug}/perfil.jpg"

    if buckets["manual"]:
        ordered = sorted(buckets["manual"], key=lambda p: _extract_manual_order(p.name))
        for idx, src in enumerate(ordered, start=1):
            dst = dest_dir / f"manual_{idx}.jpg"
            resize_image(src, dst)
            manual_paths.append(f"{area}/{slug}/manual_{idx}.jpg")

    if buckets["descricao"]:
        src = buckets["descricao"][0]
        try:
            md_text = convert_docx_to_md(src)
            (dest_dir / "descricao.md").write_text(md_text, encoding="utf-8")
            game_data["descricao"] = md_text
        except Exception as exc:
            print(f"  [WARN] Falha ao converter DOCX {src.name}: {exc}")

    game_id = models.upsert_game_by_area_nome(area, nome_jogo, game_data, manual_paths)
    return game_id


def import_all(downloads_root, data_dir):
    """Varre as 3 áreas em downloads_root e importa todos os jogos."""
    downloads_root = Path(downloads_root)
    counts = {}
    for area, folder in AREAS.items():
        area_dir = downloads_root / folder / folder
        counts[area] = 0
        if not area_dir.exists():
            print(f"[WARN] Pasta de origem ausente: {area_dir}")
            continue
        for jogo_dir in sorted(area_dir.iterdir()):
            if not jogo_dir.is_dir():
                continue
            nome_jogo = jogo_dir.name
            try:
                import_game(jogo_dir, area, nome_jogo, data_dir)
                print(f"[OK] {area}/{nome_jogo}")
                counts[area] += 1
            except Exception as exc:
                print(f"[FAIL] {area}/{nome_jogo}: {exc}")

    total = sum(counts.values())
    print(f"\nTotal: {total} jogos (anatomia: {counts['anatomia']}, "
          f"histologia: {counts['histologia']}, microbiologia: {counts['microbiologia']})")
    return counts
