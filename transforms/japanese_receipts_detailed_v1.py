from __future__ import annotations
import argparse, csv, hashlib, json, shutil, zipfile
from pathlib import Path, PurePosixPath

DATASET_ID="japanese_receipts_detailed"
VERSION="0.1.0"
SOURCE_REVISION="e679e42ba2a408038d4151ced36eb6f32589422c"
SOURCE_URL=f"https://huggingface.co/datasets/IngCrowd/japanese-receipts-detailed/tree/{SOURCE_REVISION}"
ANNOTATIONS_SHA256="90cd9777c4eb14ca06be7832ede10885f89f6e392748a3a9b1d295e2c12b4a1f"
LABELS={"store_name","branch_name","store_address","store_phone","registration_number","datetime","item_line","subtotal","tax","total","taxable_amount","payment","barcode_qr","pii","change","store_info"}
LICENSE_TEXT="""# 利用条件・出典

この配布物は、IngCrowd Inc. の Japanese Receipt Image Dataset (Detailed Annotations) を共通OCR形式へ整理したものです。

- 固定版: e679e42ba2a408038d4151ced36eb6f32589422c
- 出典: https://huggingface.co/datasets/IngCrowd/japanese-receipts-detailed
- ライセンス: CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)
- クレジット: IngCrowd Inc. と本データセットを明記してください。
- 変更: 画像画素は変更していません。画像を images/eval/ に整理し、領域ラベル・百分率座標・文字転記を labels.csv と metadata.jsonl に整理しました。全100枚を評価用splitにまとめました。
- 非商用: 商用目的では利用できません。利用者はCC BY-NC 4.0の条件に従ってください。

個人情報に関する注意: 配布元は確認した個人名や会員・決済カード番号等の選択領域を黒塗りしていますが、すべての個人情報が除去された保証はありません。店舗名、公開連絡先、QRコードや取引番号が見えることがあります。個人の特定・プロファイリングに使わないでください。
"""
README_TEXT="""# 日本語レシートOCR（詳細版）

日本のレシート画像から文字領域を見つけ、OCRの読み取り結果を確認する教材データです。文化祭や部活動の会計入力を補助する試作に使えます。読み取り結果は会計担当者が原票と照合してください。

## 収録内容

- 日本語の実レシート画像100枚
- 項目ラベルと矩形領域2,005件
- 文字転記1,802件
- すべて eval split。OCRモデルの推論と注釈との比較向けです。小規模で、学習用・全件網羅のOCR正解集ではありません。
- 詳細版は基本版1,010枚から選ばれた画像で、基本版に追加の100枚を足したものではありません。

項目には店舗名、日時、明細、税額、合計、支払情報などがあります。転記は選択された領域だけです。注釈のない印字が存在しないとは限りません。

## OCR用の形式

labels.csv の record_json と metadata.jsonl の record は、画像ごとの領域一覧です。各領域は label、bbox_percent（画像幅・高さに対する百分率座標、回転角は度）、transcription を持ちます。transcription が null の領域は、個人情報マスク領域やQR・バーコード領域などで、文字正解が付いていません。領域と文字列の対応を保っています。

## 個人情報と利用上の注意

配布元は選択した個人情報領域を黒塗りしていますが、完全な匿名化は保証しません。公開店舗情報、QRコード、取引番号が残る場合があります。個人の特定やプロファイリングを行わないでください。授業で生徒自身のレシートを共有サービスへアップロードする必要はありません。

このデータはCC BY-NC 4.0の非商用条件で提供します。詳しくは同梱の LICENSE.md を確認してください。

## 出典

IngCrowd Inc., Japanese Receipt Image Dataset (Detailed Annotations), fixed revision e679e42ba2a408038d4151ced36eb6f32589422c.
"""

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def safe_image(root:Path,value:str)->Path:
    rel=PurePosixPath(value)
    if rel.is_absolute() or ".." in rel.parts or "\\" in value or not value.startswith("images/"):
        raise ValueError("unsafe source image path")
    p=root.joinpath(*rel.parts)
    if p.is_symlink() or not p.is_file(): raise ValueError("missing or symlink source image")
    return p

def convert_record(src:dict,size:tuple[int,int])->dict:
    anns=src.get("annotations") or []
    if len(anns)!=1: raise ValueError("expected one annotation set")
    rects={}; texts={}
    for r in anns[0].get("result",[]):
        rid=r.get("id"); v=r.get("value",{})
        if not rid: raise ValueError("region missing local id")
        if r.get("type")=="rectanglelabels":
            if rid in rects: raise ValueError("duplicate region id")
            labels=v.get("rectanglelabels") or []
            if len(labels)!=1 or labels[0] not in LABELS: raise ValueError("unknown region label")
            if (r.get("original_width"),r.get("original_height"))!=size: raise ValueError("annotation dimensions mismatch")
            box={k:v.get(k) for k in ("x","y","width","height")}
            if any(not isinstance(x,(int,float)) or x<0 or x>100 for x in box.values()): raise ValueError("bbox percentage out of range")
            if box["x"]+box["width"]>100.1 or box["y"]+box["height"]>100.1: raise ValueError("bbox outside image")
            rects[rid]={"label":labels[0],"bbox_percent":{**box,"rotation_degrees":v.get("rotation",0)}}
        elif r.get("type")=="textarea":
            arr=v.get("text") or []
            if not all(isinstance(x,str) for x in arr): raise ValueError("invalid text array")
            texts[rid]=arr
        else: raise ValueError("unexpected annotation type")
    regions=[]
    for rid,box in rects.items():
        label=box["label"]; arr=texts.get(rid)
        if label=="pii" and any(x.strip() for x in (arr or [])): raise ValueError("PII transcription present")
        if label not in {"pii","barcode_qr"} and not arr: raise ValueError("text region lacks transcription")
        regions.append({"label":label,**box,"transcription":arr if arr else None})
    return {"image_width":size[0],"image_height":size[1],"coordinate_unit":"percent","image_rotation_degrees":0,"regions":regions}

