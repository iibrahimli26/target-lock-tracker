"""Reads the header (index) of MP4-family files: MP4, QuickTime and 3GP.

Only the index is read, never the picture data, so this is fast even for a
1 GB file (OQ-8). The file is a sequence of "boxes": 4 bytes size, 4 bytes
type, then content. The `moov` box is the index; it holds one `trak` box per
track, and each track's tables say what the track is and where its frames are.
"""
import math
import os
import struct
from dataclasses import dataclass, field

TOP_LEVEL = {b"ftyp", b"moov", b"mdat", b"free", b"skip", b"wide", b"pnot", b"uuid",
             b"styp", b"moof", b"sidx", b"mfra", b"meta", b"pdin", b"junk"}
MAX_INDEX_BYTES = 512 * 1024 * 1024
HIGH_PROFILES = {100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135}
CHROMA = {0: "4:0:0", 1: "4:2:0", 2: "4:2:2", 3: "4:4:4"}
IDENTITY = (65536, 0, 0, 65536)


class NotMp4(Exception):
    def __init__(self, looks_like: str | None = None):
        super().__init__(looks_like or "not an MP4-family file")
        self.looks_like = looks_like


class Damaged(Exception):
    pass


@dataclass
class Track:
    handler: str = ""                 # "vide" for picture tracks, "soun" for sound, ...
    codec: str = ""                   # four-letter code of the sample format, e.g. "avc1"
    width: int = 0
    height: int = 0
    timescale: int = 0                # ticks per second
    duration: int = 0                 # in ticks
    runs: list = field(default_factory=list)    # per-frame lengths: (count, ticks) runs
    sample_count: int | None = None
    matrix: tuple = IDENTITY          # display matrix (a, b, c, d) in 16.16 fixed point
    bit_depth: int | None = None      # H.264 only
    chroma: str | None = None         # H.264 only

    @property
    def frame_count(self) -> int:
        listed = sum(count for count, _ in self.runs)
        return self.sample_count if self.sample_count is not None else listed

    @property
    def rotation(self) -> int | None:
        """Degrees of the "turn when showing" note; 0 = none; None = some other transform."""
        if self.matrix == IDENTITY:
            return 0
        a, b, c, d = (v / 65536 for v in self.matrix)
        if a * d - b * c <= 0:
            return None
        angle = math.degrees(math.atan2(b, a))
        if abs(angle - round(angle / 90) * 90) > 0.5:
            return None
        return (-int(round(angle))) % 360       # same sign convention as ffprobe's "rotation"


@dataclass
class Mp4Info:
    brand: str
    tracks: list
    fragmented: bool

    @property
    def video_tracks(self) -> list:
        return [t for t in self.tracks if t.handler == "vide"]


