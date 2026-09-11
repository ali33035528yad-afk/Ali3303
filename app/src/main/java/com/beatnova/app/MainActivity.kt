package com.beatnova.app

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject

private const val CHANNEL_ID = "beatnova_playback"
private const val NOTIFICATION_ID = 1001
private const val ACTION_PLAY_PAUSE = "com.beatnova.app.PLAY_PAUSE"
private val Bg = Color(0xFF08090F)
private val Panel = Color(0xFF12141D)
private val White = Color(0xFFF8F8FC)
private val Muted = Color(0xFF9699A9)
private val Purple = Color(0xFFC65CFF)
private val Blue = Color(0xFF617CFF)
private val Pink = Color(0xFFFF3E9D)
private data class Song(val id: String, val title: String, val artist: String, val audioUrl: String)

private object SongRepository {
    private val client = OkHttpClient()
    suspend fun load(): Result<List<Song>> = withContext(Dispatchers.IO) {
        val base = BuildConfig.SUPABASE_URL.trimEnd('/'); val key = BuildConfig.SUPABASE_ANON_KEY
        if (base.isBlank() || key.isBlank()) return@withContext Result.failure(Exception("SUPABASE_CONFIG"))
        try {
            val request = Request.Builder().url("$base/rest/v1/songs?select=id,title,artist,audio_url&order=created_at.desc").addHeader("apikey", key).addHeader("Authorization", "Bearer $key").build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext Result.failure(Exception("HTTP_${response.code}"))
                val array = JSONArray(response.body?.string().orEmpty()); val result = mutableListOf<Song>()
                for (i in 0 until array.length()) { val o = array.getJSONObject(i); val audio = o.optString("audio_url"); if (audio.isNotBlank()) result += Song(o.optString("id", i.toString()), o.optString("title", "بدون نام"), o.optString("artist", "هنرمند ناشناس"), audio) }
                Result.success(result)
            }
        } catch (e: Exception) { Result.failure(e) }
    }
}

private object AuthRepository {
    private val client = OkHttpClient()
    private val jsonType = "application/json".toMediaType()
    suspend fun signUp(email: String, password: String): Result<String> = requestAuth("${BuildConfig.SUPABASE_URL.trimEnd('/')}/auth/v1/signup", email, password, false)
    suspend fun signIn(email: String, password: String): Result<String> = requestAuth("${BuildConfig.SUPABASE_URL.trimEnd('/')}/auth/v1/token?grant_type=password", email, password, true)
    private suspend fun requestAuth(url: String, email: String, password: String, saveToken: Boolean): Result<String> = withContext(Dispatchers.IO) {
        val key = BuildConfig.SUPABASE_ANON_KEY
        if (BuildConfig.SUPABASE_URL.isBlank() || key.isBlank()) return@withContext Result.failure(Exception("SUPABASE_CONFIG"))
        try {
            val body = JSONObject().put("email", email.trim()).put("password", password).toString().toRequestBody(jsonType)
            val request = Request.Builder().url(url).post(body).addHeader("apikey", key).addHeader("Content-Type", "application/json").build()
            client.newCall(request).execute().use { response ->
                val text = response.body?.string().orEmpty(); val obj = runCatching { JSONObject(text) }.getOrNull()
                if (!response.isSuccessful) return@withContext Result.failure(Exception(obj?.optString("msg")?.takeIf { it.isNotBlank() } ?: obj?.optString("error_description")?.takeIf { it.isNotBlank() } ?: "AUTH_HTTP_${response.code}"))
                val token = obj?.optString("access_token").orEmpty()
                if (saveToken && token.isNotBlank()) return@withContext Result.success("ورود موفق بود")
                if (token.isNotBlank()) return@withContext Result.success("ثبت‌نام موفق بود؛ وارد حساب شدی")
                Result.success("ثبت‌نام انجام شد؛ اگر تأیید ایمیل فعال باشد، ایمیل خود را تأیید کن.")
            }
        } catch (e: Exception) { Result.failure(e) }
    }
}

