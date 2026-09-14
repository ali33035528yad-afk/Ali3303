from pathlib import Path
import re

p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')

# Add painterResource import.
if 'import androidx.compose.ui.res.painterResource' not in s:
    s = s.replace('import androidx.compose.ui.platform.LocalContext\n', 'import androidx.compose.ui.platform.LocalContext\nimport androidx.compose.ui.res.painterResource\n', 1)

# Replace any SongArtwork function with a simple, guaranteed local vector fallback.
start = s.find('@Composable private fun SongArtwork')
if start < 0:
    raise SystemExit('SongArtwork function not found')
next_fun = s.find('\n@Composable', start + 10)
if next_fun < 0:
    next_fun = len(s)
new_fn = '''@Composable private fun SongArtwork(song: Song, modifier: Modifier = Modifier) {
    val artwork = when (song.id) {
        "1" -> R.drawable.cover_1
        "2" -> R.drawable.cover_2
        "3" -> R.drawable.cover_3
        "4" -> R.drawable.cover_4
        "5" -> R.drawable.cover_5
        "6" -> R.drawable.cover_6
        "7" -> R.drawable.cover_7
        "8" -> R.drawable.cover_8
        else -> R.drawable.cover_default
    }
    androidx.compose.foundation.Image(
        painter = painterResource(artwork),
        contentDescription = song.title,
        modifier = modifier,
        contentScale = androidx.compose.ui.layout.ContentScale.Crop
    )
}
'''
s = s[:start] + new_fn + s[next_fun:]
p.write_text(s, encoding='utf-8')

res = Path('app/src/main/res/drawable')
res.mkdir(parents=True, exist_ok=True)
colors = ['#5B2EFF','#E94F9B','#16B8D4','#FF6B35','#8B5CF6','#00A884','#F59E0B','#EC4899']
for i, color in enumerate(colors, 1):
    xml = f'''<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="800dp" android:height="800dp" android:viewportWidth="800" android:viewportHeight="800">
 <path android:fillColor="{color}" android:pathData="M0,0h800v800h-800z"/>
 <path android:fillColor="#33000000" android:pathData="M0,600L800,200v600H0z"/>
 <path android:fillColor="#FFFFFFFF" android:pathData="M430,350V180l100,-20v45l-70,14v131c0,35 -28,63 -63,63s-63,-28 -63,-63 28,-63 63,-63c12,0 23,3 33,9V160l-100,20v-45l123,-25c12,-2 23,7 23,20v220z"/>
 <path android:fillColor="#66FFFFFF" android:pathData="M80,80h640v640h-640z" android:strokeColor="#66FFFFFF" android:strokeWidth="3" android:fillAlpha="0"/>
</vector>'''
    (res / f'cover_{i}.xml').write_text(xml, encoding='utf-8')
(res / 'cover_default.xml').write_text((res / 'cover_1.xml').read_text(), encoding='utf-8')
print('Reliable local vector artwork installed')
