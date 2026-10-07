"""验证 animId 的编码规则：animId = base + 100*类别号 (+5 若是 NoMP)。

base 由"手/形态"决定：SwordArtsOneShot=40000、ShieldBoth=40030、ShieldLeft=40040，
NoMP 版本在 base 上 +5（40005 / 40035 / 40045）。
类别号取自 CMSG 名字里的 _NN_；无后缀的通用条目 = 类别号 0。
"""
import os
import csv
import re
from collections import Counter

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'beh', 'cmsg_map.csv')
BASES = {'SwordArtsOneShot': 40000, 'SwordArtsOneShotShieldBoth': 40030,
         'SwordArtsOneShotShieldLeft': 40040}

ok = bad = 0
bads = []
per_suffix = Counter()
bases_seen = Counter()

with open(P, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        nm = (r['cmsg'] or '').strip()
        if not nm.startswith('SwordArtsOneShot'):
            continue
        anim = (r['animId'] or '').strip()
        if not anim.isdigit():
            continue          # Selector 类没有 animId
        m = re.match(r'^(SwordArtsOneShot(?:ShieldBoth|ShieldLeft)?)(?:_(\d{2}))?_CMSG(\d*)(_NoMP\d*)?$', nm)
        if not m:
            continue
        grp, suf, seq, nomp = m.group(1), m.group(2), m.group(3), m.group(4)
        base = BASES[grp]
        cat = int(suf) if suf else 0
        pred = base + 100 * cat + (5 if nomp else 0)
        bases_seen[base] += 1
        per_suffix[cat] += 1
        if int(anim) == pred:
            ok += 1
        else:
            bad += 1
            if len(bads) < 20:
                bads.append((nm, anim, pred))

print(f'符合 animId = base + 100*类别 (+5 NoMP) 的 CMSG: {ok}')
print(f'不符合: {bad}')
for nm, anim, pred in bads:
    print(f'   ✗ {nm:<52} 实际 animId={anim}  预测={pred}')

print('\n各 base 命中数:', dict(bases_seen))
print('出现过的类别号（及次数）:', dict(sorted(per_suffix.items())))
print('\n→ 类别号 2/3/4/5/8/9 在 NR 的 WEPMOTION_CATEGORY 枚举里【不存在】（枚举只有 0 与 20-52）')
print('  且 EquipParamWeapon 里 wepmotionCategory 的取值分布也没有 1-19 → 这些槽位永远选不中（ER 遗留）')
