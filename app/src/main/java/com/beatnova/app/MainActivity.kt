package com.beatnova.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray

private val Bg = Color(0xFF07080D)
private val Panel = Color(0xFF11131B)
private val Panel2 = Color(0xFF181A24)
private val Muted = Color(0xFF9B9DAB)
private val White = Color(0xFFF8F8FC)
private val Purple = Color(0xFFC65CFF)
private val Blue = Color(0xFF5B7CFF)
private val Pink = Color(0xFFFF3E9D)

private data class Song(val id: String, val title: String, val artist: String, val audioUrl: String, val coverUrl: String = "")

private object Repo {
    private val client = OkHttpClient()
    suspend fun songs(): Result<List<Song>> = withContext(Dispatchers.IO) {
        val url = BuildConfig.SUPABASE_URL.trimEnd('/')
        val key = BuildConfig.SUPABASE_ANON_KEY
        if (url.isBlank() || key.isBlank()) return@withContext Result.failure(IllegalStateException("CONFIG"))
        try {
            val req = Request.Builder().url("$url/rest/v1/songs?select=*")
                .addHeader("apikey", key).addHeader("Authorization", "Bearer $key").build()
            client.newCall(req).execute().use { r ->
                if (!r.isSuccessful) return@withContext Result.failure(IllegalStateException("HTTP_${r.code}"))
                val json = JSONArray(r.body?.string().orEmpty())
                val out = buildList {
                    for (i in 0 until json.length()) {
                        val o = json.getJSONObject(i)
                        val audio = o.optString("audio_url")
                        if (audio.isNotBlank()) add(Song(o.optString("id", i.toString()), o.optString("title", "بدون نام"), o.optString("artist", "هنرمند ناشناس"), audio, o.optString("cover_url")))
                    }
                }
                Result.success(out)
            }
        } catch (e: Exception) { Result.failure(e) }
    }
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { BeatNova() }
    }
}

@Composable
private fun BeatNova() {
    val context = LocalContext.current
    val player = remember { ExoPlayer.Builder(context).build() }
    val scope = rememberCoroutineScope()
    var tab by remember { mutableIntStateOf(0) }
    var songs by remember { mutableStateOf<List<Song>>(emptyList()) }
    var current by remember { mutableStateOf<Song?>(null) }
    var playing by remember { mutableStateOf(false) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var query by remember { mutableStateOf("") }
    var favorites by remember { mutableStateOf(setOf<String>()) }
    var showPlayer by remember { mutableStateOf(false) }

    fun refresh() = scope.launch {
        loading = true; error = null
        Repo.songs().onSuccess { songs = it }.onFailure { error = it.message ?: "ERROR" }
        loading = false
    }
    fun play(song: Song) {
        current = song
        player.setMediaItem(MediaItem.fromUri(song.audioUrl))
        player.prepare(); player.play(); playing = true
    }
    fun toggle() {
        if (player.isPlaying) player.pause() else if (current != null) player.play()
        playing = player.isPlaying
    }
    DisposableEffect(player) {
        val listener = object : Player.Listener {
            override fun onIsPlayingChanged(v: Boolean) { playing = v }
            override fun onPlaybackStateChanged(state: Int) { if (state == Player.STATE_ENDED) playing = false }
        }
        player.addListener(listener)
        onDispose { player.removeListener(listener); player.release() }
    }
    LaunchedEffect(Unit) { refresh() }

    val filtered = songs.filter { query.isBlank() || it.title.contains(query, true) || it.artist.contains(query, true) }
    val liked = songs.filter { it.id in favorites }

    MaterialTheme(colorScheme = darkColorScheme(primary = Purple, background = Bg, surface = Panel, onSurface = White)) {
        Scaffold(
            containerColor = Bg,
            bottomBar = {
                Column {
                    if (current != null) MiniPlayer(current!!, playing, { toggle() }, { showPlayer = true })
                    NavigationBar(containerColor = Color(0xFF0D0E14), tonalElevation = 0.dp) {
                        NavItem(0, "خانه", Icons.Default.Home, tab) { tab = 0 }
                        NavItem(1, "جستجو", Icons.Default.Search, tab) { tab = 1 }
                        NavItem(2, "کتابخانه", Icons.Default.LibraryMusic, tab) { tab = 2 }
                        NavItem(3, "تنظیمات", Icons.Default.Settings, tab) { tab = 3 }
                    }
                }
            }
        ) { pad ->
            Box(Modifier.fillMaxSize().padding(pad)) {
                when (tab) {
                    0 -> Home(filtered, current, playing, loading, error, ::refresh, ::play, favorites) { id -> favorites = if (id in favorites) favorites - id else favorites + id }
                    1 -> Search(query, { query = it }, filtered, current, ::play, favorites) { id -> favorites = if (id in favorites) favorites - id else favorites + id }
                    2 -> Library(liked, current, ::play, favorites) { id -> favorites = if (id in favorites) favorites - id else favorites + id }
                    else -> Settings()
                }
                if (showPlayer && current != null) NowPlaying(current!!, playing, { toggle() }, { showPlayer = false })
            }
        }
    }
}

@Composable
private fun RowScope.NavItem(index: Int, label: String, icon: ImageVector, selected: Int, onClick: () -> Unit) {
    val isSelected = index == selected
    Box(Modifier.weight(1f).fillMaxHeight().clickable(onClick = onClick), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Icon(icon, label, tint = if (isSelected) Purple else Muted, modifier = Modifier.size(24.dp))
            Spacer(Modifier.height(3.dp))
            Text(label, color = if (isSelected) White else Muted, fontSize = 11.sp, fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal)
        }
    }
}

