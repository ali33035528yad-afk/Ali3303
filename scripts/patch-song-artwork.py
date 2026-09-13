from pathlib import Path

p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')

# Add a deterministic, per-song artwork component without introducing a new
# network/image dependency. The artwork is derived from title + artist, so
# every song gets its own stable visual and existing Supabase/audio features
# remain untouched.
marker = 'private fun normalizeEmail(value: String): String = value'
if 'private fun SongArtwork(' not in s and marker in s:
    artwork = '''@Composable\nprivate fun SongArtwork(song: Song, modifier: Modifier = Modifier, large: Boolean = false) {\n    val seed = remember(song.id, song.title, song.artist) {\n        (song.id + song.title + song.artist).hashCode()\n    }\n    val hue = ((seed.toLong() and 0x7fffffffL) % 360).toFloat()\n    val c1 = Color.hsv(hue, 0.62f, 0.86f)\n    val c2 = Color.hsv((hue + 55f) % 360f, 0.70f, 0.58f)\n    val initials = song.title.trim().split(Regex("\\\\s+")).filter { it.isNotBlank() }\n        .take(2).joinToString("") { it.first().uppercase() }.ifBlank { "♫" }\n    Box(\n        modifier = modifier\n            .clip(RoundedCornerShape(if (large) 24.dp else 14.dp))\n            .background(Brush.linearGradient(listOf(c1, c2))),\n        contentAlignment = Alignment.Center\n    ) {\n        Text(\n            initials,\n            color = Color.White,\n            fontSize = if (large) 42.sp else 18.sp,\n            fontWeight = FontWeight.ExtraBold,\n            maxLines = 1\n        )\n    }\n}\n\n'''
    s = s.replace(marker, artwork + marker, 1)

# Full player: add a prominent unique artwork above the controls.
full_marker = '    Column(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xFF1B1028), Bg, Color(0xFF090A12)))).padding(horizontal = 20.dp, vertical = 14.dp)) {'
if 'SongArtwork(song, Modifier.fillMaxWidth().height(280.dp), large = true)' not in s and full_marker in s:
    s = s.replace(full_marker, full_marker + '\n        Spacer(Modifier.height(18.dp))\n        SongArtwork(song, Modifier.fillMaxWidth().height(280.dp), large = true)', 1)

p.write_text(s, encoding='utf-8')
print('Song artwork patch applied')
