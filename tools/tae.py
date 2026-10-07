"""Elden Ring / Nightreign TAE (TimeAct) reader, ported from SoulsFormatsNEXT.

Verified against SoulsFormats/Formats/TAE/{TAE,Animation,Event}.cs

TAE header (little-endian, VarintLong=true for ER/SDT format 0x1000D):
  0x00 char[4] 'TAE '
  0x04 u8  bigEndian | 0x05 u8 0 | 0x06 u8 0 | 0x07 u8 0xFF (is64Bit)
  0x08 s32 version          (0x1000D for SDT/ER/NR)
  0x0C s32 fileSize
  0x10 varint 0x40
  0x18 varint 1
  0x20 varint 0x50
  0x28 varint 0x80
  0x30 varint eventBank
  0x38 varint 0
  0x40 u8[8] flags
  0x48 u8 unkFlagA | 0x49 u8 unkFlagB | 6 zero bytes
  0x50 s32 ID
  0x54 s32 animCount
  0x58 varint animsOffset
  0x60 varint animGroupsOffset
  0x68 varint 0xA0
  0x70 varint animCount2
  0x78 varint firstAnimOffset
  0x80 varint 1
  0x88 varint 0x90
  0x90 s32 ID (again)
  0x94 s32 ID (again)
  0x98 varint 0x50
  0xA0 varint 0
  0xA8 varint 0xB0
  0xB0 varint skeletonNameOffset
  0xB8 varint sibNameOffset
  0xC0 varint 0
  0xC8 varint 0

Animation entry (0x10 bytes when VarintLong):
  varint(id) varint(animBodyOffset)

Animation body:
  varint(eventHeadersOffset) varint(eventGroupHeadersOffset)
  varint(timesOffset) varint(animFileOffset)
  s32 eventCount  s32 eventGroupCount  s32 timesCount  s32 0

Event header:
  s32 type | s32 unk | f32 startTime | f32 endTime | varint dataOffset
"""
import struct
import sys


class Reader:
    def __init__(self, blob, pos=0, long_varint=True):
        self.b = blob
        self.p = pos
        self.long = long_varint

    def varint(self):
        if self.long:
            v = struct.unpack_from('<q', self.b, self.p)[0]
            self.p += 8
        else:
            v = struct.unpack_from('<i', self.b, self.p)[0]
            self.p += 4
        return v

    def s32(self):
        v = struct.unpack_from('<i', self.b, self.p)[0]
        self.p += 4
        return v

    def u32(self):
        v = struct.unpack_from('<I', self.b, self.p)[0]
        self.p += 4
        return v

    def f32(self):
        v = struct.unpack_from('<f', self.b, self.p)[0]
        self.p += 4
        return v

    def utf16(self, off):
        end = off
        while self.b[end:end + 2] != b'\x00\x00':
            end += 2
            if end + 2 > len(self.b):
                break
        return self.b[off:end].decode('utf-16-le', 'replace')


class Event:
    """A TAE event.

    Start/End are stored as f32 at the file offsets recorded in the event table
    (start_off / end_off).  Verified for a693_040000: AttackBehavior data_off
    0x8a8, start_off 0x30c (=0.133333), end_off 0x320 (=0.300000).  Because the
    table stores offsets rather than inline values, rewriting these floats in
    place changes the window without touching any table.
    """
    __slots__ = ('type', 'unk', 'start', 'end', 'data_off', 'params',
                 'start_off', 'end_off', 'start_off_pos', 'end_off_pos')

    def __repr__(self):
        return (f'Event(t={self.type} start={self.start:.4f} '
                f'end={self.end:.4f} data={self.data_off:#x} '
                f'start_off={self.start_off:#x} end_off={self.end_off:#x})')


class Animation:
    __slots__ = ('id', 'body_off', 'event_count', 'events', 'event_group_count',
                 'times_off', 'anim_file_off', 'anim_file_name')

    def __repr__(self):
        return f'Animation(id={self.id} events={len(self.events)})'


