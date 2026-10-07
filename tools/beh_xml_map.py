#!/usr/bin/env python3
"""beh_xml_map.py (v2) —— 解析 HKLib 导出的 **tagfile XML**，建立「CMSG ↔ 弹反动画名」映射。

v2 说明：v1 是按 `hkobject/hkparam`（packfile 风格）写的，实测 HKLib.CLI v0.1.3-NR 输出的是
**tagfile XML**，真实语法如下（已在 `Behaviors\\c0000.xml` 上核实）：

    <hktagfile version="3">
      <type id="type34"><name value="hkbBehaviorGraph" /><format value="7" />...</type>
      ...
      <object id="object2" typeid="type34">
        <record>
          <field name="userData"><integer value="0" /></field>
          <field name="variableBindingSet"><pointer id="object0" /></field>
          <field name="generators">
            <array count="3" elementtypeid="type9">
              <pointer id="object77" />
            </array>
          </field>
          <field name="name"><string value="GuardOnSmall_CMSG" /></field>
        </record>
      </object>

要点：
  * 类型名来自 `<type id><name value=...>`，且**新类型会在首次使用前就近补声明**（不能只读文件头）
  * `<record>` / `<array>` 是透明的；`<field name=...>` 归属最近的 enclosing `<object>`
  * 值：`<string value>` / `<integer value>` / `<bool value>`；引用：`<pointer id="objectN" />`
  * 字段名无 `m_` 前缀，但仍做归一化（去 m_、转小写）以兼容两种风格

依据（权威）：ERClipGeneratorTool README + BehaviorGraphViewModel.cs
  * clip generator 的动画名字段形如 `a[TaeId]_[AnimationId]`
  * 一个 CMSG(`CustomManualSelectorGenerator`) 代表**一个 animId**，内含该 animId 的全部 clip generator

用法：
  python beh_xml_map.py <xml> probe               结构侦察（对象数/类名/CMSG 样例）
  python beh_xml_map.py <xml> raw <关键词> [N]     原样打印含关键词的行 + 后 N 行
  python beh_xml_map.py <xml> map [--out F]       CMSG → 动画 全表
  python beh_xml_map.py <xml> find <关键词>        按 CMSG 名字过滤
  python beh_xml_map.py <xml> anim <动画名>        反查：该动画被哪些 CMSG 引用
  python beh_xml_map.py <xml> parry              与 parry_最终对照表.csv 交叉
"""
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

ANIM_RE = re.compile(r'(?<![0-9A-Za-z])a\d{3}_\d{6}')
NAME_KEYS = ('name', 'animationname')
ANIMID_KEYS = ('animid', 'animationid')


def norm_key(pname):
    n = pname or ''
    if n.startswith('m_'):
        n = n[2:]
    return n.lower()


class Obj:
    __slots__ = ('oid', 'cls', 'depth', 'anims', 'refs', 'children', 'named', 'animid', 'params')

    def __init__(self, oid, cls, depth):
        self.oid = oid
        self.cls = cls
        self.depth = depth
        self.anims = set()
        self.refs = set()
        self.children = []
        self.named = {}
        self.animid = None
        self.params = []

    @property
    def name(self):
        for k in NAME_KEYS:
            v = self.named.get(k)
            if v:
                return v
        return None

    @property
    def is_cmsg(self):
        return 'manualselectorgenerator' in (self.cls or '').lower()


