from __future__ import annotations
import csv, hashlib, json, shutil, zipfile
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Prepare the pinned Japan OCR Alpha10 subset.')
parser.add_argument('source_dir', type=Path, help='Downloaded alpha10 directory from the pinned source revision')
parser.add_argument('output_dir', type=Path, help='Output directory for the prepared artifact')
args = parser.parse_args()
SRC = args.source_dir
OUT = args.output_dir
if OUT.exists():
    shutil.rmtree(OUT)
(OUT/'images/eval').mkdir(parents=True)
rows = list(csv.DictReader((SRC/'alpha10_manifest.csv').open(encoding='utf-8-sig')))
labels = []
metadata = []
for row in rows:
    source = json.loads((SRC/row['source_json_path']).read_text(encoding='utf-8'))
    old = Path(row['image_path']).name
    image = f"images/eval/{row['case_id']}.png"
    shutil.copyfile(SRC/row['image_path'], OUT/image)
    items = [{
        'name': item.get('name', ''),
        'quantity': item.get('quantity'),
        'amount_yen': item.get('amount_yen'),
    } for item in source.get('items', [])]
    record = {
        'industry': row['industry'],
        'items': items,
        'total_yen': source.get('totals', {}).get('total_yen', row.get('total_yen')),
        'payment_method': source.get('payment', {}).get('method'),
    }
    normalized = json.dumps(record, ensure_ascii=False, separators=(',', ':'))
    sample = {'image': image, 'record_json': normalized, 'split': 'eval', 'sample_id': row['case_id']}
    labels.append(sample)
    metadata.append({'file_name': image, 'record': record, 'split': 'eval', 'sample_id': row['case_id']})
with (OUT/'labels.csv').open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['image','record_json','split','sample_id'])
    writer.writeheader(); writer.writerows(labels)
(OUT/'metadata.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in metadata),encoding='utf-8')
manifest = {
    'dataset_id':'japan_ocr_receipts','case_id':'japan_ocr_receipts','artifact_version':'0.1.0','version':'v0.1.0',
    'task':'ocr','image_count':len(rows),'sample_count':len(rows),'classes':[],
    'language':'ja','split':'eval','ground_truth':'structured_receipt_fields',
    'source_license':'CC BY 4.0','source_revision':'c82efda5b823494424e6bc6e9ae7577396ded908',
    'synthetic':True,'limitations':['10 samples only','structured fields, not full OCR transcription','not representative of all receipts']
}
source_items=[]
for row in rows:
    for rel in (row['image_path'],row['source_json_path']):
        p=SRC/rel
        source_items.append((f"alpha10/{rel}",hashlib.sha256(p.read_bytes()).hexdigest()))
source_digest=hashlib.sha256(''.join(f'{path} {digest}\n' for path,digest in sorted(source_items)).encode()).hexdigest()
manifest.update({
    'label_format':'structured_ocr_csv_and_jsonl',
    'transform_version':'prepare_japan_ocr_receipts_v1',
    'license':'CC BY 4.0',
    'attribution':f'K10124, Japan OCR Mini Benchmark, Alpha10 approved payload, revision c82efda5b823494424e6bc6e9ae7577396ded908, CC BY 4.0.',
    'source':{
        'url':'https://huggingface.co/datasets/K10124/japan-ocr-mini-benchmark/tree/c82efda5b823494424e6bc6e9ae7577396ded908/alpha10',
        'version':'c82efda5b823494424e6bc6e9ae7577396ded908',
        'sha256':source_digest,
        'sha256_scope':'SHA-256 of the sorted 20-file source inventory paths and individual SHA-256 values; not an archive checksum.'
    }
})
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme = '''# Japan OCR Receipts v0.1.0\n\n10枚の合成日本語レシート画像と、品目・数量・金額・合計額の構造化見本です。画像の文字列をOCRで読み取り、見本と照合する授業や、文化祭などの支出整理ツールの試作に使えます。\n\n## 内容\n- `images/eval/`: 画像10枚。画素は原データのままです。\n- `labels.csv`: 画像パス、照合用の構造化JSON、分割、サンプルID。\n- `metadata.jsonl`: CSVと同じ見本をJSON Linesで記録。\n- `manifest.json`: 版・件数・制約。\n\nこのデータは全文OCRの正解文字列を含みません。品目や合計などの項目を画像から読み取って、構造化見本と確認するための小規模サンプルです。実在店舗・取引・個人の記録ではありません。実際のレシートには個人情報が載る場合があるため、授業では合成データを使ってください。\n\n## 出典と変更\nK10124, *Japan OCR Mini Benchmark*, Alpha10 approved payload, fixed revision `c82efda5b823494424e6bc6e9ae7577396ded908`, CC BY 4.0. 画像は変更せず、source JSONから業種・品目・数量・金額・合計・支払方法だけを抽出し、共通形式に整理しました。\n\n原データ: https://huggingface.co/datasets/K10124/japan-ocr-mini-benchmark/tree/c82efda5b823494424e6bc6e9ae7577396ded908/alpha10\nライセンス: https://creativecommons.org/licenses/by/4.0/\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
(OUT/'LICENSE.txt').write_text('''Attribution: K10124, Japan OCR Mini Benchmark, Alpha10 approved payload, fixed revision c82efda5b823494424e6bc6e9ae7577396ded908.\nLicense: Creative Commons Attribution 4.0 International (CC BY 4.0). https://creativecommons.org/licenses/by/4.0/\nChanges: The original image pixels were not changed. Structured fields were normalized from the accompanying public source JSON into labels.csv and metadata.jsonl.\nNo endorsement by the source author is implied. All receipt examples are synthetic.\n''',encoding='utf-8')
# Audit and deterministic archive.
image_files = sorted((OUT/'images').rglob('*.png'))
assert len(image_files)==10 and len(labels)==10
hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in image_files]
assert len(set(hashes))==len(hashes)
archive = OUT.parent / f'{OUT.name}.zip'
if archive.exists(): archive.unlink()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(OUT.rglob('*')):
        if path.is_file(): z.write(path,Path('japan_ocr_receipts')/path.relative_to(OUT))
sha = hashlib.sha256(archive.read_bytes()).hexdigest()
print(json.dumps({'images':len(image_files),'image_bytes':sum(p.stat().st_size for p in image_files),'archive_bytes':archive.stat().st_size,'archive_sha256':sha,'image_sha256':hashes,'total_yen':[json.loads(x['record_json'])['total_yen'] for x in labels]},ensure_ascii=False,indent=2))