def sniff(head: bytes) -> str | None:
    """Best-effort name for a file that is not in the MP4 family."""
    if head[:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "an AVI video"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "a WebM video" if b"webm" in head else "a Matroska video"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "a PNG image"
    if head[:3] == b"\xff\xd8\xff":
        return "a JPEG image"
    if head[:5] == b"%PDF-":
        return "a PDF document"
    if head[:4] == b"PK\x03\x04":
        return "a ZIP archive"
    if head and all(32 <= b < 127 or b in (9, 10, 13) for b in head):
        return "a text file"
    return None


def read(path) -> Mp4Info:
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(64)
        if len(head) < 8 or head[4:8] not in TOP_LEVEL:
            raise NotMp4(sniff(head))
        pos, brand, index = 0, "", None
        while pos + 8 <= size:
            f.seek(pos)
            header = f.read(16)
            box_size, box_type = struct.unpack(">I4s", header[:8])
            header_len = 8
            if box_size == 1:                       # 64-bit size follows
                if len(header) < 16:
                    break
                box_size, header_len = struct.unpack(">Q", header[8:16])[0], 16
            elif box_size == 0:                     # "to the end of the file"
                box_size = size - pos
            if box_size < header_len:
                raise Damaged("a box has an impossible size")
            if box_type == b"ftyp":
                f.seek(pos + header_len)
                brand = f.read(4).decode("latin-1")
            if box_type == b"moov":
                if pos + box_size > size or box_size > MAX_INDEX_BYTES:
                    raise Damaged("the index is cut off")
                f.seek(pos + header_len)
                index = f.read(box_size - header_len)
                break
            pos += box_size
    if index is None:
        raise Damaged("the index is missing")
    tracks, fragmented = [], False
    for box_type, start, end in _boxes(index, 0, len(index)):
        if box_type == b"trak":
            tracks.append(_track(index, start, end))
        elif box_type == b"mvex":
            fragmented = True
    return Mp4Info(brand=brand, tracks=tracks, fragmented=fragmented)


def _boxes(data: bytes, start: int, end: int):
    pos = start
    while pos + 8 <= end:
        size, box_type = struct.unpack_from(">I4s", data, pos)
        header_len = 8
        if size == 1 and pos + 16 <= end:
            size, header_len = struct.unpack_from(">Q", data, pos + 8)[0], 16
        elif size == 0:
            size = end - pos
        if size < header_len or pos + size > end:
            return
        yield box_type, pos + header_len, pos + size
        pos += size


def _track(data: bytes, start: int, end: int) -> Track:
    track = Track()
    for box_type, s, e in _boxes(data, start, end):
        if box_type == b"tkhd":
            matrix_at = s + 4 + (32 if data[s] == 1 else 20) + 16
            m = struct.unpack_from(">9i", data, matrix_at)
            track.matrix = (m[0], m[1], m[3], m[4])
        elif box_type == b"mdia":
            for media_type, ms, me in _boxes(data, s, e):
                if media_type == b"mdhd":
                    if data[ms] == 1:
                        track.timescale, track.duration = struct.unpack_from(">IQ", data, ms + 20)
                    else:
                        track.timescale, track.duration = struct.unpack_from(">II", data, ms + 12)
                elif media_type == b"hdlr":
                    track.handler = data[ms + 8:ms + 12].decode("latin-1")
                elif media_type == b"minf":
                    for info_type, i_s, i_e in _boxes(data, ms, me):
                        if info_type == b"stbl":
                            _sample_table(data, i_s, i_e, track)
    return track


def _sample_table(data: bytes, start: int, end: int, track: Track) -> None:
    for box_type, s, e in _boxes(data, start, end):
        if box_type == b"stsd" and struct.unpack_from(">I", data, s + 4)[0] >= 1:
            entry = s + 8
            entry_size = struct.unpack_from(">I", data, entry)[0]
            track.codec = data[entry + 4:entry + 8].decode("latin-1")
            if entry_size >= 86:                    # picture sample entry
                track.width, track.height = struct.unpack_from(">HH", data, entry + 32)
                for child, cs, ce in _boxes(data, entry + 86, min(entry + entry_size, e)):
                    if child == b"avcC" and ce - cs >= 8 and data[cs + 5] & 0x1F:
                        sps_len = struct.unpack_from(">H", data, cs + 6)[0]
                        track.bit_depth, track.chroma = _sps_colour(data[cs + 8:cs + 8 + sps_len])
        elif box_type == b"stts":
            count = struct.unpack_from(">I", data, s + 4)[0]
            track.runs = [struct.unpack_from(">II", data, s + 8 + 8 * i) for i in range(count)
                          if s + 16 + 8 * i <= e]
        elif box_type in (b"stsz", b"stz2"):
            track.sample_count = struct.unpack_from(">I", data, s + 8)[0]


class _Bits:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def read(self, n: int) -> int:
        value = 0
        for _ in range(n):
            byte = self.data[self.pos >> 3]
            value = (value << 1) | ((byte >> (7 - (self.pos & 7))) & 1)
            self.pos += 1
        return value

    def ue(self) -> int:                            # unsigned Exp-Golomb number
        zeros = 0
        while self.read(1) == 0:
            zeros += 1
        return (1 << zeros) - 1 + self.read(zeros)


def _sps_colour(nal: bytes) -> tuple[int, str]:
    """Bit depth and colour sampling from an H.264 sequence parameter set."""
    rbsp, zeros = bytearray(), 0
    for byte in nal[1:]:                            # skip the 1-byte NAL header
        if zeros >= 2 and byte == 3:                # emulation-prevention byte
            zeros = 0
            continue
        rbsp.append(byte)
        zeros = zeros + 1 if byte == 0 else 0
    try:
        if rbsp[0] not in HIGH_PROFILES:
            return 8, "4:2:0"
        bits = _Bits(bytes(rbsp[3:]))
        bits.ue()                                   # seq_parameter_set_id
        chroma_idc = bits.ue()
        if chroma_idc == 3:
            bits.read(1)                            # separate_colour_plane_flag
        return bits.ue() + 8, CHROMA.get(chroma_idc, "unknown")
    except IndexError:
        return 0, "unknown"
