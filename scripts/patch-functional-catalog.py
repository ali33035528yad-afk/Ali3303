from pathlib import Path
p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')

# Keep old constructors compatible while exposing existing Supabase metadata.
s = s.replace(
    'data class Song(val id: String, val title: String, val artist: String, val audioUrl: String)',
    '''data class Song(
    val id: String,
    val title: String,
    val artist: String,
    val audioUrl: String,
    val coverUrl: String = "",
    val genre: String = "",
    val isTrending: Boolean = false,
)''', 1)
s = s.replace(
    'songs?select=id,title,artist,audio_url&order=created_at.desc',
    'songs?select=id,title,artist,audio_url,cover_url,genre,is_trending&order=created_at.desc', 1)
s = s.replace(
    'Song(o.optString("id", i.toString()), o.optString("title", "بدون نام"), o.optString("artist", "هنرمند ناشناس"), audio)',
    'Song(o.optString("id", i.toString()), o.optString("title", "بدون نام"), o.optString("artist", "هنرمند ناشناس"), audio, o.optString("cover_url"), o.optString("genre"), o.optBoolean("is_trending", false))', 1)

# Real album artwork from songs.cover_url; generated artwork remains the fallback.
if 'import coil.compose.AsyncImage' not in s:
    s = s.replace('import androidx.media3.common.MediaItem\n', 'import coil.compose.AsyncImage\nimport androidx.media3.common.MediaItem\n', 1)

def replace_fun(src, name, repl):
    marker = f'@Composable private fun {name}'
    start = src.find(marker)
    if start < 0:
        return src
    brace = src.find('{', start)
    depth = 0; string = False; escape = False
    i = brace
    while i < len(src):
        ch = src[i]
        if string:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == '"': string = False
        else:
            if ch == '"': string = True
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[:start] + repl.rstrip() + src[i+1:]
        i += 1
    return src

art = '''@Composable private fun SongArtwork(song: Song, modifier: Modifier = Modifier, large: Boolean = false) {
    val seed = remember(song.id, song.title, song.artist) { (song.id + song.title + song.artist).hashCode() }
    val hue = ((seed.toLong() and 0x7fffffffL) % 360).toFloat()
    val c1 = Color.hsv(hue, 0.62f, 0.86f)
    val c2 = Color.hsv((hue + 55f) % 360f, 0.70f, 0.58f)
    val initials = song.title.trim().split(Regex("\\\\s+")).filter { it.isNotBlank() }.take(2)
        .joinToString("") { it.first().uppercase() }.ifBlank { "♫" }
    Box(modifier = modifier.clip(RoundedCornerShape(if (large) 24.dp else 14.dp))
        .background(Brush.linearGradient(listOf(c1, c2))), contentAlignment = Alignment.Center) {
        if (song.coverUrl.isNotBlank()) {
            AsyncImage(model = song.coverUrl, contentDescription = song.title, modifier = Modifier.fillMaxSize())
        } else {
            Text(initials, color = Color.White, fontSize = if (large) 42.sp else 18.sp, fontWeight = FontWeight.ExtraBold)
        }
    }
}'''
s = replace_fun(s, 'SongArtwork', art)

# Make Download and Add-to-list in the full player actually clickable.
s = s.replace(
    'onSeek: (Float) -> Unit, onNext: () -> Unit, onPrevious: () -> Unit) {',
    'onSeek: (Float) -> Unit, onNext: () -> Unit, onPrevious: () -> Unit, onDownload: () -> Unit, onQueue: () -> Unit) {', 1)
s = s.replace(
    'Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.Download, null, tint = White); Text("دانلود", color = Muted, fontSize = 10.sp) }',
    'Column(Modifier.clickable { onDownload() }, horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.Download, null, tint = White); Text("دانلود", color = Muted, fontSize = 10.sp) }', 1)
s = s.replace(
    'Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.QueueMusic, null, tint = White); Text("افزودن به لیست", color = Muted, fontSize = 10.sp) }',
    'Column(Modifier.clickable { onQueue() }, horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.QueueMusic, null, tint = White); Text("افزودن به لیست", color = Muted, fontSize = 10.sp) }', 1)
s = s.replace(
    'IconButton(onClick = {}) { Icon(Icons.Default.MoreVert, "بیشتر", tint = White) }',
    'IconButton(onClick = onQueue) { Icon(Icons.Default.MoreVert, "افزودن به لیست", tint = White) }', 1)

# Simple persistent play queue. Next consumes queued songs first.
if 'private object BeatNovaQueue' not in s:
    marker = 'private object NotificationBus'
    queue = '''private object BeatNovaQueue {
    private const val PREFS = "beatnova_queue"
    private const val KEY = "ids"
    fun add(context: Context, song: Song) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val ids = prefs.getStringSet(KEY, emptySet())?.toMutableSet() ?: mutableSetOf()
        val added = ids.add(song.id)
        prefs.edit().putStringSet(KEY, ids).apply()
        android.widget.Toast.makeText(context, if (added) "به لیست پخش اضافه شد" else "این آهنگ قبلاً در لیست است", android.widget.Toast.LENGTH_SHORT).show()
    }
    fun next(context: Context, current: Song?, songs: List<Song>): Song? {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val ids = prefs.getStringSet(KEY, emptySet())?.toMutableSet() ?: mutableSetOf()
        val next = songs.firstOrNull { it.id in ids && it.id != current?.id }
        if (next != null) { ids.remove(next.id); prefs.edit().putStringSet(KEY, ids).apply() }
        return next
    }
}
'''
    s = s.replace(marker, queue + marker, 1)

