"""生成「让所有盾统一」的精确改动清单。

输入：parry_最终对照表.csv（tae 解析出的每 bank 每动画的弹反窗，单位=帧）
规则：只改 End，不动 Start（见进度总览 6.4：改 Start 风险高、难归因）
默认目标：所有盾的弹反窗统一到 **第 20 帧结束**（= 0.666667 s，与你已验证的 a693 样本同值）

选择范围（只挑"盾真正会用到的条目"）：
  a692 通用格挡族 40000/40030/40040（中盾 + 共用此条目的其它武器）
  a692 小盾族     44800/44830/44840（wepmotionCategory 48 = Small Shield）
  a693 小圆盾族   40000/40030/40040（skill 303 → bank 693）
  a695/a696/a697/a699 四个战技 bank：正常 40000/40030/40040 + 没蓝 40005/40035/40045
排除：a002/a003/a020（行为图无引用=死数据）、a534（AutoParry_Idle）、
      a692 的 42000/42800 族（短剑=20 / 曲剑=28，不是盾）、a693 的 40240/40340（类别 2/3，NR 无武器使用）
"""
import csv
import os

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'parry_最终对照表.csv')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'parry_patch_list.csv')
FPS = 30.0
TARGET_END_FRAME = 20          # 目标：所有窗统一在第 20 帧结束

GROUPS = [
    ('中盾格挡（通用族 302→a692）', 'a692', [40000, 40030, 40040]),
    ('小盾格挡（WMC48 族 302→a692）', 'a692', [44800, 44830, 44840]),
    ('小圆盾格挡（303→a693）', 'a693', [40000, 40030, 40040]),
    ('卡利亚式奉还（305→a695）', 'a695', [40000, 40030, 40040, 40005, 40035, 40045]),
    ('风暴障壁（306→a696）', 'a696', [40000, 40030, 40040, 40005, 40035, 40045]),
    ('黄金格挡（307→a697）', 'a697', [40000, 40030, 40040, 40005, 40035, 40045]),
    ('托普斯力场（309→a699）', 'a699', [40000, 40030, 40040, 40005, 40035, 40045]),
]

# 读现状：动画名 -> (bank, animId, start_frame, end_frame)
cur = {}
with open(CSV, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        anim = r['动画名'].strip()                      # a692_040000
        bank = 'a' + anim[1:4]
        aid = int(anim[5:])
        s, e = r['弹反帧'].strip().split('->')
        cur[(bank, aid)] = (int(s), int(e))

rows = []
print(f'{"组":<34}{"bank":<6}{"animId":<8}{"动画":<16}{"现值(帧)":<12}{"改成(帧)":<12}{"增量":<6}')
print('-' * 100)
for gname, bank, aids in GROUPS:
    for aid in aids:
        key = (bank, aid)
        if key not in cur:
            print(f'{gname:<34}{bank:<6}{aid:<8}{"(无此条目)":<16}')
            continue
        s, e = cur[key]
        anim = f'{bank}_{aid:06d}'
        newend = TARGET_END_FRAME
        delta = newend - e
        rows.append((gname, bank, aid, anim, s, e, newend, delta))
        print(f'{gname:<34}{bank:<6}{aid:<8}{anim:<16}{f"{s}->{e}":<12}'
              f'{f"{s}->{newend}":<12}{delta:+d}')

with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['group', 'bank', 'animId', 'animation', 'cur_start_f', 'cur_end_f',
                'new_end_f', 'delta_f', 'new_end_sec'])
    for gname, bank, aid, anim, s, e, ne, d in rows:
        w.writerow([gname, bank, aid, anim, s, e, ne, d, f'{ne / FPS:.6f}'])
print(f'\n共 {len(rows)} 个动画条目；目标新 End = 第 {TARGET_END_FRAME} 帧 = {TARGET_END_FRAME / FPS:.6f} s')
print(f'写入 {OUT}')

banks = sorted({b for _, b, *_ in rows})
anims = sorted({a for *_, a in [(r[1], r[2]) for r in rows]})
print('\n各 bank 需要传入的 animId（工具对不存在的条目会跳过，所以可以统一传同一串）：')
all_aids = sorted({r[2] for r in rows})
print(f'  {" ".join(str(a) for a in all_aids)}')
print('\n逐 bank 命令模板：')
for b in banks:
    print(f'  python tools\\patch_frames.py --bank {b} --anim {" ".join(str(a) for a in all_aids)} '
          f'--end {TARGET_END_FRAME / FPS:.6f} --out mods\\all_shields_parry20f --apply')
