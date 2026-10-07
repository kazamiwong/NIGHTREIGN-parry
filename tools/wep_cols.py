"""查 CMSG 后缀数字（02/03/20/28/47/48/49）对应 EquipParamWeapon 的哪一列。

思路：把这些候选数字在若干代表武器行里出现过的 (列名, 值) 全部列出来。
"""
import csv

P = r'C:\Users\kazamiwong\Downloads\EquipParamWeapon.csv'
CAND = {'2', '3', '20', '28', '47', '48', '49'}
WANT = {'30000000': "Buckler", '30010000': "Perfumer's Shield",
        '30750000': "Wylder's Small Shield", '31070000': 'Round Shield(中盾)'}

rows = []
dagger = []
with open(P, newline='', encoding='utf-8-sig') as f:
    r = csv.DictReader(f)
    cols = r.fieldnames
    for row in r:
        if row['ID'] in WANT:
            rows.append(row)
        nm = (row.get('Name') or '')
        if 'Dagger' in nm and len(dagger) < 2:
            dagger.append(row)

print('总列数 =', len(cols))
print('列名（含关键几列的邻居）:')
for i, c in enumerate(cols):
    if c in ('ID', 'Name', 'behaviorVariationId', 'wepType', 'weaponCategory',
             'wepmotionCategory', 'guardmotionCategory', 'wepmotionOneHandId',
             'wepmotionBothHandId', 'swordArtsParamId'):
        print(f'  [{i}] {c}')

for row in rows + dagger:
    print(f"\n=== {row['ID']} {row['Name']} ===")
    hits = [(c, row[c]) for c in cols if row.get(c) in CAND]
    print('  候选值命中:', ', '.join(f'{c}={v}' for c, v in hits) or '(无)')
    for c in ('behaviorVariationId', 'wepType', 'weaponCategory', 'wepmotionCategory',
              'guardmotionCategory', 'wepmotionOneHandId', 'wepmotionBothHandId',
              'swordArtsParamId'):
        if c in row:
            print(f'    {c:<22} = {row[c]}')