def load(xml_path):
    """流式解析 tagfile XML。返回 (index, class_counter, tag_names)。"""
    index = {}
    types = {}
    stack = []
    pstack = []
    class_counter = Counter()
    tag_names = Counter()
    cur_type = None

    for event, elem in ET.iterparse(xml_path, events=('start', 'end')):
        tag = elem.tag
        a = elem.attrib
        if event == 'start':
            tag_names[tag] += 1
            if tag == 'type':
                cur_type = a.get('id')
            elif tag == 'name' and cur_type is not None:
                if a.get('value'):
                    types[cur_type] = a['value']
            elif tag == 'object':
                oid = a.get('id') or f'object_anon{len(index)}'
                cls = types.get(a.get('typeid')) or a.get('typeid') or '?'
                rec = Obj(oid, cls, len(stack))
                index[oid] = rec
                class_counter[cls] += 1
                if stack:
                    p = index.get(stack[-1])
                    if p is not None:
                        p.children.append(oid)
                stack.append(oid)
            elif tag == 'field':
                if stack:
                    pstack.append([stack[-1], norm_key(a.get('name'))])
        else:
            if tag == 'field':
                if pstack:
                    pstack.pop()
            elif tag == 'object':
                if stack:
                    stack.pop()
            elif tag == 'pointer':
                if pstack:
                    oid, pname = pstack[-1]
                    rec = index.get(oid)
                    if rec is not None:
                        rec.refs.add(a.get('id'))
                        if pname and len(rec.params) < 60 and pname not in rec.params:
                            rec.params.append(pname)
            elif tag in ('string', 'integer', 'bool'):
                v = a.get('value')
                if v and pstack:
                    oid, pname = pstack[-1]
                    rec = index.get(oid)
                    if rec is not None:
                        rec.note(pname, v)
            elem.clear()
    return index, class_counter, tag_names


def _note(self, pname, text):
    if pname and pname not in self.params and len(self.params) < 60:
        self.params.append(pname)
    for am in ANIM_RE.findall(text):
        self.anims.add(am)
    if pname in NAME_KEYS and not self.named.get(pname):
        self.named[pname] = text
    if pname in ANIMID_KEYS and self.animid is None and text.lstrip('-').isdigit():
        self.animid = int(text)


Obj.note = _note


def resolve(index, oid, seen):
    if oid in seen or oid is None:
        return set()
    seen.add(oid)
    rec = index.get(oid)
    if rec is None:
        return set()
    out = set(rec.anims)
    for c in rec.children:
        out |= resolve(index, c, seen)
    for rid in rec.refs:
        out |= resolve(index, rid, seen)
    return out


def direct_anims(index, rec):
    """只看**直接** generator 引用/子对象，不做深递归。"""
    out = set()
    detail = []
    for cid in list(rec.children) + [r for r in rec.refs if r not in rec.children]:
        c = index.get(cid)
        if c is None:
            continue
        detail.append((cid, c.cls, sorted(c.anims)[:3]))
        out |= c.anims
    return out, detail


def load_parry_names(csv_path):
    names = set()
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            n = (row.get('动画名') or '').strip()
            if n:
                names.add(n)
    return names


