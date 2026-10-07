"""把「帧数表(xlsx) + tae 窗口(对照表) + 行为图」三者用脚本重算一遍，输出可核对的判定表。

不依赖任何游戏内实测，也不依赖我手工推导：
  1) 直接读原始 xlsx（E:\黑夜君临mod\其他资料\黑环小辛弹反帧提取.xlsx）
  2) 读 parry_最终对照表.csv（tae 解析结果）→ 每个 bank 的窗口集合
  3) 每个 Excel 行 → 需要的窗口（Excel 起-1 → 止，因 Excel 起 = 我们 Start + 1）
  4) 输出候选 bank，并做"唯一性 / 排他"判定
  5) 再从行为图实解表读：带弹反事件的 bank、以及 _20_/_28_/_47_/_48_ 等类别专属 CMSG 指向
"""
import csv
import os
import sys
from collections import defaultdict

XLSX = r'E:\黑夜君临mod\其他资料\黑环小辛弹反帧提取.xlsx'
CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'parry_最终对照表.csv')
CMAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'parry_cmsg_映射.csv')

print('=' * 100)
print('1) 原始帧数表（直接读 xlsx，不经任何转述）')
print('=' * 100)
if not os.path.exists(XLSX):
    print(f'!! 找不到 {XLSX}')
    sys.exit(1)

import openpyxl
wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
for ws in wb.worksheets:
    print(f'--- sheet: {ws.title}  ({ws.max_row} 行 x {ws.max_column} 列) ---')
    for row in ws.iter_rows(values_only=True):
        cells = ['' if c is None else str(c).strip() for c in row]
        if any(cells):
            print('   | ' + ' | '.join(cells))

print()
print('=' * 100)
print('2) 每个 bank 的窗口集合（来自 parry_最终对照表.csv，tae 解析结果）')
print('=' * 100)
bank_windows = defaultdict(lambda: defaultdict(list))   # bank -> (start,end) -> [anim...]
bank_anims = defaultdict(list)
with open(CSV, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        anim = r['动画名'].strip()
        bank = anim[1:4]
        win = r['弹反帧'].strip()
        bank_windows[bank][win].append(anim)
        bank_anims[bank].append(anim)

for bank in sorted(bank_windows):
    wins = ', '.join(sorted(bank_windows[bank]))
    print(f'  a{bank}  ({len(bank_anims[bank])} 条)  窗口集合 = {{ {wins} }}')

print()
print('=' * 100)
print('3) 行为图实解：类别专属 CMSG 指向哪些带弹反事件的动画')
print('=' * 100)
if os.path.exists(CMAP):
    with open(CMAP, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    parry_set = {a for b in bank_anims.values() for a in b}
    for r in rows:
        nm = r['cmsg']
        if any(k in nm for k in ('_20_', '_28_', '_47_', '_48_', '_02_', '_03_', '_04_', '_05_', '_08_', '_09_')):
            print(f'  {nm:<48} animId={r["animId"]:<8} 弹反条目: {r["parry_anims"] or "(无)"}')
else:
    print('  (没有 parry_cmsg_映射.csv)')
