from pathlib import Path
import re

# Use the original per-song SVG artwork already stored in the repository.
# This keeps artwork stable, avoids placeholder initials, and does not touch
# playback, auth, downloads, favorites, ads, or the Supabase catalog logic.
main = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = main.read_text(encoding='utf-8')

if 'import coil.compose.AsyncImage' not in s:
    s = s.replace('import androidx.media3.common.MediaItem\n', 'import coil.compose.AsyncImage\nimport androidx.media3.common.MediaItem\n', 1)

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
    val artworkUrl = when (song.id) {
        "1" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-1.svg"
        "2" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-2.svg"
        "3" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-3.svg"
        "4" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-4.svg"
        "5" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-5.svg"
        "6" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-6.svg"
        "7" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-7.svg"
        "8" -> "https://raw.githubusercontent.com/ali33035528yad-afk/Ali3303/main/artwork/song-8.svg"
        else -> song.coverUrl
    }.let { fallback -> song.coverUrl.trim().ifBlank { fallback } }

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(if (large) 24.dp else 14.dp))
            .background(Brush.linearGradient(listOf(Purple, Blue, Pink))),
        contentAlignment = Alignment.Center
    ) {
        if (artworkUrl.isNotBlank()) {
            AsyncImage(
                model = artworkUrl,
                contentDescription = song.title,
                modifier = Modifier.fillMaxSize(),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop
            )
        } else {
            Text("♫", color = White, fontSize = if (large) 54.sp else 22.sp, fontWeight = FontWeight.ExtraBold)
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
print('Reliable SVG artwork enabled for all song cards and full player')
