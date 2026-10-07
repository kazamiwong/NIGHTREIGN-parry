"""对「所有盾统一」清单里的 33 个条目做逐条安全审计。

对每个 (bank, animId)：
  * 找出弹反窗事件（type 1 = AttackBehavior；type 0 且首参数=119 = Flag119）
  * 检查改 End 会连带影响谁：
      - 其它事件的 end_off == 本窗 end_off  → 它们的 End 也会变（同值，通常无害）
      - 其它事件的 start_off == 本窗 end_off → **它们的 Start 会跟着移**（真实副作用，可能 start>end）
  * 把"新 End 之后、原本排在其后的时间边界"列出来，看会不会错位
"""
import os
import struct
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tae import Tae  # noqa: E402

SRC = r'E:\黑夜君临mod\原始文件\c0000-anibnd-dcx-wanibnd\Target\INTERROOT_win64\chr\c0000\tae'
FPS = 30.0
NEW_END = 20 / FPS

PLAN = {
    'a692': [40000, 40030, 40040, 44800, 44830, 44840],
    'a693': [40000, 40030, 40040],
    'a695': [40000, 40030, 40040, 40005, 40035, 40045],
    'a696': [40000, 40030, 40040, 40005, 40035, 40045],
    'a697': [40000, 40030, 40040, 40005, 40035, 40045],
    'a699': [40000, 40030, 40040, 40005, 40035, 40045],
}

cache = {}
summary = defaultdict(int)
detail = []

for bank, aids in PLAN.items():
    path = os.path.join(SRC, f'{bank}.tae')
    if bank not in cache:
        cache[bank] = Tae(open(path, 'rb').read())
    t = cache[bank]
    for aid in aids:
        anims = [a for a in t.anims if a.id == aid]
        if not anims:
            detail.append((bank, aid, 'NO-ANIM', '', ''))
            summary['NO-ANIM'] += 1
            continue
        a = anims[0]
        win = []
        for e in a.events:
            if e.type == 1:
                win.append((e, 'AttackBehavior'))
            elif e.type == 0 and len(e.params) >= 4 and struct.unpack_from('<i', e.params, 0)[0] == 119:
                win.append((e, 'Flag119'))
        if not win:
            types = sorted({e.type for e in a.events})
            detail.append((bank, aid, 'NO-WINDOW-EVENT', f'事件类型={types}', f'{len(a.events)} 个事件'))
            summary['NO-WINDOW-EVENT'] += 1
            continue
        e0, lab = win[0]
        end_off, start_off = e0.end_off, e0.start_off
        others_end = [e for e in a.events if e.end_off == end_off and (e.start_off, e.type) != (start_off, e.type)]
        others_start = [e for e in a.events if e.start_off == end_off]
        bad = [e for e in others_start if e.end < NEW_END]
        if bad:
            verdict = f'SIDE-EFFECT: {len(others_start)} 个事件的 Start 会跟着移到 {NEW_END:.4f}，其中 {len(bad)} 个会变成 start>end'
            summary['SIDE-EFFECT'] += 1
        elif others_start:
            verdict = f'共享槽: {len(others_start)} 个事件的 Start 会跟着移（但它们的 end 仍大于新值）'
            summary['SHARED-OK'] += 1
        else:
            verdict = 'SAFE: 该 End 槽只有本窗事件使用'
            summary['SAFE'] += 1
        detail.append((bank, aid, verdict,
                       f'窗 {e0.start * FPS:.0f}->{e0.end * FPS:.0f} 帧 (start_off={start_off:#x} end_off={end_off:#x})',
                       '; '.join(f'type{e.type} start={e.start:.4f} end={e.end:.4f}' for e in others_start[:3])))

print(f'{"bank":<7}{"animId":<8}{"判定":<70}备注')
print('-' * 150)
for bank, aid, verdict, note, extra in detail:
    print(f'{bank:<7}{aid:<8}{verdict:<70}{note[:60]}')
    if extra:
        print(f'{"":<85}{extra[:80]}')

print('\n统计:', dict(summary))
