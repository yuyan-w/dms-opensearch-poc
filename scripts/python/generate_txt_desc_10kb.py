# ========================================
# 使い方
# ========================================
# ■ 概要
# - 実行ディレクトリ配下に desc_10kb/ ディレクトリを作成し、
#   約10KBの日本語テキストファイルを10個生成するスクリプト
# - DMS / OpenSearch 検証用の description サンプルデータ作成を目的とする
#
# ■ 実行方法
# python generate_txt_desc_10kb.py
#
# ■ 実行結果
# - desc_10kb/ が存在しない場合は自動作成される
# - 以下のようなファイルが10個生成される
#   - desc_10kb/desc_ja_10kb_1.txt
#   - desc_10kb/desc_ja_10kb_2.txt
#   - ...
#   - desc_10kb/desc_ja_10kb_10.txt
#
# ■ 生成データの内容
# - 日本語の商品説明風テキストをランダム生成する
# - 文の組み合わせ、段落数、改行、箇条書きがランダムに変化する
# - 1ファイルあたりおおよそ10KB前後のサイズになる想定
#   （厳密に10KBぴったりではない）
#
# ■ 補足
# - 語彙プールは subjects / qualities / features / benefits / bullets で管理している
# - より自然な文章にしたい場合は、各配列の要素を増やす
# - よりサイズを増やしたい場合は generate_text() 内のループ回数を増やす
#
# ■ 注意事項
# - 毎回ランダム生成されるため、実行のたびに内容とサイズは変動する
# - 改行や箇条書きを含むため、SQLに直接埋め込むよりファイルとして利用する前提
# - OpenSearch の全文検索検証では、実データに近づけるため語彙プールを増やした方がよい
# ========================================

import random
import os

# 出力ディレクトリ
output_dir = "desc_10kb"
os.makedirs(output_dir, exist_ok=True)

# 語彙プール
subjects = ["本製品は", "この商品は", "当製品は", "こちらの商品は"]
qualities = ["高品質で", "高性能で", "耐久性に優れ", "使いやすく", "軽量で", "設計が洗練されており"]
features = [
    "長時間の使用にも適しています",
    "日常使いから業務用途まで対応します",
    "直感的な操作が可能です",
    "メンテナンス性にも配慮されています",
    "省エネルギー設計が施されています",
    "多機能ながらシンプルな構成です"
]
benefits = ["安心してご利用いただけます。", "幅広い用途で活躍します。", "コストパフォーマンスにも優れています。"]

bullets = [
    "高耐久素材を採用",
    "コンパクト設計",
    "静音動作",
    "簡単セットアップ",
    "長寿命バッテリー",
    "安全性を考慮した設計"
]

def make_sentence():
    s = f"{random.choice(subjects)}{random.choice(qualities)}、{random.choice(features)}。{random.choice(benefits)}"
    if random.random() < 0.3:
        s = s.replace("。", "、さらに", 1)
    return s

def make_paragraph():
    n = random.randint(2, 5)
    p = "".join(make_sentence() for _ in range(n))
    if random.random() < 0.4:
        k = random.randint(2, 4)
        p += "\n・" + "\n・".join(random.sample(bullets, k))
    return p

def generate_text():
    text = ""
    for _ in range(40):
        text += make_paragraph()
        text += "\n" * random.choice([1, 2])
    for _ in range(random.randint(5, 15)):
        text += make_sentence() + ("\n" if random.random() < 0.5 else "")
    return text

# 10ファイル生成
for i in range(1, 11):
    text = generate_text()
    filepath = os.path.join(output_dir, f"desc_ja_10kb_{i}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"{filepath}: {len(text.encode('utf-8'))} bytes")