"""挖 CategorySelector 的选择机制：generator 数组顺序 + 索引变量名。

假设：这些 `_NN_CMSG` 是按索引取用的，`NN` 可能就是索引值（或驱动索引的变量值）。
本脚本输出：
  * 每个 CategorySelector 的 generators 数组长度与逐位内容（含 null 槽）
  * 它的 selectedgeneratorindex / indexselector
  * indexselector 指向的 hkbVariableBindingSet 的成员路径与 variableIndex
  * hkbBehaviorGraphStringData 的 variableNames[variableIndex] → 变量名
"""
import sys
from collections import Counter

import xml.etree.ElementTree as ET

XML = sys.argv[1]
WANT = ('SwordArtsOneShot CategorySelector', 'SwordArtsOneShotShieldLeft CategorySelector',
        'SwordArtsOneShotShieldBoth CategorySelector')


class O:
    __slots__ = ('oid', 'cls', 'data', 'kids', 'n')

    def __init__(self, oid, cls):
        self.oid = oid
        self.cls = cls
        self.data = {}      # field name -> [(kind, value), ...] 保序
        self.kids = []      # 内联子对象
        self.n = 0


def load(path):
    index, types = {}, {}
    stack, pstack = [], []
    cur_type = None
    for ev, el in ET.iterparse(path, events=('start', 'end')):
        tag, a = el.tag, el.attrib
        if ev == 'start':
            if tag == 'type':
                cur_type = a.get('id')
            elif tag == 'name' and cur_type:
                if a.get('value'):
                    types[cur_type] = a['value']
            elif tag == 'object':
                oid = a.get('id') or f'anon{len(index)}'
                rec = O(oid, types.get(a.get('typeid')) or a.get('typeid') or '?')
                index[oid] = rec
                if stack:
                    index[stack[-1]].kids.append(oid)
                stack.append(oid)
            elif tag == 'field' and stack:
                nm = a.get('name') or ''
                if nm.startswith('m_'):
                    nm = nm[2:]
                pstack.append([stack[-1], nm.lower(), []])
        else:
            if tag == 'field' and pstack:
                oid, nm, vals = pstack.pop()
                if vals:
                    index[oid].data.setdefault(nm, []).extend(vals)
            elif tag == 'object':
                if stack:
                    stack.pop()
            elif tag == 'pointer':
                if pstack and a.get('id'):
                    pstack[-1][2].append(('ptr', a['id']))
            elif tag in ('string', 'integer', 'bool'):
                if pstack:
                    pstack[-1][2].append((tag, a.get('value')))
            el.clear()
    return index


index = load(XML)
print(f'objects = {len(index):,}')

# 变量名表
sdata = [r for r in index.values() if r.cls == 'hkbBehaviorGraphStringData']
print(f'hkbBehaviorGraphStringData 对象数 = {len(sdata)}')
varnames = []
for s in sdata:
    for cand in ('variablenames', 'variableNames'.lower(), 'variablenames'.lower()):
        if cand in s.data:
            varnames = [v for k, v in s.data[cand] if k == 'string']
            break
    if varnames:
        break
print(f'变量名数量 = {len(varnames)}; 前 8 个 = {varnames[:8]}')


def describe(oid, depth=0):
    r = index.get(oid)
    if r is None:
        return f'{oid}(?)'
    nm = ''
    for k, v in r.data.get('name', []):
        if k == 'string':
            nm = v
            break
    anim = ''
    for k, v in r.data.get('animid', []):
        if k == 'integer':
            anim = v
            break
    return f'{r.cls}:{nm or "-"}' + (f'[animId={anim}]' if anim else '')


for want in WANT:
    for r in index.values():
        nm = ''
        for k, v in r.data.get('name', []):
            if k == 'string':
                nm = v
        if nm != want:
            continue
        gen = r.data.get('generators', [])
        print('\n' + '=' * 100)
        print(f'{r.cls}  "{nm}"  oid={r.oid}  generators 数组长度 = {len(gen)}')
        print('=' * 100)
        nulls = sum(1 for k, v in gen if v == 'object0')
        print(f'  其中 null(object0) 槽 = {nulls}；非空 = {len(gen) - nulls}')
        for i, (k, v) in enumerate(gen):
            if v == 'object0':
                continue
            print(f'  [{i:>3}] {v:<12} {describe(v)}')
        print(f'  selectedgeneratorindex = {r.data.get("selectedgeneratorindex")}')
        print(f'  selectedindexcanchangeafteractivate = {r.data.get("selectedindexcanchangeafteractivate")}')
        idxs = r.data.get('indexselector', [])
        print(f'  indexselector = {idxs}')
        for k, vid in idxs:
            if k != 'ptr' or vid == 'object0':
                continue
            vb = index.get(vid)
            if vb is None:
                continue
            print(f'    -> {vid} {vb.cls}')
            for fname in ('bindings', 'memberpath', 'variableindex', 'bitindex', 'bindingtype'):
                if fname in vb.data:
                    print(f'       {fname} = {vb.data[fname][:8]}')
            # 变量名
            for fname in ('variableindex',):
                for kk, vv in vb.data.get(fname, []):
                    if kk == 'integer' and vv and vv.isdigit():
                        vi = int(vv)
                        if vi < len(varnames):
                            print(f'       -> variableNames[{vi}] = {varnames[vi]!r}')
