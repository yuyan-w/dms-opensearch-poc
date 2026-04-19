# ========================================
# 使い方
# ========================================
# ■ 前提
# - 実行ディレクトリに desc_10kb/ が存在すること
# - desc_10kb/ 配下に *.txt（約10KBの日本語テキスト）が配置されていること
#
# ■ 実行方法
# python script.py --count 100
#
# ■ オプション
# --count      : 必須。INSERTする件数
# --desc-dir   : 任意。descriptionファイルのディレクトリ（デフォルト: desc_10kb）
#
# ■ 実行例
# python script.py --count 10
# → products テーブルにランダムな description を持つレコードが10件INSERTされる
#
# ■ 注意事項
# - description は desc_10kb 配下のファイルからランダムに選択される
# - 大量件数（例: 10000件以上）を指定するとDB負荷・DMS負荷が高くなるため注意
# - charset は utf8mb4 を前提としている
# ========================================

import argparse
import random
import uuid
from decimal import Decimal
from pathlib import Path

import pymysql

HOST = "dms-test-aurora-mysql.cluster-cuwkjdec3sfy.ap-northeast-1.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "Password1234!"
DATABASE = "dmsapp"

LEAF_CATEGORIES = [
    (3, "コーヒーメーカー"),
    (4, "電子レンジ"),
    (6, "掃除機"),
    (7, "空気清浄機"),
    (9, "椅子"),
    (10, "机"),
    (11, "収納"),
    (15, "バッグ"),
    (16, "シューズ"),
]

BRANDS = [
    "Aster", "Brillia", "Crest", "D-NEXT", "EverFine", "Flux", "Glow", "Horizon"
]

STATUS_VALUES = ["active"] * 97 + ["inactive"] * 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="desc_10kb 配下のテキストをランダムに使って products に投入する"
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="投入件数",
    )
    parser.add_argument(
        "--desc-dir",
        type=str,
        default="desc_10kb",
        help="説明文ファイルの格納ディレクトリ",
    )
    return parser.parse_args()


def load_description_files(desc_dir: str) -> list[str]:
    path = Path(desc_dir)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"directory not found: {desc_dir}")

    files = sorted(path.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"no txt files found in: {desc_dir}")

    descriptions = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8").strip()
        if text:
            descriptions.append(text)

    if not descriptions:
        raise ValueError(f"no usable text found in: {desc_dir}")

    return descriptions


def make_name(category_name: str, seq: int) -> str:
    brand = random.choice(BRANDS)
    return f"{category_name}{brand}-{seq:08d}"


def make_sku(seq: int) -> str:
    return f"SKU-BULK-{seq:010d}"


def get_start_seq(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM products")
        row = cursor.fetchone()
        return int(row[0]) + 1


def build_rows(start_seq: int, count: int, descriptions: list[str]) -> list[tuple]:
    rows = []

    for seq in range(start_seq, start_seq + count):
        category_id, category_name = random.choice(LEAF_CATEGORIES)
        product_uuid = str(uuid.uuid4())
        sku = make_sku(seq)
        name = make_name(category_name, seq)
        description = random.choice(descriptions)
        price = Decimal(f"{random.uniform(980.0, 49800.0):.2f}")
        status = random.choice(STATUS_VALUES)

        rows.append((
            product_uuid,
            category_id,
            sku,
            name,
            description,
            price,
            status,
        ))

    return rows


def insert_products(conn, rows: list[tuple]) -> None:
    sql = """
    INSERT INTO products
      (uuid, category_id, sku, name, description, price, status)
    VALUES
      (%s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cursor:
        cursor.executemany(sql, rows)
    conn.commit()


def main() -> None:
    args = parse_args()
    descriptions = load_description_files(args.desc_dir)

    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        charset="utf8mb4",
        autocommit=False,
    )

    try:
        start_seq = get_start_seq(conn)
        rows = build_rows(start_seq, args.count, descriptions)
        insert_products(conn, rows)
        print(f"inserted: {args.count} rows")
        print(f"start_seq: {start_seq}")
        print(f"end_seq: {start_seq + args.count - 1}")
        print(f"description_files: {len(descriptions)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()