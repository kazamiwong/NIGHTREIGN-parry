"""按 CMSG 名字里的两位类别后缀，统计它引用了我们六个弹反 bank 的哪些条目。"""
import os
import csv
import re
from collections import defaultdict

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'beh', 'cmsg_map.csv')
BANKS = ('a692', 'a693', 'a695', 'a696', 'a697', 'a699')

suf = defaultdict(set)
cnt = defaultdict(int)
with open(P, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        nm = r['cmsg'] or ''
        m = re.search(r'_(\d{2})_CMSG', nm)
        if not m or not nm.startswith('SwordArtsOneShot'):
            continue
        k = m.group(1)
        cnt[k] += 1
        for a in (r['animations'] or '').split():
            if a[:4] in BANKS:
                suf[k].add(a)

print('后缀  该后缀的 CMSG 数   它引用的六个 bank 的弹反条目')
for k in sorted(suf, key=lambda x: int(x)):
    print(f'  _{k}_  {cnt[k]:>4}   ' + ' '.join(sorted(suf[k])))

print('\n（对照：20=Dagger 28=Curved Sword 47=Greatshield 48=Small Shield 49=Medium Shield'
      ' / 02..09 不在 WEPMOTION_CATEGORY 枚举里）')
