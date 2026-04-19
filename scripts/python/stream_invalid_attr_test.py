#!/usr/bin/env python3

# ========================================
# 使い方
# ========================================
# ■ 概要
# - products テーブルの attr_test に対して型不整合データを流す検証用スクリプト
# - OpenSearch 側で attr_test を integer / date に固定し、
#   型変換失敗（indexing failure）を発生させることが目的
#
# ■ 実行方法
# python3 stream_invalid_attr_text.py
#
# ■ 前提
# - Aurora MySQL に products テーブルが存在すること
# - products に attr_test TEXT NULL が追加済みであること
#   ALTER TABLE products ADD COLUMN attr_test TEXT NULL;
#
# - OpenSearch 側で attr_test の mapping を固定していること（例）
#   PUT products/_mapping
#   {
#     "properties": {
#       "attr_test": {
#         "type": "integer"
#       }
#     }
#   }
#
# ■ 動作概要
# - N秒ごとにM件の処理を実行
# - INSERT / UPDATE をランダムに実行
# - attr_test に対して
#     - 正常値（"123" など）
#     - 異常値（"abc" など）
#   を混在させて投入する
#
# - VALID_RATE により正常値/異常値の割合を制御
#
# ■ 検証で確認できること
# - OpenSearch 側の型変換失敗（mapping conflict）
# - DMS のリトライ挙動
# - CloudWatch Logs のエラー内容
# - CDC遅延の発生有無
#
# ■ 注意事項
# - 無限ループで実行されるため停止は Ctrl+C
# - UPDATE対象IDは 1〜100000 を前提
# - attr_test の mapping が dynamic のままだと失敗が再現できない
# ========================================

import random
import time
import uuid
from decimal import Decimal

import pymysql

HOST = "dms-test-aurora-mysql.cluster-cuwkjdec3sfy.ap-northeast-1.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "Password1234!"
DATABASE = "dmsapp"

INTERVAL_SECONDS = 5
BATCH_SIZE = 1

INSERT_RATE = 0.2
UPDATE_RATE = 0.8

MIN_TARGET_ID = 1
MAX_TARGET_ID = 100000

VALID_RATE = 0.5

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

VALID_VALUES = ["123", "456", "789", "1000"]
INVALID_VALUES = ["abc", "invalid", "NaN", "error_value", "###"]


def choose_action():
    return "insert" if random.random() < INSERT_RATE else "update"


def choose_attr_value():
    if random.random() < VALID_RATE:
        return random.choice(VALID_VALUES), "valid"
    else:
        return random.choice(INVALID_VALUES), "invalid"


def make_name(category_name, seq):
    brand = random.choice(BRANDS)
    return f"{category_name}{brand}-{seq:08d}"


def make_sku(seq):
    return f"SKU-ATTR-{seq:010d}"


def make_description(category_name):
    return f"{category_name}の検証用データ"


def get_next_seq(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM products")
        return int(cursor.fetchone()[0]) + 1


def insert_product(conn, seq):
    sql = """
    INSERT INTO products
      (uuid, category_id, sku, name, description, price, status, attr_test)
    VALUES
      (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    category_id, category_name = random.choice(LEAF_CATEGORIES)
    value, value_type = choose_attr_value()

    row = (
        str(uuid.uuid4()),
        category_id,
        make_sku(seq),
        make_name(category_name, seq),
        make_description(category_name),
        Decimal(f"{random.uniform(980.0, 49800.0):.2f}"),
        random.choice(STATUS_VALUES),
        value,
    )

    with conn.cursor() as cursor:
        cursor.execute(sql, row)

    conn.commit()
    return seq, value, value_type


def update_product(conn):
    sql = """
    UPDATE products
    SET attr_test = %s, updated_at = NOW()
    WHERE id = %s
    """

    value, value_type = choose_attr_value()
    target_id = random.randint(MIN_TARGET_ID, MAX_TARGET_ID)

    with conn.cursor() as cursor:
        cursor.execute(sql, (value, target_id))

    conn.commit()
    return target_id, value, value_type


def main():
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
        print(f"valid_rate: {VALID_RATE}")
        print(f"start_insert_seq: {next_seq}")

        while True:
            for _ in range(BATCH_SIZE):
                action = choose_action()

                if action == "insert":
                    target_id, value, value_type = insert_product(conn, next_seq)
                    print(
                        f"action=insert id={target_id} value={value} type={value_type}",
                        flush=True
                    )
                    next_seq += 1

                else:
                    target_id, value, value_type = update_product(conn)
                    print(
                        f"action=update id={target_id} value={value} type={value_type}",
                        flush=True
                    )

            time.sleep(INTERVAL_SECONDS)

    finally:
        conn.close()


if __name__ == "__main__":
    main()