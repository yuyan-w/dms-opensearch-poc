# ========================================
# 使い方
# ========================================
# ■ 概要
# - products テーブルに対して、継続的に UPDATE を行うストリーム更新用スクリプト
# - DMS の CDC 動作確認、および OpenSearch 反映確認を目的とする
# - description / price / status の更新をランダムに混在させ、
#   一定確率で desc_10kb/ 配下の巨大 description を使った更新も行う
#
# ■ 実行方法
# python3 stream_update_products.py
#
# ■ 実行結果
# - 1秒ごとに 1〜20件（設定値による）の products レコードを更新する
# - 実行ログとして以下を表示する
#   - target_id_range
#   - giant_description_rate
#   - giant_description_files
#   - update_rates
#   - requested_updates
#   - updated_rows
#   - description_updates
#   - giant description を使った更新件数
#   - price_updates
#   - status_updates
#
# ■ 動作概要
# - 指定したID範囲（MIN_TARGET_ID〜MAX_TARGET_ID）からランダムに対象 id を抽出する
# - 各レコードに対して以下のいずれかの UPDATE を行う
#   - description 更新
#   - price 更新
#   - status 更新
# - description 更新時は以下のどちらかを使用する
#   - 通常の短めの説明文
#   - desc_10kb/ 配下のテキストファイルから読み込んだ巨大 description
# - 更新時は updated_at を NOW() で更新する
#
# ■ 前提
# - Aurora MySQL に products テーブルが存在すること
# - 接続先情報（HOST / USER / PASSWORD / DATABASE）が正しいこと
# - 更新対象となる products.id が、MIN_TARGET_ID〜MAX_TARGET_ID の範囲に存在すること
# - 巨大 description を使う場合は、実行ディレクトリ配下に desc_10kb/ が存在し、
#   配下に *.txt ファイルが配置されていること
#
# ■ 主な設定値
# - SLEEP_SECONDS
#   - ループ間隔（秒）
# - MIN_UPDATES_PER_LOOP / MAX_UPDATES_PER_LOOP
#   - 1ループあたりの UPDATE 件数
# - MIN_TARGET_ID / MAX_TARGET_ID
#   - 更新対象として抽出する id の範囲
# - GIANT_DESCRIPTION_RATE
#   - description 更新時に巨大 description を使う確率
# - GIANT_DESCRIPTION_DIR
#   - 巨大 description ファイルの格納ディレクトリ
# - DESCRIPTION_UPDATE_RATE / PRICE_UPDATE_RATE / STATUS_UPDATE_RATE
#   - 更新種別ごとの比率
#
# ■ 注意事項
# - 停止するまで無限ループで実行される
# - UPDATE 対象 ID が存在しない場合、その更新は実行件数に含まれても updated_rows には反映されない
# - 巨大 description を使う UPDATE は、INSERT よりも DMS / OpenSearch 負荷が高くなりやすい
# - update_rates の合計は 1.0 になる前提
# - giant description ファイルが存在しない場合は警告を出し、通常 description のみで継続する
# ========================================

import random
import time
from decimal import Decimal
from pathlib import Path

import pymysql

HOST = "dms-test-aurora-mysql.cluster-cuwkjdec3sfy.ap-northeast-1.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "Password1234!"
DATABASE = "dmsapp"

SLEEP_SECONDS = 1
MIN_UPDATES_PER_LOOP = 1
MAX_UPDATES_PER_LOOP = 20

# 更新対象IDの範囲
MIN_TARGET_ID = 1
MAX_TARGET_ID = 100000

# 巨大descriptionを使う確率
GIANT_DESCRIPTION_RATE = 0.05

# 巨大descriptionファイルの格納ディレクトリ
GIANT_DESCRIPTION_DIR = "desc_10kb"

# 更新内容の比率
DESCRIPTION_UPDATE_RATE = 0.7
PRICE_UPDATE_RATE = 0.2
STATUS_UPDATE_RATE = 0.1

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


