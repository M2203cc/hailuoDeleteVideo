import pandas as pd

# 读取关键词文件
with open('data/keywords.txt', 'r', encoding='utf-8') as f:
    keywords = f.read().strip().splitlines()

# 读取文案文件并处理
with open('data/copywriting.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    # 使用长短不一的==================分隔文案
    ads = [ad.strip() for ad in content.split('==================') if ad.strip()]

# 创建DataFrame并保存为CSV
df = pd.DataFrame({
    'text1': keywords,
    'text2': ads
})

# 保存为CSV文件
df.to_csv('data/merge.csv', index=False, encoding='utf-8-sig')