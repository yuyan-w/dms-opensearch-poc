# ========================================
# 使い方
# ========================================
# ■ 概要
# - products テーブルに対して、継続的に INSERT を行うストリーム投入用スクリプト
# - DMS の CDC 動作確認、および OpenSearch 反映確認を目的とする
# - 通常サイズの description を基本としつつ、一定確率で desc_10kb/ 配下の巨大 description も挿入できる
#
# ■ 実行方法
# python3 stream_insert_products.py
#
# ■ 実行結果
# - 1秒ごとに 1〜20件（設定値による）の products レコードを追加する
# - 実行ログとして以下を表示する
#   - start sequence
#   - giant_description_rate
#   - giant_description_files
#   - inserted 件数
#   - giant description が使われた件数
#   - 次回採番予定の sequence
#
# ■ 動作概要
# - products の MAX(id) を取得し、その続きの採番で新規レコードを INSERT する
# - category_id / name / sku / price / status はランダム生成する
# - description は以下のどちらかを使用する
#   - 通常の短めの説明文
#   - desc_10kb/ 配下のテキストファイルから読み込んだ巨大 description
#
# ■ 前提
# - Aurora MySQL に products テーブルが存在すること
# - 接続先情報（HOST / USER / PASSWORD / DATABASE）が正しいこと
# - 巨大 description を使う場合は、実行ディレクトリ配下に desc_10kb/ が存在し、
#   配下に *.txt ファイルが配置されていること
#
# ■ 主な設定値
# - SLEEP_SECONDS
#   - ループ間隔（秒）
# - MIN_INSERTS_PER_LOOP / MAX_INSERTS_PER_LOOP
#   - 1ループあたりの INSERT 件数
# - GIANT_DESCRIPTION_RATE
#   - 巨大 description を使う確率
# - GIANT_DESCRIPTION_DIR
#   - 巨大 description ファイルの格納ディレクトリ
#
# ■ 注意事項
# - 停止するまで無限ループで実行される
# - INSERT 件数や巨大 description の比率を上げると、Aurora / DMS / OpenSearch の負荷が増加する
# - giant description ファイルが存在しない場合は警告を出し、通常 description のみで継続する
# - 実行中は id が継続的に増加するため、繰り返し実行時はデータ件数に注意する
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

SLEEP_SECONDS = 1
MIN_INSERTS_PER_LOOP = 1
MAX_INSERTS_PER_LOOP = 20

# 巨大descriptionを使う確率
GIANT_DESCRIPTION_RATE = 0.05

# 巨大descriptionファイルの格納ディレクトリ
GIANT_DESCRIPTION_DIR = "desc_10kb"

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

ADJECTIVES = [
    "軽量", "防水", "通勤向け", "高耐久", "静音", "省エネ", "高性能", "多機能",
    "コンパクト", "大容量", "家庭向け", "業務向け",
]

FEATURES = [
    "タイマー機能", "温度調整機能", "自動停止機能", "抗菌加工",
    "取り外し可能パーツ", "高効率フィルター", "静音モード", "省スペース設計",
]

SCENES = [
    "在宅勤務", "毎日の通勤", "オフィス利用", "家庭内利用",
    "一人暮らし", "ファミリー利用", "日常清掃", "朝の忙しい時間",
]

BRANDS = [
    "Aster", "Brillia", "Crest", "D-NEXT", "EverFine", "Flux", "Glow", "Horizon"
]

STATUS_VALUES = ["active"] * 97 + ["inactive"] * 3


def load_giant_descriptions(desc_dir: str) -> list[str]:
    path = Path(desc_dir)
    if not path.exists() or not path.is_dir():
        print(f"[WARN] giant description directory not found: {desc_dir}")
        return []

    files = sorted(path.glob("*.txt"))
    if not files:
        print(f"[WARN] no giant description files found in: {desc_dir}")
        return []

    descriptions = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8").strip()
        if text:
            descriptions.append(text)

    if descriptions:
        print(f"[INFO] loaded giant description files: {len(descriptions)}")

    return descriptions


def make_name(category_name: str, seq: int) -> str:
    brand = random.choice(BRANDS)
    return f"{category_name}{brand}-{seq:08d}"


def make_sku(seq: int) -> str:
    return f"SKU-STREAM-{seq:010d}"


def make_normal_description(category_name: str) -> str:
    chosen_adj = random.sample(ADJECTIVES, 4)
    chosen_feat = random.sample(FEATURES, 3)
    chosen_scene = random.sample(SCENES, 2)

    return (
        f"この{category_name}は{chosen_adj[0]}で{chosen_adj[1]}な設計を採用しており、"
        f"{chosen_scene[0]}でも扱いやすいモデルです。"
        f"{chosen_feat[0]}と{chosen_feat[1]}を備え、利用者の負担を抑えながら安定した使い心地を提供します。"
        f"さらに{chosen_adj[2]}かつ{chosen_adj[3]}な特徴を持ち、{chosen_scene[1]}にも適しています。"
        f"{chosen_feat[2]}を採用し、検索検証用のテキストとして、軽量、防水、通勤向け、高耐久、静音、省エネ、高性能、多機能、"
        f"コンパクト、大容量、家庭向け、業務向けというキーワードを含みます。"
    )


def make_description(category_name: str, giant_descriptions: list[str]) -> tuple[str, bool]:
    use_giant = bool(giant_descriptions) and random.random() < GIANT_DESCRIPTION_RATE
    if use_giant:
        return random.choice(giant_descriptions), True
    return make_normal_description(category_name), False


def get_start_seq(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM products")
        row = cursor.fetchone()
        return int(row[0]) + 1


def insert_products(conn, start_seq: int, count: int, giant_descriptions: list[str]) -> tuple[int, int]:
    sql = """
    INSERT INTO products
      (uuid, category_id, sku, name, description, price, status)
    VALUES
      (%s, %s, %s, %s, %s, %s, %s)
    """
    rows = []
    giant_count = 0

    for seq in range(start_seq, start_seq + count):
        category_id, category_name = random.choice(LEAF_CATEGORIES)
        product_uuid = str(uuid.uuid4())
        sku = make_sku(seq)
        name = make_name(category_name, seq)
        description, is_giant = make_description(category_name, giant_descriptions)
        price = Decimal(f"{random.uniform(980.0, 49800.0):.2f}")
        status = random.choice(STATUS_VALUES)

        if is_giant:
            giant_count += 1

        rows.append((
            product_uuid,
            category_id,
            sku,
            name,
            description,
            price,
            status,
        ))

    with conn.cursor() as cursor:
        cursor.executemany(sql, rows)

    conn.commit()
    return start_seq + count, giant_count


def main() -> None:
    giant_descriptions = load_giant_descriptions(GIANT_DESCRIPTION_DIR)

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
        current_seq = get_start_seq(conn)
        print(f"start sequence: {current_seq}")
        print(f"giant_description_rate: {GIANT_DESCRIPTION_RATE}")
        print(f"giant_description_files: {len(giant_descriptions)}")

        while True:
            insert_count = random.randint(MIN_INSERTS_PER_LOOP, MAX_INSERTS_PER_LOOP)
            current_seq, giant_count = insert_products(conn, current_seq, insert_count, giant_descriptions)
            print(
                f"inserted: {insert_count} rows, "
                f"giant_descriptions: {giant_count}, "
                f"next_seq: {current_seq}"
            )
            time.sleep(SLEEP_SECONDS)

    finally:
        conn.close()


if __name__ == "__main__":
    main()