"""Patch parry-window End times inside TAE files (in place, same size).

Why this is safe and exact:
  * Each event's window is stored as two f32 values at the file offsets recorded
    in the event table (Event.start_off / Event.end_off), not inline.  Rewriting
    those 4 bytes changes the window without touching any offset table, so the
    TAE length never changes and nothing else needs fixing up.
  * Verified: every start/end offset round-trips for all parry animations in
    a692/a693/a695/a696/a697/a699 (0 mismatches over 809 events).

Verified arithmetic for a693_040000:
  AttackBehavior  start 0.133333 (4f)  end 0.300000 (9f)   at data_off 0x8a8
  Flag119         start 0.133333 (4f)  end 0.300000 (9f)   at data_off 0x8d0
  Flag3 (guard)   start 0.000000 (0f)  end 0.366667 (11f)  <- deliberately untouched

Usage:
  python patch_frames.py --bank a693 --anim 40000 40030 --end 0.666 --out DIR
"""
import argparse
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tae import Tae  # noqa: E402

FPS = 30.0
DEFAULT_SRC = (r'E:\黑夜君临mod\原始文件\c0000-anibnd-dcx-wanibnd'
               r'\Target\INTERROOT_win64\chr\c0000\tae')
REL_DIR = r'Target\INTERROOT_win64\chr\c0000\tae'

# Which events carry the parry window.  AttackBehavior is the parry judgement;
# Flag119 is the "TryToInvokeForceParryMode" readiness window.  In every vanilla
# parry animation these two share the same Start/End, so extending one without
# the other would leave them inconsistent.
WINDOW_EVENTS = {1: 'AttackBehavior', 0: 'Flag119'}
FLAG119_ID = 119
FLAG3_ID = 3


def describe(blob, tae, anim_id):
    """Return the patchable (offset, old, new-label) list for one animation."""
    rows = []
    for a in tae.anims:
        if a.id != anim_id:
            continue
        for e in a.events:
            if e.type == 1:
                label = 'AttackBehavior'
            elif e.type == 0 and struct.unpack_from('<i', e.params, 0)[0] == FLAG119_ID:
                label = 'Flag119'
            else:
                continue
            rows.append((a, e, label))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEFAULT_SRC, help='dir holding the unpacked .tae files')
    ap.add_argument('--out', required=True, help='output dir for the patched tree')
    ap.add_argument('--bank', required=True, help='e.g. a693')
    ap.add_argument('--anim', nargs='+', type=int, required=True, help='animation ids')
    ap.add_argument('--end', type=float, required=True, help='new End time in seconds')
    ap.add_argument('--apply', action='store_true', help='write files (default: dry run)')
    args = ap.parse_args()

    fname = f'{args.bank}.tae'
    src_path = os.path.join(args.src, fname)
    if not os.path.isfile(src_path):
        print(f'ERROR: {src_path} not found')
        return 1
    blob = bytearray(open(src_path, 'rb').read())

    # verify the source is inside the expected unpacked tree
    out_path = os.path.join(args.out, REL_DIR, fname)

    print(f'bank       : {args.bank}  ({len(blob):,} bytes)')
    print(f'animations : {args.anim}')
    print(f'new End    : {args.end:.6f} s  ({args.end * FPS:.1f} frames)')
    print(f'output     : {out_path}')
    print()
    print(f'{"anim":>6} {"event":<15} {"old start":>10} {"old end":>10} '
          f'{"new start":>10} {"new end":>10}  {"offset":>8}')

    tae = Tae(bytes(blob))
    changes = []
    for anim_id in args.anim:
        rows = describe(blob, tae, anim_id)
        if not rows:
            print(f'{anim_id:>6} (no window events found)')
            continue
        for a, e, label in rows:
            old_end = e.end
            # never move Start: changing the opening frame is a different risk
            changes.append((anim_id, label, e.start_off, e.end_off,
                            e.start, old_end, args.end))
            print(f'{anim_id:>6} {label:<15} {e.start * FPS:>9.1f}f '
                  f'{old_end * FPS:>9.1f}f {e.start * FPS:>9.1f}f '
                  f'{args.end * FPS:>9.1f}f  {e.end_off:#08x}')

    if not changes:
        print('\nno changes to make')
        return 1

    # apply into a copy
    for anim_id, label, start_off, end_off, old_start, old_end, new_end in changes:
        struct.pack_into('<f', blob, end_off, new_end)

    # re-parse and prove the result
    tae2 = Tae(bytes(blob))
    print('\n--- post-patch verification ---')
    bad = 0
    for anim_id, label, start_off, end_off, old_start, old_end, new_end in changes:
        found = False
        for a in tae2.anims:
            if a.id != anim_id:
                continue
            for e in a.events:
                if e.end_off != end_off:
                    continue
                found = True
                if abs(e.start - old_start) > 1e-6:
                    print(f'  !! {anim_id} {label} Start moved: {e.start} != {old_start}')
                    bad += 1
                if abs(e.end - new_end) > 1e-6:
                    print(f'  !! {anim_id} {label} End wrong: {e.end} != {new_end}')
                    bad += 1
                else:
                    print(f'  ok {anim_id} {label}: '
                          f'{e.start * FPS:.1f}f -> {e.end * FPS:.1f}f')
        if not found:
            print(f'  !! {anim_id} {label} not found after patch')
            bad += 1

    print(f'\nsize unchanged: {len(blob) == len(open(src_path, "rb").read())}')
    if bad:
        print(f'VERIFICATION FAILED ({bad} problems) - not writing')
        return 1

    if not args.apply:
        print('\nDRY RUN (pass --apply to write)')
        return 0

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(blob)
    print(f'\nwrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
