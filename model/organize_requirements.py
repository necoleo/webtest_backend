import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REQ_FILE   = BASE_DIR / 'webtest_first_train_data' / 'requirements.txt'
TRAIN_FILE = BASE_DIR / 'webtest_first_train_data' / 'first_train.jsonl'

SYSTEM_PROMPT = (
    "你是一名资深的软件测试工程师。你需要帮我生成功能测试用例，需要用完整的需求内容来理解业务关联和逻辑，"
    "然后结合你对业务的理解针对指定的需求内容生成需要的测试用例，需要考虑测试用例覆盖度，切忌不要生成重复的测试用例，不要创造需求"
)

# ---------- 1. 读取原始文件 ----------
raw_data = REQ_FILE.read_text(encoding='utf-8')

# ---------- 2. 用正则一次性提取「标题行 + {...}」块 ----------
pattern = re.compile(r'^(.*?)\n(\{[^}]+\})', re.M | re.S)
blocks = pattern.findall(raw_data)        # List[Tuple[title, dict_str]]

# ---------- 3. 读取已有 first_train.jsonl ----------
train_data = json.loads(TRAIN_FILE.read_text(encoding='utf-8'))

# 为了判重，收集现有 user.content 前半截（标题）
existing_topics = {
    msg['content'].split('。', 1)[0].strip()
    for item in train_data
    for msg in item['messages']
    if msg['role'] == 'user'
}

# ---------- 4. 逐块转成新的训练条目 ----------
for title, dict_str in blocks:
    topic = title.strip()

    # 已存在则跳过
    if topic in existing_topics:
        continue

    # 把 "{1: 'xxx', 2: 'yyy'}" 解析成字典
    try:
        rules_dict = eval(dict_str)
    except Exception as e:
        print(f"解析失败: {topic}\n{e}")
        continue

    # 拼接 user.content
    rule_part = '，'.join([f"{k}: {v}" for k, v in rules_dict.items()])
    user_content = (
        f"{topic}。需求关联的业务逻辑和关联规则为：{rule_part}"
    )

    new_item = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",    "content": user_content},
            {"role": "assistant","content": ""}
        ],
        "label": True
    }
    train_data.append(new_item)

# ---------- 5. 回写 first_train.jsonl ----------
TRAIN_FILE.write_text(
    json.dumps(train_data, ensure_ascii=False, indent=2),
    encoding='utf-8'
)
print(f"已追加 {len(train_data)} 条记录到 first_train.jsonl")