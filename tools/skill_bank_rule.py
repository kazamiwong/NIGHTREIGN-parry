"""验证机制假设：动画 bank = 600 + SwordArtsParam.swordArtsType。

做法：读 SwordArtsParam.csv，对每一行算 600+swordArtsType，检查 tae 目录里是否有 a{NNN}.tae。
若命中率很高（尤其盾牌 300-309 那段全中），则"技能 → bank"就是数据可证的事实，
而不是靠帧窗排他推出来的。
"""
import csv
import os

SA = r'C:\Users\kazamiwong\Downloads\SwordArtsParam.csv'
TAE = r'E:\黑夜君临mod\原始文件\c0000-anibnd-dcx-wanibnd\Target\INTERROOT_win64\chr\c0000\tae'

have = set()
for fn in os.listdir(TAE):
    if fn.endswith('.tae') and len(fn) == 8 and fn[1:4].isdigit():
        have.add(int(fn[1:4]))
print(f'tae 文件数 = {len(os.listdir(TAE))}, 其中 aNNN.tae 解析出 {len(have)} 个 bank 号')
print('存在 bank 号的分布（按十位分组）:')
groups = {}
for b in sorted(have):
    groups.setdefault(b // 10 * 10, []).append(b)
for g in sorted(groups):
    print(f'  a{g:03d}-a{g+9:03d}: {len(groups[g]):>3} 个')

with open(SA, newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

print('\n=== 600 + swordArtsType 是否命中现有 tae ===')
hit = miss = 0
misses = []
for r in rows:
    sid = (r.get('ID') or '').strip()
    st = (r.get('swordArtsType') or '').strip()
    if not sid.isdigit() or not st.lstrip('-').isdigit():
        continue
    bank = 600 + int(st)
    ok = bank in have
    if ok:
        hit += 1
    else:
        miss += 1
        misses.append((sid, st, bank, (r.get('Name') or '')[:34]))
print(f'命中 {hit} / 未命中 {miss}')

print('\n--- 盾牌段 300-309 / 1196（我们关心的）---')
for r in rows:
    sid = (r.get('ID') or '').strip()
    if sid in ('300', '301', '302', '303', '304', '305', '306', '307', '308', '309', '1196'):
        st = (r.get('swordArtsType') or '').strip()
        bank = 600 + int(st) if st.lstrip('-').isdigit() else None
        print(f'  skill {sid:<5} swordArtsType={st:<5} -> a{bank}  {"✅ 存在" if bank in have else "❌ 不存在"}  {r.get("Name","")}')

print('\n--- 未命中样例（前 25）---')
for sid, st, bank, nm in misses[:25]:
    print(f'  skill {sid:<6} type={st:<5} -> a{bank:<4} {nm}')
