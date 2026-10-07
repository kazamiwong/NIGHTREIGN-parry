"""改帧器（改指针版）：把弹反窗的 End **指向一个已存在的时刻**，而不是改写那个 float。

为什么这样更好：
  TAE 里时间是"同一瞬间只存一份 float"，多个事件用偏移指向它。
  直接改 float（tools\\patch_frames.py）会把**所有**指向该瞬间的事件一起改掉 ——
  实测 33 个条目里有 24 个会连带把另一个 type129 事件的起点推后到 start>end（可能让该事件失效）。
  本脚本改为：把 AttackBehavior / Flag119 事件头里的 `end_off` 字段改成指向**另一个已存在的时刻槽**，
  于是窗口变长，而其它事件**一个字节都不动**。

安全性：NR/ER 的 tae 用 64 位 varint（每项 8 字节定长），所以改指针同样是**定长原地改写**，
文件长度不变；脚本还会逐字节 diff 证明"只有我们指定的那几个指针字段变了"。

用法：
  python patch_frames_repoint.py --bank a692 --anim 40000 44800 --to 20 --out mods\\xxx --apply
"""
import argparse
import os
import struct
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tae import Tae  # noqa: E402

FPS = 30.0
DEFAULT_SRC = (r'E:\黑夜君临mod\原始文件\c0000-anibnd-dcx-wanibnd'
               r'\Target\INTERROOT_win64\chr\c0000\tae')
REL_DIR = r'Target\INTERROOT_win64\chr\c0000\tae'


def window_events(anim):
    out = []
    for e in anim.events:
        if e.type == 1:
            out.append((e, 'AttackBehavior'))
        elif e.type == 0 and len(e.params) >= 4 and struct.unpack_from('<i', e.params, 0)[0] == 119:
            out.append((e, 'Flag119'))
    return out


def slot_map(anim):
    """动画里所有被事件引用过的时间槽：offset -> float 值"""
    slots = {}
    for e in anim.events:
        for off in (e.start_off, e.end_off):
            if 0 < off < 1 << 40:
                v = struct.unpack_from('<f', anim._blob, off)[0] if hasattr(anim, '_blob') else None
                slots[off] = v
    return slots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEFAULT_SRC)
    ap.add_argument('--out', required=True)
    ap.add_argument('--bank', required=True)
    ap.add_argument('--anim', nargs='+', type=int, required=True)
    ap.add_argument('--to', type=float, default=20.0, help='目标 End（帧，默认 20）')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    fname = f'{args.bank}.tae'
    src_path = os.path.join(args.src, fname)
    blob = bytearray(open(src_path, 'rb').read())
    orig = bytes(blob)
    out_path = os.path.join(args.out, REL_DIR, fname)

    tae = Tae(bytes(blob))
    print(f'{fname}: {len(blob):,} bytes, is64={tae.is64}, 目标 End = {args.to:.0f} 帧 = {args.to / FPS:.6f} s')

    # 时间槽表：offset -> 值（取全文件里出现过、且被本动画事件引用的槽）
    write_size = 8 if tae.is64 else 4
    patched_fields = []          # (file_offset, size) —— 允许变化的字节区间
    plan = []

    for aid in args.anim:
        anims = [a for a in tae.anims if a.id == aid]
        if not anims:
            print(f'  anim {aid}: 文件里没有这个动画')
            continue
        anim = anims[0]
        win = window_events(anim)
        if not win:
            print(f'  anim {aid}: 没有 AttackBehavior/Flag119 事件')
            continue
        e0 = win[0][0]
        cur_end, cur_start = e0.end, e0.start
        # 候选：本动画所有事件引用过的时间槽，且值 > 当前 End
        cand = {}
        for e in anim.events:
            for off in (e.start_off, e.end_off):
                if 0 < off < len(blob) - 4:
                    v = struct.unpack_from('<f', blob, off)[0]
                    if v > cur_end + 1e-6 and v < 50.0:
                        cand.setdefault(round(v, 6), off)
        if not cand:
            print(f'  anim {aid}: 没有任何"更晚的"时间槽可用，跳过')
            continue
        target = args.to / FPS
        best_val = min(cand, key=lambda v: (abs(v - target), v))
        best_off = cand[best_val]
        dev_f = abs(best_val - target) * FPS
        plan.append((aid, anim, win, cur_start, cur_end, best_val, best_off))
        print(f'  anim {aid}: 窗 {cur_start * FPS:.0f}->{cur_end * FPS:.0f} 帧  →  End 指向 '
              f'{best_val * FPS:.1f} 帧 (槽 {best_off:#x}，与目标差 {dev_f:.1f} 帧)')

    if not plan:
        print('没有可改的条目')
        return 1

    for aid, anim, win, cs, ce, nv, noff in plan:
        for e, lab in win:
            struct.pack_into('<q' if write_size == 8 else '<i', blob, e.end_off_pos, noff)
            patched_fields.append((e.end_off_pos, write_size))

    # ---- 验证 ----
    print('\n--- 验证 ---')
    tae2 = Tae(bytes(blob))
    ok = True
    for aid, anim, win, cs, ce, nv, noff in plan:
        a2 = [a for a in tae2.anims if a.id == aid][0]
        for e, lab in window_events(a2):
            if abs(e.end - nv) > 1e-6:
                print(f'  !! {aid} {lab} End 不是目标值: {e.end} != {nv}')
                ok = False
            if abs(e.start - cs) > 1e-6:
                print(f'  !! {aid} {lab} Start 变了: {e.start} != {cs}')
                ok = False
        print(f'  ok {aid}: 窗 {cs * FPS:.0f}->{ce * FPS:.0f} 帧  →  {cs * FPS:.0f}->{nv * FPS:.1f} 帧')

    # 逐字节 diff：变化必须全部落在我们指定的指针字段内
    allowed = set()
    for off, size in patched_fields:
        allowed.update(range(off, off + size))
    diffs = [i for i in range(len(blob)) if blob[i] != orig[i]]
    stray = [i for i in diffs if i not in allowed]
    print(f'\n变化的字节数 = {len(diffs)}（全部应落在 {len(patched_fields)} 个指针字段内）')
    if stray:
        print(f'  !! 有 {len(stray)} 个字节落在预期之外，前几个偏移: {[hex(i) for i in stray[:8]]}')
        ok = False
    else:
        print('  ✓ 只有被指定的指针字段发生变化，其它数据一字未动')
    print(f'  文件长度不变: {len(blob) == len(orig)}  ({len(blob):,})')

    if not ok:
        print('VERIFICATION FAILED - 不写盘')
        return 1
    if not args.apply:
        print('\nDRY RUN（加 --apply 才写盘）')
        return 0
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(blob)
    print(f'\nwrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
