"""侦察 HKLib tagfile XML 的真实语法（用于改写 beh_xml_map.py）。

输出：各元素标签的计数与"首次出现样例"（含后 2 行上下文），
重点是 object/field/string/integer/real/pointer/record/array 的写法，
以及指针用什么属性指向目标对象。
"""
import sys
from collections import Counter

p = sys.argv[1]
tags = Counter()
first = {}
objs = 0

with open(p, encoding='utf-8') as f:
    buf = []
    for i, line in enumerate(f, 1):
        s = line.strip()
        if not s.startswith('<'):
            continue
        tag = s.split()[0].lstrip('<').rstrip('>/')
        tags[tag] += 1
        if tag not in first:
            ctx = [s[:300]]
            for _ in range(2):
                try:
                    ctx.append(next(f).strip()[:300])
                except StopIteration:
                    break
            first[tag] = (i, ctx)
        if tag == 'object':
            objs += 1
            if objs <= 2:
                print(f'=== object #{objs} @line {i} ===')
                print(s[:300])
                for _ in range(14):
                    try:
                        print(next(f).strip()[:300])
                    except StopIteration:
                        break
                print()

print('--- 标签计数 ---')
for k, v in tags.most_common(30):
    print(f'{k:<12} {v}')
print('\n--- 每类标签的首次出现样例 ---')
for k, (i, ctx) in sorted(first.items()):
    print(f'\n[{k}] @line {i}')
    for c in ctx:
        print('   ' + c)
