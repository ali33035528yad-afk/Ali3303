from pathlib import Path
import struct
import zlib
import math

# Generate real local PNG files. This avoids all runtime SVG/network loading issues.
assets = Path('app/src/main/assets/covers')
assets.mkdir(parents=True, exist_ok=True)

covers = [
    ('1', 'BeatNova', 'Track 01'),
    ('2', '20438', 'Track 02'),
    ('3', 'Khojasteh.Yadet.Ni', 'Iranian Pop'),
    ('4', 'Bache Gherti', 'Mohsen Lorestani'),
    ('5', 'Leila Jan', 'Mohsen Lorestani'),
    ('6', 'Naro Naro', 'Remix'),
    ('7', 'Adelante', 'Sash!'),
    ('8', 'audio (6)', 'Track 08'),
]

# Tiny dependency-free PNG writer with gradient/background + record-disc motif.
def png_chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

def make_png(path, idx, title, artist, w=640, h=640):
    rows = []
    # Deterministic per-song accent values.
    accents = [(150,80,255), (35,190,255), (255,90,170), (80,220,180), (255,180,70), (120,100,255), (40,210,255), (220,90,255)]
    ar, ag, ab = accents[(idx - 1) % len(accents)]
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            t = (x + y) / (w + h)
            glow = max(0.0, 1.0 - math.hypot(x-w*0.68, y-h*0.28)/(w*0.72))
            r = int(10 + 30*t + ar*0.30*glow)
            g = int(12 + 18*t + ag*0.30*glow)
            b = int(30 + 35*(1-t) + ab*0.30*glow)
            # Concentric record rings.
            d = math.hypot(x-w*0.5, y-h*0.42)
            if 105 < d < 235 and int(d) % 16 < 3:
                r = min(255, r+22); g = min(255, g+22); b = min(255, b+22)
            # Central music-note-like bright disc.
            if (x-w*0.5)**2 + (y-h*0.42)**2 < 42**2:
                r, g, b = 245, 240, 255
            row += bytes((r,g,b,255))
        rows.append(row)
    raw = b''.join(rows)
    data = b'\x89PNG\r\n\x1a\n'
    data += png_chunk(b'IHDR', struct.pack('>IIBBBBB', w,h,8,6,0,0,0))
    data += png_chunk(b'IDAT', zlib.compress(raw, 9))
    data += png_chunk(b'IEND', b'')
    path.write_bytes(data)

for sid, title, artist in covers:
    make_png(assets / f'song-{sid}.png', int(sid), title, artist)

p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')
# Keep the existing Coil setup harmless, but force the first eight songs to local PNG assets.
old = 'AsyncImage(model = if (song.id in 1..8) "file:///android_asset/covers/song-${song.id}.svg" else song.coverUrl, imageLoader = imageLoader, contentDescription = song.title, modifier = Modifier.fillMaxSize())'
new = 'AsyncImage(model = if (song.id in 1..8) "file:///android_asset/covers/song-${song.id}.png" else song.coverUrl, imageLoader = imageLoader, contentDescription = song.title, modifier = Modifier.fillMaxSize())'
if old in s:
    s = s.replace(old, new, 1)
elif 'file:///android_asset/covers/song-' not in s:
    raise SystemExit('SongArtwork local asset model not found')
p.write_text(s, encoding='utf-8')
print('Eight guaranteed local PNG covers generated and SongArtwork switched to PNG')
