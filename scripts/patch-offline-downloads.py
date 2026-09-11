from pathlib import Path

src = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = src.read_text()

# Song is shared with the offline-download feature file.
s = s.replace('private data class Song(val id: String, val title: String, val artist: String, val audioUrl: String)',
              'data class Song(val id: String, val title: String, val artist: String, val audioUrl: String)', 1)

# Initialize the persistent Media3 download/cache stack before Compose creates the player.
s = s.replace(
    'override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); AuthSession.init(this); AuthRecoveryBus.url = intent?.dataString;',
    'override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); AuthSession.init(this); BeatNovaDownloads.initialize(this); AuthRecoveryBus.url = intent?.dataString;',
    1,
)

# Make ExoPlayer read from the same persistent cache used by Media3 downloads.
s = s.replace(
    'val context = LocalContext.current; val player = remember { ExoPlayer.Builder(context).build() };',
    'val context = LocalContext.current; val player = remember { ExoPlayer.Builder(context).setMediaSourceFactory(BeatNovaDownloads.mediaSourceFactory(context)).build() };',
    1,
)

# Add a dedicated Downloads tab and keep Settings as the fifth tab.
s = s.replace(
    '2 -> LibraryScreen(songs.filter { it.id in favorites }, current, favorites, ::play, ::toggleFavorite); else -> if (loggedInEmail.isNullOrBlank()) SettingsScreen { showAuth = true } else LoggedInSettingsScreen(loggedInEmail!!, onLogout = { AuthSession.clear(); loggedInEmail = null })',
    '2 -> LibraryScreen(songs.filter { it.id in favorites }, current, favorites, ::play, ::toggleFavorite); 3 -> DownloadsScreen(songs, current, playing, ::play); else -> if (loggedInEmail.isNullOrBlank()) SettingsScreen { showAuth = true } else LoggedInSettingsScreen(loggedInEmail!!, onLogout = { AuthSession.clear(); loggedInEmail = null })',
    1,
)

# Give every online song a dedicated download action and use deterministic artwork/iconography.
old_song_icon = 'Box(Modifier.size(52.dp).clip(RoundedCornerShape(15.dp)).background(Brush.linearGradient(listOf(Blue, Purple))), contentAlignment = Alignment.Center) { Icon(if (selected) Icons.Default.GraphicEq else Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(25.dp)) };'
new_song_icon = 'Box(Modifier.size(52.dp).clip(RoundedCornerShape(15.dp)).background(Brush.linearGradient(listOf(Blue, Purple))), contentAlignment = Alignment.Center) { BeatNovaSongIcon(song, selected) };'
if old_song_icon in s:
    s = s.replace(old_song_icon, new_song_icon, 1)

old_actions = 'IconButton(onClick = { onFavorite(song.id) }) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "کتابخانه شخصی", tint = if (favorite) Pink else Muted) }; Icon(if (selected) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White)'
new_actions = 'IconButton(onClick = { onFavorite(song.id) }) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "کتابخانه شخصی", tint = if (favorite) Pink else Muted) }; BeatNovaDownloadButton(song); Icon(if (selected) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = White)'
if old_actions in s:
    s = s.replace(old_actions, new_actions, 1)

# Replace the four-item bottom bar with five items: Home, Search, Library, Downloads, Settings.
old_bottom = '@Composable private fun BottomBar(selected: Int, onSelect: (Int) -> Unit) { Row(Modifier.fillMaxWidth().height(76.dp).background(Color(0xFF0E0F16)), verticalAlignment = Alignment.CenterVertically) { BottomItem(0, "خانه", Icons.Default.Home, selected, onSelect); BottomItem(1, "جستجو", Icons.Default.Search, selected, onSelect); BottomItem(2, "کتابخانه", Icons.Default.LibraryMusic, selected, onSelect); BottomItem(3, "تنظیمات", Icons.Default.Settings, selected, onSelect) } }'
new_bottom = '@Composable private fun BottomBar(selected: Int, onSelect: (Int) -> Unit) { Row(Modifier.fillMaxWidth().height(76.dp).background(Color(0xFF0E0F16)), verticalAlignment = Alignment.CenterVertically) { BottomItem(0, "خانه", Icons.Default.Home, selected, onSelect); BottomItem(1, "جستجو", Icons.Default.Search, selected, onSelect); BottomItem(2, "کتابخانه", Icons.Default.LibraryMusic, selected, onSelect); BottomItem(3, "دانلودها", Icons.Default.Download, selected, onSelect); BottomItem(4, "تنظیمات", Icons.Default.Settings, selected, onSelect) } }'
if old_bottom in s:
    s = s.replace(old_bottom, new_bottom, 1)

src.write_text(s)