def build(srcroot:Path,outdir:Path)->dict:
    ap=srcroot/"annotations.json"
    source_ann_sha=sha256(ap)
    if source_ann_sha!=ANNOTATIONS_SHA256: raise ValueError("annotations SHA-256 mismatch")
    records=json.loads(ap.read_text(encoding="utf-8"))
    if len(records)!=100: raise ValueError("expected fixed 100-image subset")
    case=outdir/DATASET_ID; imgout=case/"images"/"eval"
    imgout.mkdir(parents=True,exist_ok=True)
    rows=[]; metadata=[]; source_images=[]; counts={}; regions_n=trans_n=0; seen=set()
    for i,sr in enumerate(records,1):
        rel=sr.get("data",{}).get("image")
        if not isinstance(rel,str) or rel in seen: raise ValueError("missing or duplicate image reference")
        seen.add(rel); original=safe_image(srcroot,rel)
        result=sr["annotations"][0]["result"]
        box=next(x for x in result if x.get("type")=="rectanglelabels")
        size=(box["original_width"],box["original_height"])
        rec=convert_record(sr,size)
        for region in rec["regions"]:
            counts[region["label"]]=counts.get(region["label"],0)+1; regions_n+=1
            if region["transcription"] is not None: trans_n+=1
        name=PurePosixPath(rel).name; image_rel=f"images/eval/{name}"
        target=imgout/name; shutil.copyfile(original,target)
        digest=sha256(original)
        if sha256(target)!=digest: raise ValueError("source image changed during copy")
        sample=f"receipt-{i:03d}"
        rows.append({"image":image_rel,"record_json":json.dumps(rec,ensure_ascii=False,separators=(",",":")),"split":"eval","sample_id":sample})
        metadata.append({"file_name":image_rel,"record":rec,"split":"eval","sample_id":sample})
        source_images.append({"path":rel,"size":original.stat().st_size,"sha256":digest})
    actual={p.relative_to(srcroot).as_posix() for p in (srcroot/"images").rglob("*") if p.is_file()}
    if actual!=seen: raise ValueError("image set differs from annotations")
    if regions_n!=2005 or trans_n!=1802: raise ValueError("region/transcription count mismatch")
    with (case/"labels.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["image","record_json","split","sample_id"]); w.writeheader(); w.writerows(rows)
    with (case/"metadata.jsonl").open("w",encoding="utf-8",newline="") as f:
        for item in metadata: f.write(json.dumps(item,ensure_ascii=False,separators=(",",":"))+"\n")
    (case/"LICENSE.md").write_text(LICENSE_TEXT,encoding="utf-8")
    (case/"README.md").write_text(README_TEXT,encoding="utf-8")
    internal={"case_id":DATASET_ID,"version":"v"+VERSION,"image_count":100,"sample_count":100,"task":"ocr","split_counts":{"eval":100},"label_format":"structured_ocr_csv_and_jsonl","coordinate_unit":"percent","annotation_regions":regions_n,"transcriptions":trans_n,"region_labels":counts,"license":"CC BY-NC 4.0","source_revision":SOURCE_REVISION,"source_annotations_sha256":source_ann_sha,"transform_version":"japanese_receipts_detailed_v1"}
    (case/"manifest.json").write_text(json.dumps(internal,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    files=[]
    for p in sorted(case.rglob("*")):
        if p.is_symlink() or not p.is_file(): continue
        files.append({"path":p.relative_to(outdir).as_posix(),"size":p.stat().st_size,"sha256":sha256(p)})
    return {"manifest_version":"1.0.0","dataset_id":DATASET_ID,"artifact_version":VERSION,"files":files,"image_count":100,"split_counts":{"eval":100},"label_format":"structured_ocr_csv_and_jsonl","transform_version":"japanese_receipts_detailed_v1","license":"CC BY-NC 4.0","attribution":"IngCrowd Inc., Japanese Receipt Image Dataset (Detailed Annotations), fixed revision "+SOURCE_REVISION+", CC BY-NC 4.0.","source":{"url":SOURCE_URL,"version":SOURCE_REVISION,"sha256":source_ann_sha,"image_count":100,"images":source_images}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--zip",type=Path,required=True)
    a=p.parse_args()
    s=a.source_root.resolve(); o=a.output_dir.resolve()
    if o==s or s in o.parents: raise SystemExit("output must be outside source")
    if o.exists(): shutil.rmtree(o)
    o.mkdir(parents=True)
    manifest=build(s,o)
    (o/f"{DATASET_ID}-v{VERSION}.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(a.zip,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as z:
        for file in sorted((o/DATASET_ID).rglob("*")):
            if file.is_file(): z.write(file,file.relative_to(o).as_posix())
    print(json.dumps({"images":manifest["image_count"],"regions":2005,"transcriptions":1802,"artifact_files":len(manifest["files"]),"zip_bytes":a.zip.stat().st_size,"zip_sha256":sha256(a.zip),"manifest":str(o/f"{DATASET_ID}-v{VERSION}.json")}))

if __name__=="__main__": main()
