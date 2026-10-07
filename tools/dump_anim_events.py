"""dump 某个 bank 里指定动画的全部事件：type / flag id / start_off / end_off / start / end，
并标出「多个事件共用同一个 end_off」的情况（这决定改 End 会不会连带改到别的窗口）。

用法：python dump_anim_events.py a692 44800 [更多 animId...]
"""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tae import Tae  # noqa: E402

SRC = r'E:\黑夜君临mod\原始文件\c0000-anibnd-dcx-wanibnd\Target\INTERROOT_win64\chr\c0000\tae'
FLAG_NAME = {3: 'Set Guard Type', 5: 'Parry Window', 11: '?11', 18: 'DisableParriedAttack',
             21: 'Guard Key Input', 22: 'Cancel - Guard', 63: 'FlagAIForParryTiming',
             73: 'Parry Possible State', 119: 'TryToInvokeForceParryMode'}

bank = sys.argv[1]
anims = [int(x) for x in sys.argv[2:]]
path = os.path.join(SRC, f'{bank}.tae')
blob = open(path, 'rb').read()
t = Tae(blob)
print(f'{path}  ({len(blob):,} bytes)')

for aid in anims:
    matches = [a for a in t.anims if a.id == aid]
    if not matches:
        print(f'\n=== anim {aid}: 文件里没有这个动画 id ===')
        continue
    a = matches[0]
    print(f'\n=== anim {aid}: {len(a.events)} 个事件 ===')
    for e in a.events:
        label = ''
        if e.type == 1:
            label = 'AttackBehavior'
        elif e.type == 0:
            try:
                fid = struct.unpack_from('<i', e.params, 0)[0]
                label = f'JumpTable flag {fid} ({FLAG_NAME.get(fid, "?")})'
            except Exception:
                label = 'JumpTable'
        print(f'  type={e.type:<2} {label:<44} start_off={e.start_off:#08x} '
              f'end_off={e.end_off:#08x} start={e.start:>9.6f} end={e.end:>9.6f}')
    cnt = Counter(e.end_off for e in a.events)
    shared = {k: v for k, v in cnt.items() if v > 1}
    print(f'  → 共用同一 end_off 的情况: ' +
          (', '.join(f'{k:#08x} × {v} 个事件' for k, v in shared.items()) if shared else '无'))
    for off in shared:
        who = [e for e in a.events if e.end_off == off]
        print('     共用者: ' + ' | '.join(
            f'type{e.type}' + (f' flag{struct.unpack_from("<i", e.params, 0)[0]}' if e.type == 0 and len(e.params) >= 4 else '')
            + f' start={e.start:.4f}' for e in who))
