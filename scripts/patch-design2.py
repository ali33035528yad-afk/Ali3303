from pathlib import Path

p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')


def replace_function(src, name, replacement):
    marker = f'@Composable private fun {name}'
    start = src.find(marker)
    if start < 0:
        raise SystemExit(f'Could not find {name}')
    brace = src.find('{', start)
    if brace < 0:
        raise SystemExit(f'Could not find body for {name}')
    depth = 0
    in_string = False
    escape = False
    i = brace
    while i < len(src):
        ch = src[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[:start] + replacement.rstrip() + src[i + 1:]
        i += 1
    raise SystemExit(f'Unclosed body for {name}')


hero = '''@Composable private fun HeroCard(count: Int, isPlaying: Boolean) {
    Box(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)
        .clip(RoundedCornerShape(28.dp))
        .background(Brush.linearGradient(listOf(Color(0xFF35105E), Color(0xFF253E88), Color(0xFF111522))))
        .padding(20.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("موسیقی، حال خوب زندگی", color = White, fontSize = 23.sp, fontWeight = FontWeight.ExtraBold)
                Spacer(Modifier.height(7.dp))
                Text("بهترین آهنگ‌ها، همیشه با تو", color = Color(0xFFD9D6E8), fontSize = 12.sp)
                Spacer(Modifier.height(14.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    BadgePill("$count آهنگ", Icons.Default.QueueMusic)
                    BadgePill(if (isPlaying) "در حال پخش" else "آماده پخش", Icons.Default.PlayArrow)
                }
            }
            Box(Modifier.size(92.dp).clip(RoundedCornerShape(26.dp))
                .background(Brush.linearGradient(listOf(Pink, Purple, Blue))), contentAlignment = Alignment.Center) {
                Icon(Icons.Default.Headphones, null, tint = White, modifier = Modifier.size(50.dp))
            }
        }
    }
}'''

songrow = '''@Composable private fun SongRow(song: Song, selected: Boolean, favorite: Boolean, play: (Song) -> Unit, onFavorite: (String) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 5.dp)
        .clip(RoundedCornerShape(18.dp))
        .background(if (selected) Color(0xFF241A35) else Panel)
        .clickable { play(song) }.padding(9.dp), verticalAlignment = Alignment.CenterVertically) {
        SongArtwork(song, Modifier.size(58.dp), large = false)
        Spacer(Modifier.width(11.dp))
        Column(Modifier.weight(1f)) {
            Text(song.title, color = White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(song.artist, color = Muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        IconButton(onClick = { onFavorite(song.id) }) {
            Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "کتابخانه شخصی", tint = if (favorite) Pink else Muted)
        }
        BeatNovaDownloadButton(song)
        Icon(if (selected) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White)
    }
}'''

mini = '''@Composable private fun MiniPlayer(song: Song, playing: Boolean, toggle: () -> Unit, open: () -> Unit) {
    Row(Modifier.fillMaxWidth().background(Color(0xFF11131D)).clickable(onClick = open)
        .padding(horizontal = 12.dp, vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) {
        SongArtwork(song, Modifier.size(48.dp), large = false)
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            Text(song.title, color = White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(song.artist, color = Muted, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        IconButton(onClick = toggle) { Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White) }
    }
}'''

bottom = '''@Composable private fun BottomBar(selected: Int, onSelect: (Int) -> Unit) {
    Row(Modifier.fillMaxWidth().height(76.dp).background(Color(0xFF090B12)), verticalAlignment = Alignment.CenterVertically) {
        BottomItem(0, "خانه", Icons.Default.Home, selected, onSelect)
        BottomItem(1, "جستجو", Icons.Default.Search, selected, onSelect)
        BottomItem(2, "کتابخانه", Icons.Default.LibraryMusic, selected, onSelect)
        BottomItem(3, "دانلودها", Icons.Default.Download, selected, onSelect)
        BottomItem(4, "پروفایل", Icons.Default.Person, selected, onSelect)
    }
}'''

home = '''@Composable private fun HomeScreen(songs: List<Song>, loading: Boolean, error: String?, current: Song?, playing: Boolean, favorites: Set<String>, refresh: () -> Unit, play: (Song) -> Unit, favorite: (String) -> Unit) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 28.dp)) {
        item {
            Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("موسیقی برای هر لحظه", color = Muted, fontSize = 13.sp)
                    Text("BeatNova", color = White, fontSize = 31.sp, fontWeight = FontWeight.ExtraBold)
                }
                IconButton(onClick = refresh) { Icon(Icons.Default.Refresh, "به‌روزرسانی", tint = White) }
            }
        }
        item {
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                listOf("همه", "پاپ", "الکترونیک", "شاد", "غمگین").forEachIndexed { index, label ->
                    Box(Modifier.clip(CircleShape).background(if (index == 0) Purple else Panel).padding(horizontal = 13.dp, vertical = 9.dp)) {
                        Text(label, color = White, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
        item { HeroCard(songs.size, current != null && playing) }
        item { BeatNovaBannerAdSlot() }
        item { SectionHeader("پیشنهاد ویژه 🔥", "برای تو") }
        item {
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                songs.take(3).forEach { song ->
                    Column(Modifier.weight(1f).clip(RoundedCornerShape(18.dp)).background(Panel).clickable { play(song) }.padding(8.dp)) {
                        SongArtwork(song, Modifier.fillMaxWidth().aspectRatio(1f), large = true)
                        Spacer(Modifier.height(7.dp))
                        Text(song.title, color = White, fontWeight = FontWeight.Bold, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(song.artist, color = Muted, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
        item { SectionHeader("دسته‌بندی‌ها", "همه") }
        item {
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("پاپ" to Icons.Default.MusicNote, "راک" to Icons.Default.GraphicEq, "ایرانی" to Icons.Default.Star, "بین‌الملل" to Icons.Default.Public).forEach { (label, icon) ->
                    Column(Modifier.weight(1f).clip(RoundedCornerShape(16.dp)).background(Panel).padding(vertical = 13.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(icon, null, tint = Purple, modifier = Modifier.size(25.dp))
                        Spacer(Modifier.height(5.dp))
                        Text(label, color = White, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
        item { SectionHeader("جدیدترین آهنگ‌ها", "${songs.size} آهنگ") }
        when {
            loading -> item { LoadingBox() }
            error != null -> item { EmptyState("اتصال به کتابخانه آماده نیست", "Supabase یا جدول songs را بررسی کن", Icons.Default.CloudOff) }
            songs.isEmpty() -> item { EmptyState("هنوز آهنگی اضافه نشده", "آهنگ‌های مجاز خودت را در جدول songs قرار بده.", Icons.Default.LibraryMusic) }
            else -> {
                songs.take(30).forEachIndexed { index, song ->
                    item(key = song.id) { SongRow(song, current?.id == song.id, song.id in favorites, play, favorite) }
                    if (index == 4) item(key = "native-ad-slot") { BeatNovaNativeAdSlot() }
                }
            }
        }
    }
}'''

full = '''@Composable private fun FullPlayerScreen(song: Song, playing: Boolean, progress: Float, duration: Long, isFavorite: Boolean, onBack: () -> Unit, onToggle: () -> Unit, onFavorite: () -> Unit, onSeek: (Float) -> Unit, onNext: () -> Unit, onPrevious: () -> Unit) {
    val minutes = { ms: Long -> "${ms / 60000}:${((ms / 1000) % 60).toString().padStart(2, '0')}" }
    Column(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xFF160B25), Bg, Color(0xFF070910)))).padding(horizontal = 18.dp, vertical = 12.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.Default.KeyboardArrowDown, "بستن", tint = White) }
            Text("در حال پخش", color = White, fontWeight = FontWeight.Bold, fontSize = 16.sp, modifier = Modifier.weight(1f))
            IconButton(onClick = onFavorite) { Icon(if (isFavorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "پسندیدن", tint = if (isFavorite) Pink else White) }
            IconButton(onClick = {}) { Icon(Icons.Default.MoreVert, "بیشتر", tint = White) }
        }
        Spacer(Modifier.height(14.dp))
        SongArtwork(song, Modifier.fillMaxWidth().aspectRatio(1f), large = true)
        Spacer(Modifier.height(20.dp))
        Text(song.title, color = White, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(song.artist, color = Muted, fontSize = 14.sp, modifier = Modifier.padding(top = 5.dp))
        Spacer(Modifier.height(12.dp))
        Slider(value = progress, onValueChange = onSeek, modifier = Modifier.fillMaxWidth(), colors = SliderDefaults.colors(thumbColor = Purple, activeTrackColor = Purple, inactiveTrackColor = Color.White.copy(alpha = .18f)))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(minutes((duration * progress).toLong()), color = Muted, fontSize = 11.sp)
            Text(minutes(duration), color = Muted, fontSize = 11.sp)
        }
        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceEvenly) {
            IconButton(onClick = onPrevious, modifier = Modifier.size(48.dp)) { Icon(Icons.Default.SkipPrevious, "قبلی", tint = White, modifier = Modifier.size(30.dp)) }
            FilledIconButton(onClick = onToggle, modifier = Modifier.size(72.dp), colors = IconButtonDefaults.filledIconButtonColors(containerColor = Purple)) {
                Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, "پخش", tint = White, modifier = Modifier.size(38.dp))
            }
            IconButton(onClick = onNext, modifier = Modifier.size(48.dp)) { Icon(Icons.Default.SkipNext, "بعدی", tint = White, modifier = Modifier.size(30.dp)) }
        }
        Spacer(Modifier.height(10.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.FavoriteBorder, null, tint = White); Text("علاقه‌مندی", color = Muted, fontSize = 10.sp) }
            Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.Download, null, tint = White); Text("دانلود", color = Muted, fontSize = 10.sp) }
            Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Default.QueueMusic, null, tint = White); Text("افزودن به لیست", color = Muted, fontSize = 10.sp) }
        }
        Spacer(Modifier.height(12.dp))
        Text("BeatNova • پخش‌کننده موسیقی", color = Muted, fontSize = 11.sp, modifier = Modifier.align(Alignment.CenterHorizontally))
    }
}'''

for name, replacement in [('HeroCard', hero), ('SongRow', songrow), ('MiniPlayer', mini), ('BottomBar', bottom), ('HomeScreen', home), ('FullPlayerScreen', full)]:
    s = replace_function(s, name, replacement)

p.write_text(s, encoding='utf-8')
print('BeatNova design 2 patch applied')