class Tae:
    def __init__(self, blob):
        self.b = blob
        if blob[:4] != b'TAE ':
            raise ValueError(f'bad magic {blob[:4]!r}')
        r = Reader(blob)
        r.p = 0x04
        self.big_endian = blob[0x04] == 1
        self.is64 = blob[0x07] == 0xFF
        self.version = r.s32() if False else struct.unpack_from('<i', blob, 0x08)[0]
        self.file_size = struct.unpack_from('<i', blob, 0x0C)[0]
        r.p = 0x30
        self.event_bank = r.varint()
        self.flags = blob[0x40:0x48]
        self.file_id = struct.unpack_from('<i', blob, 0x50)[0]
        self.anim_count = struct.unpack_from('<i', blob, 0x54)[0]
        r.p = 0x58
        self.anims_off = r.varint()
        self.anim_groups_off = r.varint()
        self.unk_0x68 = r.varint()
        self.anim_count2 = r.varint()
        self.first_anim_off = r.varint()
        r.p = 0xB0
        skel_off = r.varint()
        sib_off = r.varint()
        self.skeleton_name = r.utf16(skel_off) if skel_off else None
        self.sib_name = r.utf16(sib_off) if sib_off else None
        self.anims = []
        self._read_anims()

    def _read_anims(self):
        n = self.anim_count
        if n <= 0 or n > 200000:
            return
        entries = []
        p = self.anims_off
        for _ in range(n):
            r = Reader(self.b, p, self.is64)
            anim_id = r.varint()
            body_off = r.varint()
            p = r.p
            entries.append((anim_id, body_off))

        for anim_id, body_off in entries:
            a = Animation()
            a.id = anim_id
            a.body_off = body_off
            a.events = []
            a.anim_file_name = None
            if 0 < body_off < len(self.b):
                r = Reader(self.b, body_off, self.is64)
                eh_off = r.varint()
                eg_off = r.varint()
                a.times_off = r.varint()
                a.anim_file_off = r.varint()
                a.event_count = r.s32()
                a.event_group_count = r.s32()
                _times_count = r.s32()
                r.s32()
                if 0 < eh_off < len(self.b) and 0 < a.event_count < 100000:
                    er = Reader(self.b, eh_off, self.is64)
                    for _i in range(a.event_count):
                        # Event.Read: three varint OFFSETS, not inline values
                        so_pos = er.p
                        start_off = er.varint()
                        eo_pos = er.p
                        end_off = er.varint()
                        data_off = er.varint()
                        e = Event()
                        e.start_off = start_off
                        e.end_off = end_off
                        e.start_off_pos = so_pos       # 头里 start_off 字段的文件偏移
                        e.end_off_pos = eo_pos         # 头里 end_off 字段的文件偏移（改指针用）
                        e.start = struct.unpack_from('<f', self.b, start_off)[0] if 0 < start_off < len(self.b) - 4 else 0.0
                        e.end = struct.unpack_from('<f', self.b, end_off)[0] if 0 < end_off < len(self.b) - 4 else 0.0
                        if e.end == float('inf') or e.end > 1e30:
                            e.end = 100.0
                        e.data_off = data_off
                        if 0 < data_off < len(self.b) - 8:
                            e.type = struct.unpack_from('<i', self.b, data_off)[0]
                            e.unk = struct.unpack_from('<i', self.b, data_off + 4)[0]
                            # parameters immediately follow type+unk+varint(offset)
                            p_off = data_off + 8 + (8 if self.is64 else 4)
                            p_off = (p_off + 0xF) & ~0xF if False else p_off
                            e.params = self.b[p_off:p_off + 0x40]
                        else:
                            e.type = -1
                            e.unk = 0
                            e.params = b''
                        a.events.append(e)
                # anim file name
                a.anim_file_name = self._read_anim_file_name(a)
            self.anims.append(a)

    def _read_anim_file_name(self, a):
        try:
            if not (0 < a.anim_file_off < len(self.b) - 16):
                return None
            fr = Reader(self.b, a.anim_file_off, self.is64)
            fr.u32()                      # mini header type
            if self.is64:
                fr.s32()
            fo = fr.varint()              # offset-of-offset to filename
            if self.is64:
                fr.varint()
            if not (0 < fo < len(self.b) - 16):
                return None
            n_off = struct.unpack_from('<q', self.b, fo)[0]
            if not (0 < n_off < len(self.b) - 4):
                return None
            raw = self.b[n_off:n_off + 128]
            txt = raw.decode('utf-16-le', 'replace').split('\x00')[0]
            if txt and all(32 <= ord(c) < 127 for c in txt):
                return txt
        except (struct.error, UnicodeDecodeError, ValueError):
            pass
        return None

    def anim_name(self, a):
        """Derive the standard aXX_NNN_NNNN name from the numeric anim ID."""
        return f'{(a.id >> 24) & 0xFF:02d}_{(a.id >> 16) & 0xFF:03d}_{a.id & 0xFFFF:04d}'

    def anim_name_full(self, a):
        bank = self.file_id
        return f'a{bank:02d}_{(a.id >> 16) & 0xFF:03d}_{a.id & 0xFFFF:04d}'


if __name__ == '__main__':
    for path in sys.argv[1:]:
        blob = open(path, 'rb').read()
        name = path.split('\\')[-1]
        print('=' * 78)
        try:
            t = Tae(blob)
        except Exception as e:
            print(f'{name}: FAIL {e}')
            continue
        print(f'{name}  size={len(blob):,}  fileID={t.file_id}  anims={t.anim_count}  '
              f'bank={t.event_bank}  skel={t.skeleton_name!r} sib={t.sib_name!r}')
        for a in t.anims[:10]:
            types = {}
            for e in a.events:
                types[e.type] = types.get(e.type, 0) + 1
            print(f'   anim {t.anim_name_full(a):<16} id={a.id:<10} events={len(a.events):>4} '
                  f'file={a.anim_file_name!r} types={types}')
