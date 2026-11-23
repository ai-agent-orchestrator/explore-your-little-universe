#!/usr/bin/env python3
"""Build web-ready tarot assets for the frontend.

- Splits the four minor-arcana sheets into 56 individual card images
  (card rectangles are detected, not assumed from a fixed grid).
- Downsizes the 22 major arcana + card back to WebP.
- Writes frontend/public/tarot/deck.json (78 cards) and updates minor-arcana.json
  `individual_image_path` entries.

Usage: python3 tools/build_tarot_assets.py
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
import scipy.ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'docs/images/tarot'
OUT = ROOT / 'frontend/public/tarot'
MAJOR_W, MAJOR_H = 480, 720
MINOR_W, MINOR_H = 320, 480  # sheet crops are ~250x375 and not all the same aspect; normalised to 2:3
SUITS = ['wands', 'cups', 'swords', 'pentacles']
ROW_SIZES = [5, 5, 4]


def _runs(flags):
    """Yield (start, stop) of consecutive True runs."""
    out, start = [], None
    for i, f in enumerate(list(flags) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            out.append((start, i))
            start = None
    return out


def detect_cards(path):
    """Row bands from horizontal gaps, card columns from vertical gaps inside each band.

    Cards in a row nearly touch (a few px apart) and bright sky can bridge them in a
    flood-fill, so gaps are found with column/row profiles of dark background instead.
    """
    im = Image.open(path).convert('RGB')
    lum = np.asarray(im).astype(int).sum(axis=2)
    dark = lum < 190
    rows = [r for r in _runs(dark.mean(axis=1) < 0.93) if r[1] - r[0] > 200]
    assert len(rows) == 3, f'{path.name}: expected 3 rows, found {len(rows)}'
    boxes = []
    for (y0, y1), size in zip(rows, ROW_SIZES):
        band = dark[y0:y1]
        cols = [c for c in _runs(band.mean(axis=0) < 0.93) if c[1] - c[0] > 150]
        assert len(cols) == size, f'{path.name}: row at y={y0} expected {size} cards, found {len(cols)}'
        for x0, x1 in cols:
            # trim leftover background margin (rounded corners / glow) to the card's own edge
            sub = dark[y0:y1, x0:x1]
            xs = np.where(sub.mean(axis=0) < 0.6)[0]
            ys = np.where(sub.mean(axis=1) < 0.6)[0]
            boxes.append((x0 + xs[0], y0 + ys[0], x0 + xs[-1] + 1, y0 + ys[-1] + 1))
    return im, boxes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'minor').mkdir(exist_ok=True)
    majors = json.loads((SRC / 'major-arcana.json').read_text())
    minors = json.loads((SRC / 'minor/minor-arcana.json').read_text())
    deck = []

    for c in majors['cards']:
        im = Image.open(ROOT / c['image_path']).convert('RGB').resize((MAJOR_W, MAJOR_H), Image.LANCZOS)
        name = f"{c['slug']}.webp"
        im.save(OUT / name, 'WEBP', quality=86, method=6)
        deck.append({'card_id': c['card_id'], 'arcana': 'major', 'name_en': c['name_en'],
                     'name_ko': c['name_ko'], 'image': f'tarot/{name}'})
    Image.open(SRC / 'back.png').convert('RGB').resize((MAJOR_W, MAJOR_H), Image.LANCZOS) \
        .save(OUT / 'back.webp', 'WEBP', quality=86, method=6)

    by_id = {c['card_id']: c for c in minors['cards']}
    for suit in SUITS:
        im, boxes = detect_cards(SRC / f'minor/{suit}-sheet.png')
        flat = boxes  # already ordered row-major
        assert len(flat) == 14
        for idx, box in enumerate(flat):
            cid = f'{suit}_{idx + 1:02d}'
            meta = by_id[cid]
            r = 0 if idx < 5 else 1 if idx < 10 else 2
            assert meta['sheet_position']['row'] == r, (cid, meta['sheet_position'])
            crop = im.crop(box)
            crop = crop.resize((MINOR_W, MINOR_H), Image.LANCZOS)
            name = f'minor/{cid}.webp'
            crop.save(OUT / name, 'WEBP', quality=88, method=6)
            meta['individual_image_path'] = f'frontend/public/tarot/{name}'
            deck.append({'card_id': cid, 'arcana': 'minor', 'suit': suit, 'name_en': meta['name_en'],
                         'name_ko': meta.get('name_ko'), 'image': f'tarot/{name}'})

    minors['status'] = 'individual_images_extracted'
    (SRC / 'minor/minor-arcana.json').write_text(json.dumps(minors, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'deck.json').write_text(json.dumps({'deck': 'Karmic Resonance', 'back': 'tarot/back.webp', 'cards': deck},
                                             ensure_ascii=False, indent=1) + '\n')
    print(len(deck), 'cards written to', OUT)


if __name__ == '__main__':
    main()
