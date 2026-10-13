"""Generate 250 deterministic augmented examples from the existing 50 synthetic labels.
NOT independently collected real imagery; use a separate real-world holdout for external validity.
"""
from __future__ import annotations
import argparse, csv, random
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sample_data" / "benchmark_50"
DEST = ROOT / "sample_data" / "robust_250"

def font(sz=37):
    for name in ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if Path(name).exists(): return ImageFont.truetype(name,sz)
    return ImageFont.load_default()

def changed_label(img, kind):
    # Make an explicit printed-vs-barcode mismatch. The original barcode remains untouched.
    draw=ImageDraw.Draw(img)
    if kind == 'wrong_batch':
        draw.rectangle((65,220,590,293),fill=(255,255,255))
        draw.text((70,241), 'LOT: WRONG99', fill=(22,27,31),font=font())
    elif kind == 'wrong_expiry':
        draw.rectangle((65,298,590,374),fill=(255,255,255))
        draw.text((70,318), 'EXP: 2033-01',fill=(22,27,31),font=font())
    return img

def generate(out=DEST, seed=20261012):
    rng=random.Random(seed); out.mkdir(parents=True,exist_ok=True)
    with (SOURCE/'ground_truth.csv').open(newline='',encoding='utf-8') as f: source=list(csv.DictReader(f))
    entries=[]
    for i,row in enumerate(source):
        with Image.open(SOURCE/row['filename']) as original: original=original.convert('RGB')
        variants=['lighting','blur','rotation','wrong_batch','damaged_code']
        # Rotate between bad expiry and wrong batch per source: both defects covered.
        if i % 2: variants[3]='wrong_expiry'
        for j,variant in enumerate(variants):
            image=original.copy(); seed_i=rng.randrange(1_000_000)
            if variant == 'lighting': image=ImageEnhance.Contrast(ImageEnhance.Brightness(image).enhance(0.67 if i%2 else 1.35)).enhance(0.75)
            elif variant == 'blur': image=image.filter(ImageFilter.GaussianBlur(radius=1.25 if i%2 else 1.7))
            elif variant == 'rotation':
                image=image.rotate(-2.8 if i%2 else 2.8,resample=Image.Resampling.BICUBIC,expand=False,fillcolor=(240,240,240))
            elif variant.startswith('wrong_'): image=changed_label(image,variant)
            elif variant=='damaged_code':
                d=ImageDraw.Draw(image)
                # Damage a central stripe through the code, not printed text; may remain decodable
                d.rectangle((790,288,960,322),fill=(255,255,255))
            name=f"test_{i+1:03d}_{variant}.png"; image.save(out/name,optimize=True)
            defect=variant in ('wrong_batch','wrong_expiry','damaged_code')
            expected='REVIEW' if row['expected_status']=='REVIEW' or defect else 'PASS'
            entries.append({'filename':name,'source_filename':row['filename'],'variant':variant,
              'expected_status':expected,'printed_product_code':row['product_code'],
              'printed_batch':('WRONG99' if variant=='wrong_batch' else row['batch']),
              'printed_expiry':('2033-01' if variant=='wrong_expiry' else row['expiry']),
              'barcode_payload':row['barcode_payload'],'symbology':row['symbology'],
              'barcode_should_decode': 'false' if variant=='damaged_code' else 'true',
              'seed':str(seed_i)})
    with (out/'ground_truth.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
    print(f"Generated {len(entries)} images at {out}")
    return entries

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=20261012);a=parser.parse_args();generate(seed=a.seed)