@Composable private fun Home(songs: List<Song>, current: Song?, playing: Boolean, loading: Boolean, error: String?, refresh: () -> Unit, play: (Song) -> Unit, favs: Set<String>, fav: (String) -> Unit) {
    LazyColumn(contentPadding = PaddingValues(bottom = 20.dp), modifier = Modifier.fillMaxSize()) {
        item { Row(Modifier.fillMaxWidth().padding(start = 20.dp, end = 12.dp, top = 22.dp, bottom = 14.dp), verticalAlignment = Alignment.CenterVertically) { Column(Modifier.weight(1f)) { Text("سلام 👋", color = Muted, fontSize = 14.sp); Text("BeatNova", color = White, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold) }; IconButton(onClick = refresh) { Icon(Icons.Default.Refresh, "به‌روزرسانی", tint = White) } } }
        item { HeroCard(songs.size, current, playing) }
        item { SectionTitle("دسته‌بندی‌ها", "همه") }
        item { LazyRow(contentPadding = PaddingValues(horizontal = 18.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) { item { Category("میکس‌ها", Icons.Default.MusicNote, Purple) }; item { Category("ترندها", Icons.Default.TrendingUp, Pink) }; item { Category("آرامش", Icons.Default.Headphones, Blue) }; item { Category("آلبوم‌ها", Icons.Default.Album, Color(0xFF00C7A5)) } } }
        item { SectionTitle("جدیدترین‌ها", "${songs.size} آهنگ") }
        if (error != null) item { InfoBanner(error) }
        if (loading) item { Box(Modifier.fillMaxWidth().height(180.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Purple) } }
        else if (songs.isEmpty()) item { Empty() }
        else items(songs.take(30), key = { it.id }) { SongItem(it, current?.id == it.id, it.id in favs, play, fav) }
    }
}

@Composable private fun HeroCard(count: Int, current: Song?, playing: Boolean) { Box(Modifier.fillMaxWidth().padding(horizontal = 16.dp).clip(RoundedCornerShape(28.dp)).background(Brush.linearGradient(listOf(Color(0xFF2C1550), Color(0xFF131A42), Color(0xFF10121B)))).padding(22.dp)) { Column { Row(verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(58.dp).clip(RoundedCornerShape(18.dp)).background(Brush.linearGradient(listOf(Pink, Purple))), contentAlignment = Alignment.Center) { Icon(Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(32.dp)) }; Spacer(Modifier.width(14.dp)); Column { Text("ONLINE MUSIC", color = Color(0xFFDAB7FF), fontSize = 11.sp, fontWeight = FontWeight.Bold); Text("موسیقی، همیشه با تو", color = White, fontSize = 20.sp, fontWeight = FontWeight.ExtraBold) } }; Spacer(Modifier.height(22.dp)); Text("کشف کن • پخش کن • لذت ببر", color = White, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold); Text("کتابخانه آنلاین BeatNova را با آهنگ‌های مجاز خودت بساز.", color = Color(0xFFD2D1DC), fontSize = 13.sp); Spacer(Modifier.height(18.dp)); Row(verticalAlignment = Alignment.CenterVertically) { Pill("$count آهنگ", Icons.Default.QueueMusic); Spacer(Modifier.width(8.dp)); Pill(if (current != null && playing) "در حال پخش" else "آماده پخش", Icons.Default.PlayArrow) } } } }

