"""用新增的两列（弹反霸体帧 / 特殊弹反战灰特效帧）去 tae 里找对应事件。

思路：把每个动画的所有事件按（start, end）折算成帧，与 xlsx 的列做精确匹配
（沿用已确立的口径：Excel 起 = 我们 Start + 1、Excel 止 = 我们 End）。
命中的事件类型/flag id 就是那一列的真身。
"""
import os
import struct
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tae import Tae  # noqa: E402

XLSX = r'E:\黑夜君临mod\其他资料\黑环小辛弹反帧提取.xlsx'
SRC = r'E:\黑夜君临mod\原始文件\c0000-anibnd-dcx-wanibnd\Target\INTERROOT_win64\chr\c0000\tae'
FPS = 30.0
FLAG = {3: 'Set Guard Type', 5: 'Parry Window', 18: 'DisableParriedAttack',
        22: 'Cancel - Guard', 63: 'FlagAIForParryTiming', 73: 'Parry Possible State',
        119: 'TryToInvokeForceParryMode'}

# xlsx 行名 -> (bank, animId)（正常/没蓝分别对应 40000 族 / 40005 族）
ROW2ANIM = {
    '拳头格挡': ('a692', 40000), '钩爪格挡': ('a692', 40000), '中盾格挡': ('a692', 40000),
    '刺剑格挡': ('a692', 40000), '曲剑格挡': ('a692', 42800), '短剑格挡': ('a692', 42000),
    '小盾格挡': ('a692', 44800), '小圆盾格挡': ('a693', 40000),
    '黄金格挡 (正常)': ('a697', 40000), '黄金格挡 (没蓝)': ('a697', 40005),
    '风暴障壁 (正常)': ('a696', 40000), '风暴障壁 (没蓝)': ('a696', 40005),
    '托普斯的力场 (正常)': ('a699', 40000), '托普斯的力场 (没蓝)': ('a699', 40005),
    '卡利亚式奉还 (正常)': ('a695', 40000), '卡利亚式奉还 (没蓝)': ('a695', 40005),
}

wb = openpyxl.load_workbook(XLSX, data_only=True)
ws = wb['Sheet1']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def label(e):
    if e.type == 1:
        return 'AttackBehavior(type1)'
    if e.type == 0 and len(e.params) >= 4:
        f = struct.unpack_from('<i', e.params, 0)[0]
        return f'Flag{f} {FLAG.get(f, "?")}'
    return f'type{e.type}'


cache = {}
print(f'{"xlsx 行":<20}{"动画":<16}{"弹反":<10}{"霸体":<10}{"霸体命中事件":<34}{"特效":<10}特效命中事件')
print('-' * 150)
for r in rows[1:]:
    name = (r[0] or '').strip()
    if not name or name not in ROW2ANIM:
        continue
    bank, aid = ROW2ANIM[name]
    p_s, p_e = num(r[1]), num(r[2])
    h_s, h_e = num(r[5]), num(r[6])
    v_s, v_e = num(r[8]), num(r[9])
    if bank not in cache:
        cache[bank] = Tae(open(os.path.join(SRC, f'{bank}.tae'), 'rb').read())
    anim = [a for a in cache[bank].anims if a.id == aid]
    if not anim:
        print(f'{name:<20}{bank}_{aid:<10}  (文件里没有)')
        continue
    evs = anim[0].events
    # 折算成帧
    def fr(x):
        return round(x * FPS)

    def find(s, e):
        if s is None or e is None:
            return None
        hits = [label(ev) for ev in evs if fr(ev.start) == s - 1 and fr(ev.end) == e]
        return ', '.join(sorted(set(hits))[:2]) if hits else '（没找到）'

    print(f'{name:<20}{bank}_{aid:<10}{f"{p_s}->{p_e}":<10}'
          f'{f"{h_s}->{h_e}" if h_s else "-":<10}{find(h_s, h_e) or "-":<34}'
          f'{f"{v_s}->{v_e}" if v_s else "-":<10}{find(v_s, v_e) or "-"}')
