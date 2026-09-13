from pathlib import Path

# Make the eight BeatNova covers local assets so they do not depend on
# Supabase/Raw GitHub image hosting at runtime. They are still SVG and are
# decoded by Coil's SVG decoder.
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

for sid, title, artist in covers:
    safe_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    safe_artist = artist.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#17112f"/><stop offset="0.55" stop-color="#35216b"/><stop offset="1" stop-color="#0b1022"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="42%" r="55%">
      <stop offset="0" stop-color="#9b5cff" stop-opacity="0.8"/><stop offset="1" stop-color="#9b5cff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="800" height="800" rx="64" fill="url(#bg)"/>
  <circle cx="600" cy="190" r="280" fill="url(#glow)"/>
  <circle cx="170" cy="660" r="210" fill="#20d9ff" opacity="0.10"/>
  <g fill="none" stroke="#ffffff" stroke-opacity="0.14" stroke-width="3">
    <circle cx="400" cy="350" r="170"/><circle cx="400" cy="350" r="115"/><circle cx="400" cy="350" r="60"/>
  </g>
  <circle cx="400" cy="350" r="46" fill="#f4f0ff" opacity="0.95"/>
  <path d="M430 350v-150c0-12 9-22 21-24l82-14v45l-72 13v130c0 34-27 61-61 61s-61-27-61-61 27-61 61-61c12 0 22 3 30 9v-84l-61 11v-44l84-15c12-2 23 7 23 20v164z" fill="#ffffff"/>
  <text x="70" y="625" fill="#ffffff" font-family="sans-serif" font-size="42" font-weight="700">{safe_title}</text>
  <text x="70" y="680" fill="#d8ceff" font-family="sans-serif" font-size="28">{safe_artist}</text>
  <text x="70" y="742" fill="#8feaff" font-family="sans-serif" font-size="22" letter-spacing="5">BEATNOVA  •  {sid}</text>
</svg>'''
    (assets / f'song-{sid}.svg').write_text(svg, encoding='utf-8')

# Coil's base compose module does not decode SVG by itself.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
if 'io.coil-kt:coil-svg:2.7.0' not in g:
    marker = 'implementation("io.coil-kt:coil-compose:2.7.0")'
    if marker in g:
        g = g.replace(marker, marker + '\n    implementation("io.coil-kt:coil-svg:2.7.0")', 1)
    else:
        raise SystemExit('coil-compose dependency not found')
    gradle.write_text(g, encoding='utf-8')

p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')

if 'import coil.ImageLoader' not in s:
    s = s.replace('import coil.compose.AsyncImage\n', 'import coil.ImageLoader\nimport coil.compose.AsyncImage\nimport coil.decode.SvgDecoder\n', 1)
if 'import androidx.compose.ui.platform.LocalContext' not in s:
    s = s.replace('import androidx.compose.ui.unit.dp\n', 'import androidx.compose.ui.platform.LocalContext\nimport androidx.compose.ui.unit.dp\n', 1)

old = 'AsyncImage(model = song.coverUrl, imageLoader = imageLoader, contentDescription = song.title, modifier = Modifier.fillMaxSize())'
new = 'AsyncImage(model = if (song.id in 1..8) "file:///android_asset/covers/song-${song.id}.svg" else song.coverUrl, imageLoader = imageLoader, contentDescription = song.title, modifier = Modifier.fillMaxSize())'
if old in s:
    s = s.replace(old, new, 1)
else:
    old2 = 'AsyncImage(model = song.coverUrl, contentDescription = song.title, modifier = Modifier.fillMaxSize())'
    new2 = 'AsyncImage(model = if (song.id in 1..8) "file:///android_asset/covers/song-${song.id}.svg" else song.coverUrl, imageLoader = imageLoader, contentDescription = song.title, modifier = Modifier.fillMaxSize())'
    if old2 in s:
        anchor = 'if (song.coverUrl.isNotBlank()) {'
        if anchor in s and 'val imageLoader = remember(context)' not in s:
            s = s.replace(anchor, anchor + '''\n            val context = LocalContext.current\n            val imageLoader = remember(context) {\n                ImageLoader.Builder(context)\n                    .components { add(SvgDecoder.Factory()) }\n                    .build()\n            }''', 1)
        s = s.replace(old2, new2, 1)
    elif 'file:///android_asset/covers/song-' not in s:
        raise SystemExit('SongArtwork AsyncImage block not found')

p.write_text(s, encoding='utf-8')
print('Eight local SVG covers generated and SongArtwork patched')