@Composable private fun Pill(text: String, icon: ImageVector) { Row(Modifier.clip(CircleShape).background(Color.White.copy(alpha = .10f)).padding(horizontal = 11.dp, vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) { Icon(icon, null, tint = White, modifier = Modifier.size(15.dp)); Spacer(Modifier.width(5.dp)); Text(text, color = White, fontSize = 11.sp, fontWeight = FontWeight.SemiBold) } }
@Composable private fun SectionTitle(title: String, action: String) { Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 16.dp), verticalAlignment = Alignment.CenterVertically) { Text(title, color = White, fontSize = 19.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); Text(action, color = Purple, fontSize = 12.sp, fontWeight = FontWeight.Bold) } }
@Composable private fun Category(name: String, icon: ImageVector, color: Color) { Column(Modifier.width(82.dp), horizontalAlignment = Alignment.CenterHorizontally) { Box(Modifier.size(62.dp).clip(RoundedCornerShape(20.dp)).background(color.copy(alpha = .14f)), contentAlignment = Alignment.Center) { Icon(icon, null, tint = color, modifier = Modifier.size(27.dp)) }; Spacer(Modifier.height(7.dp)); Text(name, color = Muted, fontSize = 11.sp) } }

@Composable private fun Search(query: String, change: (String) -> Unit, songs: List<Song>, current: Song?, play: (Song) -> Unit, favs: Set<String>, fav: (String) -> Unit) { Column(Modifier.fillMaxSize().padding(top = 22.dp)) { Text("جستجو", color = White, fontSize = 29.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 20.dp)); Text("آهنگ یا هنرمند مورد علاقه‌ات را پیدا کن", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)); OutlinedTextField(query, change, Modifier.fillMaxWidth().padding(16.dp), singleLine = true, placeholder = { Text("نام آهنگ یا خواننده") }, leadingIcon = { Icon(Icons.Default.Search, null) }, shape = RoundedCornerShape(18.dp)); LazyColumn(contentPadding = PaddingValues(bottom = 20.dp)) { if (songs.isEmpty()) item { Empty() } else items(songs, key = { it.id }) { SongItem(it, current?.id == it.id, it.id in favs, play, fav) } } } }
@Composable private fun Library(songs: List<Song>, current: Song?, play: (Song) -> Unit, favs: Set<String>, fav: (String) -> Unit) { Column(Modifier.fillMaxSize().padding(top = 22.dp)) { Text("کتابخانه من", color = White, fontSize = 29.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 20.dp)); Text("آهنگ‌های مورد علاقه‌ات", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)); LazyColumn(Modifier.weight(1f), contentPadding = PaddingValues(top = 14.dp, bottom = 20.dp)) { if (songs.isEmpty()) item { Empty() } else items(songs, key = { it.id }) { SongItem(it, current?.id == it.id, it.id in favs, play, fav) } } } }

@Composable private fun SongItem(song: Song, selected: Boolean, favorite: Boolean, play: (Song) -> Unit, fav: (String) -> Unit) { Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 5.dp).clip(RoundedCornerShape(19.dp)).background(if (selected) Color(0xFF211A31) else Panel).clickable { play(song) }.padding(10.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(58.dp).clip(RoundedCornerShape(16.dp)).background(Brush.linearGradient(listOf(Blue.copy(alpha = .75f), Purple.copy(alpha = .85f)))), contentAlignment = Alignment.Center) { Icon(if (selected) Icons.Default.GraphicEq else Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(27.dp)) }; Spacer(Modifier.width(12.dp)); Column(Modifier.weight(1f)) { Text(song.title, color = White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis); Text(song.artist, color = Muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis) }; IconButton(onClick = { fav(song.id) }) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, null, tint = if (favorite) Pink else Muted) }; Box(Modifier.size(38.dp).clip(CircleShape).background(if (selected) Purple else Panel2), contentAlignment = Alignment.Center) { Icon(if (selected) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White, modifier = Modifier.size(20.dp)) } } }
@Composable private fun MiniPlayer(song: Song, playing: Boolean, toggle: () -> Unit, open: () -> Unit) { Row(Modifier.fillMaxWidth().background(Color(0xFF151621)).clickable { open() }.padding(horizontal = 14.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(46.dp).clip(RoundedCornerShape(13.dp)).background(Brush.linearGradient(listOf(Pink, Purple))), contentAlignment = Alignment.Center) { Icon(Icons.Default.MusicNote, null, tint = White) }; Spacer(Modifier.width(10.dp)); Column(Modifier.weight(1f)) { Text(song.title, color = White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis); Text(song.artist, color = Muted, fontSize = 11.sp) }; IconButton(onClick = toggle) { Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White) } } }
@Composable private fun NowPlaying(song: Song, playing: Boolean, toggle: () -> Unit, close: () -> Unit) { Box(Modifier.fillMaxSize().background(Bg)) { Column(Modifier.fillMaxSize().statusBarsPadding().padding(18.dp), horizontalAlignment = Alignment.CenterHorizontally) { Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { IconButton(onClick = close) { Icon(Icons.Default.KeyboardArrowDown, "بستن", tint = White) }; Text("در حال پخش", color = White, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); Icon(Icons.Default.MoreHoriz, null, tint = Muted) }; Spacer(Modifier.height(48.dp)); Box(Modifier.size(280.dp).clip(RoundedCornerShape(38.dp)).background(Brush.linearGradient(listOf(Color(0xFF2C1B50), Color(0xFF15204A), Color(0xFF40123B)))), contentAlignment = Alignment.Center) { Icon(Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(110.dp)) }; Spacer(Modifier.height(34.dp)); Text(song.title, color = White, fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1, overflow = TextOverflow.Ellipsis); Text(song.artist, color = Muted, fontSize = 14.sp); Spacer(Modifier.height(28.dp)); LinearProgressIndicator(progress = { if (playing) .45f else .0f }, Modifier.fillMaxWidth().height(4.dp).clip(CircleShape), color = Purple, trackColor = Panel2); Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text("0:00", color = Muted, fontSize = 11.sp); Text("—", color = Muted, fontSize = 11.sp) }; Spacer(Modifier.height(24.dp)); Row(verticalAlignment = Alignment.CenterVertically) { IconButton(onClick = {}) { Icon(Icons.Default.Shuffle, null, tint = Muted) }; IconButton(onClick = {}) { Icon(Icons.Default.SkipPrevious, null, tint = White, modifier = Modifier.size(34.dp)) }; IconButton(onClick = toggle, modifier = Modifier.size(72.dp).clip(CircleShape).background(Brush.linearGradient(listOf(Pink, Purple)))) { Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White, modifier = Modifier.size(35.dp)) }; IconButton(onClick = {}) { Icon(Icons.Default.SkipNext, null, tint = White, modifier = Modifier.size(34.dp)) }; IconButton(onClick = {}) { Icon(Icons.Default.Repeat, null, tint = Muted) } } } } }