class MainActivity : ComponentActivity() {
    private val notificationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); createNotificationChannel(this); if (Build.VERSION.SDK_INT >= 33 && ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS); setContent { BeatNovaApp() } }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); if (intent.action == ACTION_PLAY_PAUSE) NotificationBus.toggle() }
}
private object NotificationBus { var toggle: () -> Unit = {} }
private fun createNotificationChannel(context: Context) { if (Build.VERSION.SDK_INT >= 26) context.getSystemService(NotificationManager::class.java).createNotificationChannel(NotificationChannel(CHANNEL_ID, "پخش BeatNova", NotificationManager.IMPORTANCE_LOW)) }
private fun showPlaybackNotification(context: Context, song: Song, playing: Boolean) { if (Build.VERSION.SDK_INT >= 33 && ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return; val actionIntent = PendingIntent.getActivity(context, 10, Intent(context, MainActivity::class.java).setAction(ACTION_PLAY_PAUSE), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE); val openIntent = PendingIntent.getActivity(context, 11, Intent(context, MainActivity::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE); val notification = NotificationCompat.Builder(context, CHANNEL_ID).setSmallIcon(R.drawable.ic_beatnova).setContentTitle(song.title).setContentText(song.artist).setContentIntent(openIntent).setPriority(NotificationCompat.PRIORITY_LOW).setOngoing(playing).setOnlyAlertOnce(true).setVisibility(NotificationCompat.VISIBILITY_PUBLIC).addAction(if (playing) android.R.drawable.ic_media_pause else android.R.drawable.ic_media_play, if (playing) "مکث" else "پخش", actionIntent).build(); NotificationManagerCompat.from(context).notify(NOTIFICATION_ID, notification) }
private fun clearPlaybackNotification(context: Context) = NotificationManagerCompat.from(context).cancel(NOTIFICATION_ID)

@Composable private fun BeatNovaApp() {
    val context = LocalContext.current; val player = remember { ExoPlayer.Builder(context).build() }; val scope = rememberCoroutineScope(); val prefs = remember { context.getSharedPreferences("beatnova_library", Context.MODE_PRIVATE) }
    var tab by remember { mutableIntStateOf(0) }; var songs by remember { mutableStateOf(emptyList<Song>()) }; var current by remember { mutableStateOf<Song?>(null) }; var playing by remember { mutableStateOf(false) }; var loading by remember { mutableStateOf(true) }; var error by remember { mutableStateOf<String?>(null) }; var query by remember { mutableStateOf("") }; var showAuth by remember { mutableStateOf(false) }
    var favorites by remember { mutableStateOf(prefs.getStringSet("favorites", emptySet())?.toSet() ?: emptySet()) }
    fun saveFavorites(value: Set<String>) { favorites = value; prefs.edit().putStringSet("favorites", value).apply() }; fun toggleFavorite(id: String) = saveFavorites(if (id in favorites) favorites - id else favorites + id)
    fun refresh() = scope.launch { loading = true; error = null; SongRepository.load().onSuccess { songs = it }.onFailure { error = it.message }; loading = false }
    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showPlaybackNotification(context, song, true) }
    fun togglePlay() { if (player.isPlaying) player.pause() else if (current != null) player.play(); current?.let { showPlaybackNotification(context, it, player.isPlaying) } }
    DisposableEffect(player) { val listener = object : Player.Listener { override fun onIsPlayingChanged(isPlaying: Boolean) { playing = isPlaying; current?.let { showPlaybackNotification(context, it, isPlaying) } }; override fun onPlaybackStateChanged(state: Int) { if (state == Player.STATE_ENDED) { playing = false; clearPlaybackNotification(context) } } }; NotificationBus.toggle = ::togglePlay; player.addListener(listener); onDispose { NotificationBus.toggle = {}; player.removeListener(listener); player.release(); clearPlaybackNotification(context) } }
    LaunchedEffect(Unit) { refresh() }
    MaterialTheme(colorScheme = darkColorScheme(primary = Purple, background = Bg, surface = Panel, onSurface = White)) {
        if (showAuth) { AuthScreen(onBack = { showAuth = false }) } else Column(Modifier.fillMaxSize().background(Bg)) {
            Box(Modifier.weight(1f).fillMaxWidth()) { when (tab) { 0 -> HomeScreen(songs, loading, error, current, playing, favorites, ::refresh, ::play, ::toggleFavorite); 1 -> SearchScreen(query, { query = it }, songs.filter { query.isBlank() || it.title.contains(query, true) || it.artist.contains(query, true) }, current, favorites, ::play, ::toggleFavorite); 2 -> LibraryScreen(songs.filter { it.id in favorites }, current, favorites, ::play, ::toggleFavorite); else -> SettingsScreen { showAuth = true } } }
            current?.let { MiniPlayer(it, playing, ::togglePlay) }; BottomBar(tab) { tab = it }
        }
    }
}

@Composable private fun AuthScreen(onBack: () -> Unit) {
    val scope = rememberCoroutineScope(); var register by remember { mutableStateOf(true) }; var email by remember { mutableStateOf("") }; var password by remember { mutableStateOf("") }; var busy by remember { mutableStateOf(false) }; var message by remember { mutableStateOf<String?>(null) }; var success by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().background(Bg).padding(22.dp)) {
        IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "بازگشت", tint = White) }
        Spacer(Modifier.height(10.dp)); Text(if (register) "ثبت‌نام در BeatNova" else "ورود به BeatNova", color = White, fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("حساب خودت را بساز و کتابخانه‌ات را شخصی‌تر کن", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp, bottom = 22.dp))
        OutlinedTextField(value = email, onValueChange = { email = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("ایمیل") }, leadingIcon = { Icon(Icons.Default.Email, null) }, shape = RoundedCornerShape(16.dp))
        Spacer(Modifier.height(12.dp)); OutlinedTextField(value = password, onValueChange = { password = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("رمز عبور") }, leadingIcon = { Icon(Icons.Default.Lock, null) }, visualTransformation = PasswordVisualTransformation(), shape = RoundedCornerShape(16.dp))
        Spacer(Modifier.height(18.dp)); Button(onClick = { if (email.isBlank() || password.length < 6) { message = "ایمیل را وارد کن و رمز عبور باید حداقل ۶ کاراکتر باشد."; return@Button }; busy = true; message = null; scope.launch { val result = if (register) AuthRepository.signUp(email, password) else AuthRepository.signIn(email, password); busy = false; result.onSuccess { message = it; success = true }.onFailure { message = it.message ?: "خطا در احراز هویت" } } }, enabled = !busy, modifier = Modifier.fillMaxWidth().height(52.dp), shape = RoundedCornerShape(16.dp)) { if (busy) CircularProgressIndicator(modifier = Modifier.size(22.dp), color = White) else Text(if (register) "ثبت‌نام" else "ورود", fontWeight = FontWeight.Bold) }
        message?.let { Spacer(Modifier.height(14.dp)); Text(it, color = if (success) Purple else Pink, fontSize = 13.sp) }
        Spacer(Modifier.height(20.dp)); Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) { Text(if (register) "قبلاً حساب داری؟ " else "حساب نداری؟ ", color = Muted); Text(if (register) "ورود" else "ثبت‌نام", color = Purple, fontWeight = FontWeight.Bold, modifier = Modifier.clickable { register = !register; message = null; success = false }) }
    }
}

