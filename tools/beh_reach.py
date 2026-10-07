"""行为图可达性分析：从 hkRootLevelContainer 出发做 BFS（走 children + pointer refs），
判定每类 CMSG 是否"活着"，并把 _NN_ 后缀的语义空间摊开。

用法：python beh_reach.py <xml>
"""
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import beh_xml_map as m

xml = sys.argv[1]
index, classes, tags = m.load(xml)
print(f'objects = {len(index):,}')

# 反向引用表（谁指向我）
parents = defaultdict(list)
for rec in index.values():
    for cid in rec.children:
        parents[cid].append(rec.oid)
    for rid in rec.refs:
        if rid:
            parents[rid].append(rec.oid)

# 找根：hkRootLevelContainer（没有父的顶层容器）
roots = [r.oid for r in index.values() if r.cls == 'hkRootLevelContainer']
if not roots:
    roots = [r.oid for r in index.values() if r.cls == 'hkbBehaviorGraph']
print('roots =', roots[:3])

seen = set()
stack = list(roots)
while stack:
    oid = stack.pop()
    if oid in seen:
        continue
    seen.add(oid)
    rec = index.get(oid)
    if rec is None:
        continue
    for cid in rec.children:
        if cid not in seen:
            stack.append(cid)
    for rid in rec.refs:
        if rid and rid not in seen:
            stack.append(rid)
print(f'可达对象 = {len(seen):,} / {len(index):,}  (不可达 {len(index)-len(seen):,})')

cmsgs = [r for r in index.values() if r.is_cmsg]
alive = [r for r in cmsgs if r.oid in seen]
dead = [r for r in cmsgs if r.oid not in seen]
print(f'CMSG 总数 = {len(cmsgs):,}；可达 = {len(alive):,}；不可达 = {len(dead):,}')

SUF = re.compile(r'_(\d{2})_CMSG')
print('\n=== 按两位后缀统计（CMSG 名字里的 _NN_）===')
tab = defaultdict(lambda: [0, 0, set()])
for r in cmsgs:
    mm = SUF.search(r.name or '')
    if not mm:
        continue
    k = mm.group(1)
    tab[k][0 if r.oid in seen else 1] += 1
    if r.oid in seen:
        tab[k][2].add((r.name or '').split('_CMSG')[0])
print('  后缀   可达  不可达   可达的名字样例')
for k in sorted(tab, key=lambda x: int(x)):
    ok, bad, names = tab[k]
    ex = sorted(names)[:2]
    print(f'  _{k}_   {ok:>4}  {bad:>5}    {ex}')

print('\n=== 我们关心的那些 CMSG：可达性 + 父对象 ===')
KEY = ('SwordArtsOneShotShieldLeft_02_CMSG', 'SwordArtsOneShotShieldLeft_03_CMSG',
       'SwordArtsOneShotShieldLeft_04_CMSG', 'SwordArtsOneShotShieldLeft_05_CMSG',
       'SwordArtsOneShotShieldLeft_08_CMSG', 'SwordArtsOneShotShieldLeft_09_CMSG',
       'SwordArtsOneShotShieldLeft_48_CMSG', 'SwordArtsOneShot_48_CMSG',
       'SwordArtsOneShot_20_CMSG', 'SwordArtsOneShot_28_CMSG',
       'SwordArtsOneShotShieldLeft_47_CMSG', 'SwordArtsOneShot_CMSG')
for r in cmsgs:
    if r.name in KEY:
        ps = sorted({(index[p].cls, index[p].name or '') for p in parents.get(r.oid, []) if p in index})
        print(f'  {r.name:<46} {"可达" if r.oid in seen else "不可达"}  animId={r.animid}')
        for cls, nm in ps[:4]:
            print(f'        父: {cls:<34} {nm}')
