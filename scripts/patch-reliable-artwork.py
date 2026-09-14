from pathlib import Path
import re

# Online-only artwork. The app reads cover_url from Supabase and never bundles artwork locally.
main = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = main.read_text(encoding='utf-8')

imports = [
    'import coil.compose.AsyncImage\n',
    'import coil.ImageLoader\n',
    'import coil.decode.SvgDecoder\n',
    'import androidx.compose.ui.platform.LocalContext\n',
]
if 'import coil.compose.AsyncImage' not in s:
    s = s.replace('import androidx.media3.common.MediaItem\n', ''.join(imports) + 'import androidx.media3.common.MediaItem\n', 1)
else:
    if 'import coil.ImageLoader' not in s:
        s = s.replace('import coil.compose.AsyncImage\n', 'import coil.compose.AsyncImage\nimport coil.ImageLoader\n', 1)
    if 'import coil.decode.SvgDecoder' not in s:
        s = s.replace('import coil.ImageLoader\n', 'import coil.ImageLoader\nimport coil.decode.SvgDecoder\n', 1)
    if 'import androidx.compose.ui.platform.LocalContext' not in s:
        s = s.replace('import coil.decode.SvgDecoder\n', 'import coil.decode.SvgDecoder\nimport androidx.compose.ui.platform.LocalContext\n', 1)

pattern = re.compile(r'@Composable\s+private fun SongArtwork\s*\([^)]*\)\s*\{')
m = pattern.search(s)
if not m:
    raise SystemExit('SongArtwork function not found')

start = m.start()
brace = s.find('{', m.start(), m.end())
depth = 0
string = False
escape = False
end = None
for i in range(brace, len(s)):
    ch = s[i]
    if string:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == '"':
            string = False
    else:
        if ch == '"':
            string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
if end is None:
    raise SystemExit('SongArtwork body could not be parsed')

new_fn = '''@Composable
private fun SongArtwork(song: Song, modifier: Modifier = Modifier, large: Boolean = false) {
    // IMPORTANT: artwork is online-only. The URL comes directly from Supabase songs.cover_url.
    val artworkUrl = song.coverUrl.trim()
    val context = LocalContext.current
    val svgImageLoader = remember {
        ImageLoader.Builder(context)
            .components { add(SvgDecoder.Factory()) }
            .build()
    }
    val shape = RoundedCornerShape(if (large) 24.dp else 14.dp)
    Box(
        modifier = modifier.clip(shape).background(Color(0xFF171923)),
        contentAlignment = Alignment.Center
    ) {
        if (artworkUrl.isNotBlank()) {
            AsyncImage(
                model = artworkUrl,
                imageLoader = svgImageLoader,
                contentDescription = song.title,
                modifier = Modifier.fillMaxSize().clip(shape),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                onError = { println("BeatNova artwork load failed: $artworkUrl - ${it.result.throwable}") }
            )
        } else {
            Icon(Icons.Default.MusicNote, null, tint = Purple, modifier = Modifier.size(if (large) 48.dp else 28.dp))
        }
    }
}'''

s = s[:start] + new_fn + s[end:]
main.write_text(s, encoding='utf-8')

gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
if 'implementation("io.coil-kt:coil-svg:2.7.0")' not in g:
    g = g.replace('implementation("io.coil-kt:coil-compose:2.7.0")', 'implementation("io.coil-kt:coil-compose:2.7.0")\n    implementation("io.coil-kt:coil-svg:2.7.0")', 1)
gradle.write_text(g, encoding='utf-8')
print('Online-only Supabase cover_url artwork enabled with explicit SVG decoder')