@Composable private fun Settings() { Column(Modifier.fillMaxSize().padding(20.dp).statusBarsPadding()) { Text("تنظیمات", color = White, fontSize = 29.sp, fontWeight = FontWeight.ExtraBold); Text("کنترل و اطلاعات BeatNova", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp, bottom = 22.dp)); Setting("اتصال آنلاین", if (BuildConfig.SUPABASE_URL.isBlank()) "تنظیم نشده" else "Supabase متصل", Icons.Default.Wifi); Setting("پخش‌کننده", "Media3 ExoPlayer", Icons.Default.Headphones); Setting("نسخه", "1.1.0 • Android 7+", Icons.Default.Info); Setting("ظاهر", "تم تیره BeatNova", Icons.Default.DarkMode); Spacer(Modifier.height(18.dp)); Text("BeatNova برای پخش محتوای قانونی و دارای مجوز طراحی شده است.", color = Muted, fontSize = 12.sp) } }
@Composable private fun Setting(title: String, value: String, icon: ImageVector) { Row(Modifier.fillMaxWidth().padding(vertical = 5.dp).clip(RoundedCornerShape(18.dp)).background(Panel).padding(15.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(44.dp).clip(RoundedCornerShape(14.dp)).background(Purple.copy(alpha = .13f)), contentAlignment = Alignment.Center) { Icon(icon, null, tint = Purple) }; Spacer(Modifier.width(13.dp)); Column { Text(title, color = White, fontWeight = FontWeight.Bold); Text(value, color = Muted, fontSize = 12.sp) } } }
@Composable private fun InfoBanner(error: String) { Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 5.dp).clip(RoundedCornerShape(16.dp)).background(Color(0xFF211A2C)).padding(13.dp), verticalAlignment = Alignment.CenterVertically) { Icon(Icons.Default.WifiOff, null, tint = Purple); Spacer(Modifier.width(10.dp)); Text(if (error == "CONFIG") "Supabase در Codemagic تنظیم نشده است." else "اتصال به سرویس موسیقی ناموفق بود.", color = Muted, fontSize = 12.sp) } }
@Composable private fun Empty() { Box(Modifier.fillMaxWidth().height(210.dp), contentAlignment = Alignment.Center) { Column(horizontalAlignment = Alignment.CenterHorizontally) { Box(Modifier.size(70.dp).clip(CircleShape).background(Panel2), contentAlignment = Alignment.Center) { Icon(Icons.Default.LibraryMusic, null, tint = Purple, modifier = Modifier.size(32.dp)) }; Spacer(Modifier.height(12.dp)); Text("هنوز آهنگی اضافه نشده", color = White, fontWeight = FontWeight.Bold); Text("آهنگ‌های مجاز را در جدول songs قرار بده.", color = Muted, fontSize = 12.sp) } } }