def make_normal_description() -> str:
    chosen_adj = random.sample(ADJECTIVES, 4)
    chosen_feat = random.sample(FEATURES, 3)
    chosen_scene = random.sample(SCENES, 2)

    return (
        f"この商品は{chosen_adj[0]}で{chosen_adj[1]}な設計を採用しており、"
        f"{chosen_scene[0]}でも扱いやすいモデルです。"
        f"{chosen_feat[0]}と{chosen_feat[1]}を備え、利用者の負担を抑えながら安定した使い心地を提供します。"
        f"さらに{chosen_adj[2]}かつ{chosen_adj[3]}な特徴を持ち、{chosen_scene[1]}にも適しています。"
        f"{chosen_feat[2]}を採用し、検索検証用のテキストとして、軽量、防水、通勤向け、高耐久、静音、省エネ、高性能、多機能、"
        f"コンパクト、大容量、家庭向け、業務向けというキーワードを含みます。"
    )


def make_description(giant_descriptions: list[str]) -> tuple[str, bool]:
    use_giant = bool(giant_descriptions) and random.random() < GIANT_DESCRIPTION_RATE
    if use_giant:
        return random.choice(giant_descriptions), True
    return make_normal_description(), False


def choose_update_type() -> str:
    r = random.random()
    if r < DESCRIPTION_UPDATE_RATE:
        return "description"
    if r < DESCRIPTION_UPDATE_RATE + PRICE_UPDATE_RATE:
        return "price"
    return "status"


def update_products(conn, count: int, giant_descriptions: list[str]) -> tuple[int, int, int, int, int]:
    sql_update_description = """
    UPDATE products
    SET description = %s, updated_at = NOW()
    WHERE id = %s
    """
    sql_update_price = """
    UPDATE products
    SET price = %s, updated_at = NOW()
    WHERE id = %s
    """
    sql_update_status = """
    UPDATE products
    SET status = %s, updated_at = NOW()
    WHERE id = %s
    """

    requested_ids = random.sample(
        range(MIN_TARGET_ID, MAX_TARGET_ID + 1),
        k=min(count, MAX_TARGET_ID - MIN_TARGET_ID + 1),
    )

    updated_count = 0
    giant_description_count = 0
    description_update_count = 0
    price_update_count = 0
    status_update_count = 0

    updated_ids = []

    with conn.cursor() as cursor:
        for target_id in requested_ids:
            update_type = choose_update_type()

            if update_type == "description":
                description, is_giant = make_description(giant_descriptions)
                affected_rows = cursor.execute(sql_update_description, (description, target_id))
                if affected_rows > 0:
                    updated_ids.append(target_id)
                    updated_count += 1
                    description_update_count += 1
                    if is_giant:
                        giant_description_count += 1

            elif update_type == "price":
                price = Decimal(f"{random.uniform(980.0, 49800.0):.2f}")
                affected_rows = cursor.execute(sql_update_price, (price, target_id))
                if affected_rows > 0:
                    updated_ids.append(target_id) 
                    updated_count += 1
                    price_update_count += 1

            else:
                status = random.choice(STATUS_VALUES)
                affected_rows = cursor.execute(sql_update_status, (status, target_id))
                if affected_rows > 0:
                    updated_ids.append(target_id) 
                    updated_count += 1
                    status_update_count += 1

    conn.commit()
    return (
        updated_ids,
        updated_count,
        giant_description_count,
        description_update_count,
        price_update_count,
        status_update_count,
    )


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
        print(f"target_id_range: {MIN_TARGET_ID} - {MAX_TARGET_ID}")
        print(f"giant_description_rate: {GIANT_DESCRIPTION_RATE}")
        print(f"giant_description_files: {len(giant_descriptions)}")
        print(
            "update_rates: "
            f"description={DESCRIPTION_UPDATE_RATE}, "
            f"price={PRICE_UPDATE_RATE}, "
            f"status={STATUS_UPDATE_RATE}"
        )

        while True:
            update_count = random.randint(MIN_UPDATES_PER_LOOP, MAX_UPDATES_PER_LOOP)
            (
                updated_ids,
                updated_count,
                giant_description_count,
                description_update_count,
                price_update_count,
                status_update_count,
            ) = update_products(conn, update_count, giant_descriptions)

            print(
                f"updated: {update_count}, "
                f"updated_rows: {updated_count}, "
                f"ids: {updated_ids}, "
                f"description_updates: {description_update_count}, "
                f"giant_descriptions: {giant_description_count}, "
                f"price_updates: {price_update_count}, "
                f"status_updates: {status_update_count}"
            )
            time.sleep(SLEEP_SECONDS)

    finally:
        conn.close()


if __name__ == "__main__":
    main()