s = s.replace(
    'onNext = { val i = songs.indexOfFirst { it.id == current!!.id }; if (i >= 0 && i + 1 < songs.size) play(songs[i + 1]) },',
    'onNext = { val queued = BeatNovaQueue.next(context, current, songs); if (queued != null) play(queued) else { val i = songs.indexOfFirst { it.id == current!!.id }; if (i >= 0 && i + 1 < songs.size) play(songs[i + 1]) } },', 1)
s = s.replace(
    'onPrevious = { val i = songs.indexOfFirst { it.id == current!!.id }; if (i > 0) play(songs[i - 1]) })',
    'onPrevious = { val i = songs.indexOfFirst { it.id == current!!.id }; if (i > 0) play(songs[i - 1]) }, onDownload = { BeatNovaDownloads.toggle(context, current!!) }, onQueue = { BeatNovaQueue.add(context, current!!) })', 1)

# Supabase-controlled recommendations/categories in the existing Design 2 home.
home = '''@Composable private fun HomeScreen(songs: List<Song>, loading: Boolean, error: String?, current: Song?, playing: Boolean, favorites: Set<String>, refresh: () -> Unit, play: (Song) -> Unit, favorite: (String) -> Unit) {
    var selectedGenre by remember { mutableStateOf("همه") }
    val genres = remember(songs) { listOf("همه") + songs.map { it.genre.trim() }.filter { it.isNotBlank() }.distinct().take(8) }
    val filtered = if (selectedGenre == "همه") songs else songs.filter { it.genre.equals(selectedGenre, true) }
    val featured = songs.filter { it.isTrending }.ifEmpty { songs }.take(3)
    if (selectedGenre !in genres) selectedGenre = "همه"
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 28.dp)) {
        item { Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) { Text("موسیقی برای هر لحظه", color = Muted, fontSize = 13.sp); Text("BeatNova", color = White, fontSize = 31.sp, fontWeight = FontWeight.ExtraBold) }
            IconButton(onClick = refresh) { Icon(Icons.Default.Refresh, "به‌روزرسانی", tint = White) }
        } }
        item { Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            genres.forEach { label -> Box(Modifier.clip(CircleShape).background(if (label == selectedGenre) Purple else Panel).clickable { selectedGenre = label }.padding(horizontal = 13.dp, vertical = 9.dp)) { Text(label, color = White, fontSize = 11.sp, fontWeight = FontWeight.Bold) } }
        } }
        item { HeroCard(songs.size, current != null && playing) }
        item { BeatNovaBannerAdSlot() }
        item { SectionHeader("پیشنهاد ویژه 🔥", "${featured.size} آهنگ") }
        item { Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            featured.forEach { song -> Column(Modifier.weight(1f).clip(RoundedCornerShape(18.dp)).background(Panel).clickable { play(song) }.padding(8.dp)) {
                SongArtwork(song, Modifier.fillMaxWidth().aspectRatio(1f), large = true); Spacer(Modifier.height(7.dp)); Text(song.title, color = White, fontWeight = FontWeight.Bold, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis); Text(song.artist, color = Muted, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            } }
        } }
        item { SectionHeader("دسته‌بندی‌ها", "قابل کنترل از Supabase") }
        item { Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            genres.drop(1).take(4).forEach { label -> Column(Modifier.weight(1f).clip(RoundedCornerShape(16.dp)).background(if (label == selectedGenre) Color(0xFF241A35) else Panel).clickable { selectedGenre = label }.padding(vertical = 13.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(Icons.Default.MusicNote, null, tint = Purple, modifier = Modifier.size(25.dp)); Spacer(Modifier.height(5.dp)); Text(label, color = White, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            } }
        } }
        item { SectionHeader(if (selectedGenre == "همه") "جدیدترین آهنگ‌ها" else "آهنگ‌های «$selectedGenre»", "${filtered.size} آهنگ") }
        when { loading -> item { LoadingBox() }; error != null -> item { EmptyState("اتصال به کتابخانه آماده نیست", "Supabase یا جدول songs را بررسی کن", Icons.Default.CloudOff) }; filtered.isEmpty() -> item { EmptyState("هنوز آهنگی در این دسته نیست", "برای آهنگ genre تعیین کن.", Icons.Default.LibraryMusic) }; else -> filtered.take(30).forEachIndexed { index, song ->
            item(key = song.id) { SongRow(song, current?.id == song.id, song.id in favorites, play, favorite) }
            if (index == 4) item(key = "native-ad-slot") { BeatNovaNativeAdSlot() }
        } }
    }
}'''
s = replace_fun(s, 'HomeScreen', home)

p.write_text(s, encoding='utf-8')
print('Functional controls and Supabase catalog patch applied')