@Composable private fun HomeScreen(songs: List<Song>, loading: Boolean, error: String?, current: Song?, playing: Boolean, favorites: Set<String>, refresh: () -> Unit, play: (Song) -> Unit, favorite: (String) -> Unit) { LazyColumn(modifier = Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 28.dp)) { item { Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 18.dp), verticalAlignment = Alignment.CenterVertically) { Column(Modifier.weight(1f)) { Text("موسیقی برای هر لحظه", color = Muted, fontSize = 13.sp); Text("BeatNova", color = White, fontSize = 32.sp, fontWeight = FontWeight.ExtraBold) }; IconButton(onClick = refresh) { Icon(Icons.Default.Refresh, "به‌روزرسانی", tint = White) } } }; item { HeroCard(songs.size, current != null && playing) }; item { SectionHeader("کشف موسیقی", "ویژه شما") }; item { FeatureCard("کتابخانه شخصی", "با زدن قلب، آهنگ را ذخیره کن", Icons.Default.Favorite, Purple) }; item { SectionHeader("جدیدترین آهنگ‌ها", "${songs.size} آهنگ") }; when { loading -> item { LoadingBox() }; error != null -> item { EmptyState("اتصال به کتابخانه آماده نیست", "Supabase یا جدول songs را بررسی کن", Icons.Default.CloudOff) }; songs.isEmpty() -> item { EmptyState("هنوز آهنگی اضافه نشده", "آهنگ‌های مجاز خودت را در جدول songs قرار بده.", Icons.Default.LibraryMusic) }; else -> items(songs.take(30), key = { it.id }) { song -> SongRow(song, current?.id == song.id, song.id in favorites, play, favorite) } } } }
@Composable private fun HeroCard(count: Int, isPlaying: Boolean) { Box(Modifier.fillMaxWidth().padding(horizontal = 16.dp).clip(RoundedCornerShape(30.dp)).background(Brush.linearGradient(listOf(Color(0xFF32135C), Color(0xFF1B2354), Color(0xFF12131D)))).padding(22.dp)) { Column { Row(verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(64.dp).clip(RoundedCornerShape(20.dp)).background(Brush.linearGradient(listOf(Pink, Purple))), contentAlignment = Alignment.Center) { Icon(Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(34.dp)) }; Spacer(Modifier.width(14.dp)); Column { Text("ONLINE MUSIC", color = Color(0xFFE0B9FF), fontSize = 11.sp, fontWeight = FontWeight.Bold); Text("صدای لحظه‌های تو", color = White, fontSize = 21.sp, fontWeight = FontWeight.ExtraBold) } }; Spacer(Modifier.height(20.dp)); Text("کشف کن • پخش کن • لذت ببر", color = White, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold); Spacer(Modifier.height(7.dp)); Text("BeatNova برای کتابخانه موسیقی مجاز تو.", color = Color(0xFFD1D0DC), fontSize = 13.sp); Spacer(Modifier.height(18.dp)); Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { BadgePill("$count آهنگ", Icons.Default.QueueMusic); BadgePill(if (isPlaying) "در حال پخش" else "آماده پخش", Icons.Default.PlayArrow) } } } }
@Composable private fun FeatureCard(title: String, subtitle: String, icon: ImageVector, color: Color) { Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 5.dp).clip(RoundedCornerShape(22.dp)).background(Panel).padding(15.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(50.dp).clip(RoundedCornerShape(16.dp)).background(color.copy(alpha = .14f)), contentAlignment = Alignment.Center) { Icon(icon, null, tint = color, modifier = Modifier.size(25.dp)) }; Spacer(Modifier.width(13.dp)); Column(Modifier.weight(1f)) { Text(title, color = White, fontWeight = FontWeight.Bold, fontSize = 15.sp); Text(subtitle, color = Muted, fontSize = 11.sp, maxLines = 2) }; Icon(Icons.Default.ChevronLeft, null, tint = Muted) } }
@Composable private fun BadgePill(text: String, icon: ImageVector) { Row(Modifier.clip(CircleShape).background(Color.White.copy(alpha = .10f)).padding(horizontal = 11.dp, vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) { Icon(icon, null, tint = White, modifier = Modifier.size(15.dp)); Spacer(Modifier.width(5.dp)); Text(text, color = White, fontSize = 11.sp, fontWeight = FontWeight.SemiBold) } }
@Composable private fun SectionHeader(title: String, action: String) { Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 15.dp), verticalAlignment = Alignment.CenterVertically) { Text(title, color = White, fontSize = 19.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); Text(action, color = Purple, fontSize = 12.sp, fontWeight = FontWeight.Bold) } }
@Composable private fun LoadingBox() { Box(Modifier.fillMaxWidth().height(150.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Purple) } }
@Composable private fun EmptyState(title: String, subtitle: String, icon: ImageVector) { Column(Modifier.fillMaxWidth().padding(24.dp).clip(RoundedCornerShape(24.dp)).background(Panel).padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally) { Icon(icon, null, tint = Purple, modifier = Modifier.size(42.dp)); Spacer(Modifier.height(12.dp)); Text(title, color = White, fontSize = 16.sp, fontWeight = FontWeight.Bold); Spacer(Modifier.height(5.dp)); Text(subtitle, color = Muted, fontSize = 12.sp) } }
@Composable private fun SongRow(song: Song, selected: Boolean, favorite: Boolean, play: (Song) -> Unit, onFavorite: (String) -> Unit) { Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 5.dp).clip(RoundedCornerShape(18.dp)).background(if (selected) Color(0xFF241A35) else Panel).clickable { play(song) }.padding(10.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(52.dp).clip(RoundedCornerShape(15.dp)).background(Brush.linearGradient(listOf(Blue, Purple))), contentAlignment = Alignment.Center) { Icon(if (selected) Icons.Default.GraphicEq else Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(25.dp)) }; Spacer(Modifier.width(11.dp)); Column(Modifier.weight(1f)) { Text(song.title, color = White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis); Text(song.artist, color = Muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis) }; IconButton(onClick = { onFavorite(song.id) }) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "کتابخانه شخصی", tint = if (favorite) Pink else Muted) }; Icon(if (selected) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White) } }
@Composable private fun SearchScreen(query: String, onQuery: (String) -> Unit, songs: List<Song>, current: Song?, favorites: Set<String>, play: (Song) -> Unit, favorite: (String) -> Unit) { Column(Modifier.fillMaxSize().padding(top = 22.dp)) { Text("جستجو", color = White, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 20.dp)); Text("آهنگ یا هنرمند مورد علاقه‌ات را پیدا کن", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)); OutlinedTextField(value = query, onValueChange = onQuery, modifier = Modifier.fillMaxWidth().padding(16.dp), singleLine = true, placeholder = { Text("نام آهنگ یا خواننده") }, leadingIcon = { Icon(Icons.Default.Search, null) }, shape = RoundedCornerShape(18.dp)); LazyColumn(contentPadding = PaddingValues(bottom = 24.dp)) { if (songs.isEmpty()) item { EmptyState("نتیجه‌ای پیدا نشد", "جستجو را تغییر بده.", Icons.Default.SearchOff) } else items(songs, key = { it.id }) { SongRow(it, current?.id == it.id, it.id in favorites, play, favorite) } } } }
@Composable private fun LibraryScreen(songs: List<Song>, current: Song?, favorites: Set<String>, play: (Song) -> Unit, favorite: (String) -> Unit) { Column(Modifier.fillMaxSize().padding(top = 22.dp)) { Text("کتابخانه من", color = White, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 20.dp)); Text("${songs.size} آهنگ ذخیره‌شده", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp)); LazyColumn(contentPadding = PaddingValues(top = 14.dp, bottom = 24.dp)) { if (songs.isEmpty()) item { EmptyState("کتابخانه خالی است", "با زدن قلب کنار هر آهنگ، آن را به کتابخانه شخصی بفرست.", Icons.Default.FavoriteBorder) } else items(songs, key = { it.id }) { SongRow(it, current?.id == it.id, it.id in favorites, play, favorite) } } } }
@Composable private fun SettingsScreen(onAccount: () -> Unit) { Column(Modifier.fillMaxSize().padding(22.dp)) { Text("تنظیمات", color = White, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold); Spacer(Modifier.height(20.dp)); Row(Modifier.fillMaxWidth().padding(vertical = 5.dp).clip(RoundedCornerShape(20.dp)).background(Panel).clickable { onAccount() }.padding(17.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(48.dp).clip(RoundedCornerShape(15.dp)).background(Purple.copy(alpha = .14f)), contentAlignment = Alignment.Center) { Icon(Icons.Default.PersonAdd, null, tint = Purple, modifier = Modifier.size(26.dp)) }; Spacer(Modifier.width(14.dp)); Column(Modifier.weight(1f)) { Text("ثبت‌نام / ورود", color = White, fontWeight = FontWeight.Bold, fontSize = 16.sp); Text("ساخت حساب کاربری با Supabase", color = Muted, fontSize = 11.sp) }; Icon(Icons.Default.ChevronLeft, null, tint = Muted) }; Spacer(Modifier.height(8.dp)); SettingRow("کیفیت پخش", "بهینه برای اینترنت موبایل", Icons.Default.HighQuality); SettingRow("ظاهر برنامه", "تم تیره BeatNova", Icons.Default.DarkMode); SettingRow("درباره BeatNova", "نسخه 1.2.0", Icons.Default.Info) } }
@Composable private fun SettingRow(title: String, subtitle: String, icon: ImageVector) { Row(Modifier.fillMaxWidth().padding(vertical = 5.dp).clip(RoundedCornerShape(18.dp)).background(Panel).padding(15.dp), verticalAlignment = Alignment.CenterVertically) { Icon(icon, null, tint = Purple, modifier = Modifier.size(25.dp)); Spacer(Modifier.width(14.dp)); Column { Text(title, color = White, fontWeight = FontWeight.Bold); Text(subtitle, color = Muted, fontSize = 11.sp) } } }
@Composable private fun MiniPlayer(song: Song, playing: Boolean, toggle: () -> Unit) { Row(Modifier.fillMaxWidth().background(Color(0xFF171824)).padding(horizontal = 14.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.size(44.dp).clip(RoundedCornerShape(14.dp)).background(Brush.linearGradient(listOf(Pink, Purple))), contentAlignment = Alignment.Center) { Icon(Icons.Default.MusicNote, null, tint = White) }; Spacer(Modifier.width(10.dp)); Column(Modifier.weight(1f)) { Text(song.title, color = White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis); Text(song.artist, color = Muted, fontSize = 11.sp) }; IconButton(onClick = toggle) { Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White) } } }
@Composable private fun BottomBar(selected: Int, onSelect: (Int) -> Unit) { Row(Modifier.fillMaxWidth().height(76.dp).background(Color(0xFF0E0F16)), verticalAlignment = Alignment.CenterVertically) { BottomItem(0, "خانه", Icons.Default.Home, selected, onSelect); BottomItem(1, "جستجو", Icons.Default.Search, selected, onSelect); BottomItem(2, "کتابخانه", Icons.Default.LibraryMusic, selected, onSelect); BottomItem(3, "تنظیمات", Icons.Default.Settings, selected, onSelect) } }
@Composable private fun RowScope.BottomItem(index: Int, label: String, icon: ImageVector, selected: Int, onSelect: (Int) -> Unit) { val active = index == selected; Box(Modifier.weight(1f).fillMaxHeight().clickable { onSelect(index) }, contentAlignment = Alignment.Center) { Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(icon, null, tint = if (active) Purple else Muted, modifier = Modifier.size(25.dp)); Spacer(Modifier.height(3.dp)); Text(label, color = if (active) White else Muted, fontSize = 11.sp, fontWeight = if (active) FontWeight.Bold else FontWeight.Normal) } } }