def cmd_raw(xml, key, after=6):
    after = int(after)
    with open(xml, 'r', encoding='utf-8', errors='replace') as f:
        pending = 0
        for i, line in enumerate(f, 1):
            if key in line:
                pending = after
                print(f'--- line {i} ---')
                print(line.rstrip()[:1500])
            elif pending:
                pending -= 1
                print(line.rstrip()[:1500])
    return 0


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    xml, mode = sys.argv[1], sys.argv[2]

    if mode == 'raw':
        return cmd_raw(xml, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 6)

    index, classes, tags = load(xml)
    print(f'objects = {len(index):,}')
    print('类名 top: ' + ', '.join(f'{c}={n}' for c, n in classes.most_common(12)))
    cmsgs = [r for r in index.values() if r.is_cmsg]
    print(f'CMSG = {len(cmsgs):,}')

    if mode == 'probe':
        print('\n-- CMSG 样例（前 10）--')
        for r in cmsgs[:10]:
            print(f'  {r.oid:<12} {r.cls:<36} name={r.name} animId={r.animid} '
                  f'children={len(r.children)} refs={len(r.refs)}')
            print(f'      params: {", ".join(r.params[:12])}')
        print('\n-- CMSG 上见到的字段名 --')
        pc = Counter()
        for r in cmsgs:
            pc.update(r.params)
        print('  ' + ', '.join(f'{p}({n})' for p, n in pc.most_common(20)))
        print('\n-- 含动画名的对象类名分布 --')
        for c, n in Counter(r.cls for r in index.values() if r.anims).most_common(12):
            print(f'  {c:<40} {n}')
        return 0

    if not cmsgs:
        print('\n⚠️ 没找到 CMSG')
        return 2

    if mode == 'find':
        key = sys.argv[3].lower()
        for r in sorted(cmsgs, key=lambda x: x.name or ''):
            if key in (r.name or '').lower():
                own, detail = direct_anims(index, r)
                print(f'{r.name}  ({r.cls}, animId={r.animid}, oid={r.oid})')
                print(f'  直接 generator: {len(detail)} 个；直接动画: {sorted(own)}')
                for cid, cls, am in detail[:12]:
                    print(f'    {cid:<12} {cls:<34} {am}')
                allanims = sorted(resolve(index, r.oid, set()))
                print(f'  闭包动画({len(allanims)}): {allanims}')
        return 0

    if mode == 'anim':
        key = sys.argv[3]
        hit = 0
        for r in sorted(cmsgs, key=lambda x: x.name or ''):
            if key in resolve(index, r.oid, set()):
                hit += 1
                own, _ = direct_anims(index, r)
                mark = '直接' if key in own else '间接'
                print(f'  {r.name}  (animId={r.animid}, {mark})')
        print(f'\n{key} 被 {hit} 个 CMSG 引用')
        return 0

    if mode == 'map':
        out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
        rows = []
        for r in sorted(cmsgs, key=lambda x: (x.name or '')):
            anims = sorted(resolve(index, r.oid, set()))
            banks = sorted({a[:4] for a in anims})
            rows.append((r.name, r.cls, r.animid, len(anims), ' '.join(banks), ' '.join(anims)))
            head = ' '.join(anims[:6]) + (' ...' if len(anims) > 6 else '')
            print(f'{(r.name or "?"):<46} animId={str(r.animid):<8} banks={" ".join(banks):<26} {head}')
        if out:
            with open(out, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(['cmsg', 'class', 'animId', 'anim_count', 'banks', 'animations'])
                w.writerows(rows)
            print(f'\nwrote {out}')
        return 0

    if mode == 'parry':
        csv_path = sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv else \
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parry_最终对照表.csv')
        parry = load_parry_names(csv_path)
        print(f'\n对照表弹反动画 = {len(parry)} 条（{csv_path}）')
        bank_anim = defaultdict(set)
        for a in parry:
            bank_anim[a[:4]].add(a)

        hits = defaultdict(set)
        rows = []
        print('\n' + '=' * 100)
        print('引用了弹反动画的 CMSG')
        print('=' * 100)
        for r in sorted(cmsgs, key=lambda x: (x.name or '')):
            anims = resolve(index, r.oid, set())
            p = sorted(anims & parry)
            if not p:
                continue
            for a in p:
                hits[a].add(r.name)
            banks = sorted({a[:4] for a in p})
            rows.append((r.name, r.animid, len(p), ' '.join(banks), ' '.join(p)))
            print(f'{(r.name or "?"):<44} animId={str(r.animid):<7} banks={" ".join(banks):<24} {len(p):>2}条: {" ".join(p)}')

        print('\n' + '=' * 100)
        print('反过来：每条弹反动画被哪些 CMSG 引用（按 bank 分组）')
        print('=' * 100)
        for bank in sorted(bank_anim):
            print(f'\n[{bank}] {len(bank_anim[bank])} 条弹反动画')
            for a in sorted(bank_anim[bank]):
                owners = sorted(x for x in hits.get(a, ()) if x)
                print(f'  {a}  <-  ' + (', '.join(owners) if owners else '⚠️ 无 CMSG 引用'))

        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parry_cmsg_映射.csv')
        with open(out, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['cmsg', 'animId', 'parry_count', 'banks', 'parry_anims'])
            w.writerows(rows)
        print(f'\nwrote {out}')
        return 0

    print(f'unknown mode: {mode}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
