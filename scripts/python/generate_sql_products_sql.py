# Python推奨:
# - 10万件の長文description生成がしやすい
# - UUID、SKU、カテゴリ分散、バッチINSERT生成が簡単
# - bashより保守しやすい
#
# 使い方:
#   python3 generate_products_sql.py
#
# 生成物:
#   insert_products.sql
#
# 適用例:
#   mysql -h <aurora-endpoint> -P 3306 -u admin -p dmsapp < insert_products.sql

import random
import uuid
from pathlib import Path

OUTPUT_FILE = "insert_products.sql"
TOTAL_ROWS = 100_000
BATCH_SIZE = 1000

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
    "コンパクト", "大容量", "折りたたみ可能", "メンテナンスしやすい", "長時間使用向け",
    "家庭向け", "業務向け", "デザイン性が高い", "高級感のある", "扱いやすい", "初心者向け",
]

FEATURES = [
    "タイマー機能", "温度調整機能", "自動停止機能", "バッテリー残量表示", "抗菌加工",
    "取り外し可能パーツ", "高効率フィルター", "静音モード", "収納しやすい設計",
    "手入れしやすい構造", "スマートフォン連携", "USB充電対応", "省スペース設計",
    "長寿命モーター", "高い安定性", "汚れに強い表面加工",
]

SCENES = [
    "在宅勤務", "毎日の通勤", "オフィス利用", "家庭内利用", "一人暮らし", "ファミリー利用",
    "週末のまとめ買い", "来客時", "日常清掃", "朝の忙しい時間", "狭い部屋", "長時間作業",
]

MATERIALS = [
    "アルミ素材", "樹脂素材", "ステンレス素材", "通気性の高い生地", "耐久性のある合成素材",
    "傷が目立ちにくい表面材", "軽量フレーム", "高反発クッション材",
]

BRANDS = [
    "Aster", "Brillia", "Crest", "D-NEXT", "EverFine", "Flux", "Glow", "Horizon", "Iris", "J-Works"
]

STATUS_VALUES = ["active"] * 97 + ["inactive"] * 3


def sql_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")


def make_name(category_name: str, i: int) -> str:
    brand = BRANDS[i % len(BRANDS)]
    model = f"{category_name}{brand}-{i:06d}"
    return model


def make_sku(i: int) -> str:
    return f"SKU-{i:08d}"


def make_description(category_name: str, i: int) -> str:
    random.seed(i)

    chosen_adj = random.sample(ADJECTIVES, 4)
    chosen_feat = random.sample(FEATURES, 3)
    chosen_scene = random.sample(SCENES, 2)
    chosen_material = random.sample(MATERIALS, 2)

    paragraphs = [
        (
            f"この{category_name}は{chosen_adj[0]}で{chosen_adj[1]}な設計を採用しており、"
            f"{chosen_scene[0]}でも扱いやすいモデルです。"
            f"{chosen_feat[0]}と{chosen_feat[1]}を備え、利用者の負担を抑えながら安定した使い心地を提供します。"
        ),
        (
            f"本製品は{chosen_material[0]}と{chosen_material[1]}を組み合わせ、"
            f"{chosen_adj[2]}かつ{chosen_adj[3]}な使い勝手を目指しています。"
            f"{chosen_scene[1]}を想定した設計となっており、長時間の利用でも扱いやすいことが特徴です。"
        ),
        (
            f"さらに、{chosen_feat[2]}や収納しやすい構造を取り入れることで、"
            f"日常利用から継続利用まで幅広いシーンで性能を発揮します。"
            f"検索検証用のテキストとして、軽量、防水、通勤向け、高耐久、静音、省エネ、高性能、多機能、"
            f"コンパクト、大容量、家庭向け、業務向けというキーワードを意図的に含めています。"
        ),
    ]
    return " ".join(paragraphs)


def row_sql(i: int) -> str:
    category_id, category_name = random.choice(LEAF_CATEGORIES)
    product_uuid = str(uuid.uuid4())
    sku = make_sku(i)
    name = make_name(category_name, i)
    description = make_description(category_name, i)
    price = round(random.uniform(980.0, 49800.0), 2)
    status = random.choice(STATUS_VALUES)

    return (
        f"('{sql_escape(product_uuid)}', "
        f"{category_id}, "
        f"'{sql_escape(sku)}', "
        f"'{sql_escape(name)}', "
        f"'{sql_escape(description)}', "
        f"{price:.2f}, "
        f"'{status}')"
    )


def main() -> None:
    out = Path(OUTPUT_FILE)

    with out.open("w", encoding="utf-8") as f:
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")

        for start in range(1, TOTAL_ROWS + 1, BATCH_SIZE):
            end = min(start + BATCH_SIZE - 1, TOTAL_ROWS)
            f.write(
                "INSERT INTO products "
                "(uuid, category_id, sku, name, description, price, status)\nVALUES\n"
            )

            values = [row_sql(i) for i in range(start, end + 1)]
            f.write(",\n".join(values))
            f.write(";\n\n")

    print(f"generated: {OUTPUT_FILE} ({TOTAL_ROWS} rows)")


if __name__ == "__main__":
    main()