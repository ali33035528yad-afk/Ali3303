from pathlib import Path

# Coil's base compose module does not decode SVG by itself. Add the SVG decoder
# and give AsyncImage an ImageLoader that knows how to render the SVG covers.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
if 'io.coil-kt:coil-svg:2.7.0' not in g:
    g = g.replace('implementation("io.coil-kt:coil-compose:2.7.0")', 'implementation("io.coil-kt:coil-compose:2.7.0")\n    implementation("io.coil-kt:coil-svg:2.7.0")', 1)
    gradle.write_text(g, encoding='utf-8')

p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')

for old, new in [
    ('import coil.compose.AsyncImage\n', 'import coil.ImageLoader\nimport coil.compose.AsyncImage\nimport coil.decode.SvgDecoder\n'),
    ('import androidx.compose.ui.platform.LocalContext\n', 'import androidx.compose.ui.platform.LocalContext\n'),
]:
    if old in s and new not in s:
        s = s.replace(old, new, 1)
if 'import androidx.compose.ui.platform.LocalContext' not in s:
    s = s.replace('import androidx.compose.ui.unit.dp\n', 'import androidx.compose.ui.platform.LocalContext\nimport androidx.compose.ui.unit.dp\n', 1)

old = 'if (song.coverUrl.isNotBlank()) {\n            AsyncImage(model = song.coverUrl, contentDescription = song.title, modifier = Modifier.fillMaxSize())\n        } else {'
new = 'if (song.coverUrl.isNotBlank()) {\n            val context = LocalContext.current\n            val imageLoader = remember(context) {\n                ImageLoader.Builder(context)\n                    .components { add(SvgDecoder.Factory()) }\n                    .build()\n            }\n            AsyncImage(model = song.coverUrl, imageLoader = imageLoader, contentDescription = song.title, modifier = Modifier.fillMaxSize())\n        } else {'
if old in s:
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('SVG artwork decoder enabled')
