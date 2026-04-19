#!/usr/bin/env python3

# ========================================
# 使い方
# ========================================
# ■ 概要
# - products テーブルに対して、5秒に1件の頻度で huge_description を流す異常系検証用スクリプト
# - INSERT / UPDATE の両方を実行し、100KB description を使った DMS / OpenSearch 挙動確認を目的とする
#
# ■ 実行方法
# ./stream_invalid_huge_description.py
# または
# python3 stream_invalid_huge_description.py
#
# ■ 前提
# - Aurora MySQL に products テーブルが存在すること
# - products に huge_description LONGTEXT NULL が追加済みであること
# - 実行ディレクトリ配下に desc_100kb/ が存在し、*.txt ファイルが配置されていること
#
# ■ 動作概要
# - 5秒ごとに1回処理を実行する
# - 1回ごとに INSERT または UPDATE を1件実行する
# - INSERT / UPDATE の比率は INSERT 20%, UPDATE 80%
# - huge_description には desc_100kb/ 配下のファイルをランダムに1つ使用する
# - 実行ログとして action / id / payload_size_bytes / source_file を表示する
#
# ■ 注意事項
# - 停止するまで無限ループで実行される
# - UPDATE対象IDは 1〜100000 を前提としている
# - 100KB description により Aurora / DMS / OpenSearch の負荷が増加するため注意
# ========================================

import random
import time
import uuid
from decimal import Decimal
from pathlib import Path

import pymysql

HOST = "dms-test-aurora-mysql.cluster-cuwkjdec3sfy.ap-northeast-1.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "Password1234!"
DATABASE = "dmsapp"

INTERVAL_SECONDS = 5   # N秒
BATCH_SIZE = 1         # M件（1秒1件なら 1 / 1秒ループにする）

INSERT_RATE = 0.2
UPDATE_RATE = 0.8

MIN_TARGET_ID = 1
MAX_TARGET_ID = 100000

HUGE_DESCRIPTION_DIR = "desc_100kb"

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


def load_huge_description_files(desc_dir: str) -> list[tuple[str, str]]:
    path = Path(desc_dir)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"huge description directory not found: {desc_dir}")

    files = sorted(path.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"no huge description files found in: {desc_dir}")

    descriptions = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8").strip()
        if text:
            descriptions.append((file_path.name, text))

    if not descriptions:
        raise ValueError(f"no usable huge description text found in: {desc_dir}")

    return descriptions


def choose_action() -> str:
    return "insert" if random.random() < INSERT_RATE else "update"


def make_name(category_name: str, seq: int) -> str:
    brand = random.choice(BRANDS)
    return f"{category_name}{brand}-{seq:08d}"


def make_sku(seq: int) -> str:
    return f"SKU-HUGE-{seq:010d}"


def make_description(category_name: str) -> str:
    return (
        f"この{category_name}は高耐久で使いやすい設計を採用しており、"
        f"検索検証向けの通常 description として利用されます。"
    )


def get_next_seq(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM products")
        row = cursor.fetchone()
        return int(row[0]) + 1


def insert_product(conn, seq: int, huge_descriptions: list[tuple[str, str]]) -> tuple[int, int, str]:
    sql = """
    INSERT INTO products
      (uuid, category_id, sku, name, description, huge_description, price, status)
    VALUES
      (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    category_id, category_name = random.choice(LEAF_CATEGORIES)
    file_name, huge_description = random.choice(huge_descriptions)

    row = (
        str(uuid.uuid4()),
        category_id,
        make_sku(seq),
        make_name(category_name, seq),
        make_description(category_name),
        huge_description,
        Decimal(f"{random.uniform(980.0, 49800.0):.2f}"),
        random.choice(STATUS_VALUES),
    )

    with conn.cursor() as cursor:
        cursor.execute(sql, row)

    conn.commit()
    return seq, len(huge_description.encode("utf-8")), file_name


def update_product(conn, huge_descriptions: list[tuple[str, str]]) -> tuple[int, int, str]:
    sql = """
    UPDATE products
    SET huge_description = %s, updated_at = NOW()
    WHERE id = %s
    """

    file_name, huge_description = random.choice(huge_descriptions)
    target_id = random.randint(MIN_TARGET_ID, MAX_TARGET_ID)

    with conn.cursor() as cursor:
        affected_rows = cursor.execute(sql, (huge_description, target_id))

    conn.commit()

    if affected_rows == 0:
        return target_id, len(huge_description.encode("utf-8")), file_name

    return target_id, len(huge_description.encode("utf-8")), file_name


def main() -> None:
    huge_descriptions = load_huge_description_files(HUGE_DESCRIPTION_DIR)

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
        next_seq = get_next_seq(conn)

        print(f"sleep_seconds: {INTERVAL_SECONDS}")
        print(f"insert_rate: {INSERT_RATE}")
        print(f"update_rate: {UPDATE_RATE}")
        print(f"huge_description_files: {len(huge_descriptions)}")
        print(f"update_target_range: {MIN_TARGET_ID} - {MAX_TARGET_ID}")
        print(f"start_insert_seq: {next_seq}")

        while True:
            for _ in range(BATCH_SIZE):
                action = choose_action()

                if action == "insert":
                    target_id, payload_size_bytes, source_file = insert_product(conn, next_seq, huge_descriptions)
                    print(
                        f"action=insert "
                        f"id={target_id} "
                        f"payload_size_bytes={payload_size_bytes} "
                        f"source_file={source_file}",
                        flush=True
                    )
                    next_seq += 1

                else:
                    target_id, payload_size_bytes, source_file = update_product(conn, huge_descriptions)
                    print(
                        f"action=update "
                        f"id={target_id} "
                        f"payload_size_bytes={payload_size_bytes} "
                        f"source_file={source_file}",
                        flush=True
                    )

            time.sleep(INTERVAL_SECONDS)

    finally:
        conn.close()


if __name__ == "__main__":
    main()