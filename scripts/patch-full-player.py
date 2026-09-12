from pathlib import Path

p = Path("app/src/main/java/com/beatnova/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

if "FullPlayerScreen(" in s:
    print("Full Player already integrated.")
    raise SystemExit(0)

old = 'var tab by remember { mutableIntStateOf(0) }; var loggedInEmail by remember { mutableStateOf(AuthSession.email) }; var songs by remember { mutableStateOf(emptyList<Song>()) }; var current by remember { mutableStateOf<Song?>(null) }; var playing by remember { mutableStateOf(false) }; var loading by remember { mutableStateOf(true) };'
new = 'var tab by remember { mutableIntStateOf(0) }; var loggedInEmail by remember { mutableStateOf(AuthSession.email) }; var songs by remember { mutableStateOf(emptyList<Song>()) }; var current by remember { mutableStateOf<Song?>(null) }; var playing by remember { mutableStateOf(false) }; var showFullPlayer by remember { mutableStateOf(false) }; var playerProgress by remember { mutableFloatStateOf(0f) }; var playerDuration by remember { mutableLongStateOf(0L) }; var loading by remember { mutableStateOf(true) };'
if old not in s: raise SystemExit("Player state anchor not found.")
s = s.replace(old, new, 1)

old = 'fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showPlaybackNotification(context, song, true) }'
new = 'fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true) }'
if old not in s: raise SystemExit("play() anchor not found.")
s = s.replace(old, new, 1)

anchor = '    LaunchedEffect(Unit) { refresh() }'
progress = '''    LaunchedEffect(showFullPlayer, current) {
        while (showFullPlayer && current != null) {
            playerDuration = player.duration.takeIf { it > 0 } ?: 0L
            playerProgress = if (playerDuration > 0) (player.currentPosition.toFloat() / playerDuration).coerceIn(0f, 1f) else 0f
            kotlinx.coroutines.delay(500)
        }
    }
'''
if anchor not in s: raise SystemExit("LaunchedEffect anchor not found.")
s = s.replace(anchor, progress + anchor, 1)

old = 'if (recoveryUrl?.startsWith("beatnova://auth/recovery") == true) { PasswordRecoveryScreen(recoveryUrl = recoveryUrl, onDone = { AuthRecoveryBus.url = null }) } else if (showAuth) { AuthScreen(onBack = { showAuth = false }, onAuthSuccess = { loggedInEmail = AuthSession.email; showAuth = false }) } else Column(Modifier.fillMaxSize().background(Bg)) {'
new = '''if (recoveryUrl?.startsWith("beatnova://auth/recovery") == true) {
            PasswordRecoveryScreen(recoveryUrl = recoveryUrl, onDone = { AuthRecoveryBus.url = null })
        } else if (showAuth) {
            AuthScreen(onBack = { showAuth = false }, onAuthSuccess = { loggedInEmail = AuthSession.email; showAuth = false })
        } else if (showFullPlayer && current != null) {
            FullPlayerScreen(song = current!!, playing = playing, progress = playerProgress, duration = playerDuration,
                isFavorite = current!!.id in favorites, onBack = { showFullPlayer = false }, onToggle = ::togglePlay,
                onFavorite = { toggleFavorite(current!!.id) },
                onSeek = { fraction -> if (playerDuration > 0) player.seekTo((playerDuration * fraction).toLong()) },
                onNext = { val i = songs.indexOfFirst { it.id == current!!.id }; if (i >= 0 && i + 1 < songs.size) play(songs[i + 1]) },
                onPrevious = { val i = songs.indexOfFirst { it.id == current!!.id }; if (i > 0) play(songs[i - 1]) })
        } else Column(Modifier.fillMaxSize().background(Bg)) {'''
if old not in s: raise SystemExit("Root content anchor not found.")
s = s.replace(old, new, 1)

old = 'current?.let { MiniPlayer(it, playing, ::togglePlay) }; BottomBar(tab) { tab = it }'
new = 'current?.let { MiniPlayer(it, playing, ::togglePlay, open = { showFullPlayer = true }) }; BottomBar(tab) { tab = it }'
if old not in s: raise SystemExit("MiniPlayer call anchor not found.")
s = s.replace(old, new, 1)

marker = '@Composable private fun AuthScreen(onBack: () -> Unit, onAuthSuccess: () -> Unit) {'
full_player = '''@Composable private fun FullPlayerScreen(
    song: Song,
    playing: Boolean,
    progress: Float,
    duration: Long,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onToggle: () -> Unit,
    onFavorite: () -> Unit,
    onSeek: (Float) -> Unit,
    onNext: () -> Unit,
    onPrevious: () -> Unit,
) {
    val minutes = { ms: Long -> "${ms / 60000}:${((ms / 1000) % 60).toString().padStart(2, '0')}" }
    Column(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xFF1B1028), Bg, Color(0xFF090A12)))).padding(horizontal = 20.dp, vertical = 14.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.Default.KeyboardArrowDown, "بستن", tint = White) }
            Text("در حال پخش", color = White, fontWeight = FontWeight.Bold, fontSize = 16.sp, modifier = Modifier.weight(1f))
            IconButton(onClick = onFavorite) { Icon(if (isFavorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "پسندیدن", tint = if (isFavorite) Pink else White) }
        }
        Spacer(Modifier.height(22.dp))
        Box(Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(30.dp)).background(Brush.linearGradient(listOf(Purple, Blue, Pink))), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(Icons.Default.MusicNote, null, tint = White, modifier = Modifier.size(92.dp))
                Spacer(Modifier.height(12.dp))
                Text("BEATNOVA", color = White, fontSize = 27.sp, fontWeight = FontWeight.Black, letterSpacing = 3.sp)
                Text("MUSIC • PLAYER", color = White.copy(alpha = .78f), fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 2.sp)
            }
        }
        Spacer(Modifier.height(24.dp))
        Text(song.title, color = White, fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(song.artist, color = Muted, fontSize = 14.sp, modifier = Modifier.padding(top = 5.dp))
        Spacer(Modifier.height(18.dp))
        Slider(value = progress, onValueChange = onSeek, modifier = Modifier.fillMaxWidth(), colors = SliderDefaults.colors(thumbColor = Purple, activeTrackColor = Purple, inactiveTrackColor = Color.White.copy(alpha = .18f)))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(minutes((duration * progress).toLong()), color = Muted, fontSize = 11.sp)
            Text(minutes(duration), color = Muted, fontSize = 11.sp)
        }
        Spacer(Modifier.height(12.dp))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceEvenly) {
            IconButton(onClick = onPrevious, modifier = Modifier.size(48.dp)) { Icon(Icons.Default.SkipPrevious, "قبلی", tint = White, modifier = Modifier.size(30.dp)) }
            FilledIconButton(onClick = onToggle, modifier = Modifier.size(72.dp), colors = IconButtonDefaults.filledIconButtonColors(containerColor = White)) {
                Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, if (playing) "مکث" else "پخش", tint = Bg, modifier = Modifier.size(38.dp))
            }
            IconButton(onClick = onNext, modifier = Modifier.size(48.dp)) { Icon(Icons.Default.SkipNext, "بعدی", tint = White, modifier = Modifier.size(30.dp)) }
        }
        Spacer(Modifier.height(16.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
            Icon(Icons.Default.GraphicEq, null, tint = Purple, modifier = Modifier.size(22.dp))
            Spacer(Modifier.width(8.dp))
            Text("BeatNova • پخش‌کننده موسیقی", color = Muted, fontSize = 12.sp)
        }
    }
}

'''
if marker not in s: raise SystemExit("AuthScreen marker not found.")
s = s.replace(marker, full_player + marker, 1)

old = '@Composable private fun MiniPlayer(song: Song, playing: Boolean, toggle: () -> Unit) { Row(Modifier.fillMaxWidth().background(Color(0xFF171824)).padding(horizontal = 14.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {'
new = '@Composable private fun MiniPlayer(song: Song, playing: Boolean, toggle: () -> Unit, open: () -> Unit) { Row(Modifier.fillMaxWidth().background(Color(0xFF171824)).clickable(onClick = open).padding(horizontal = 14.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {'
if old not in s: raise SystemExit("MiniPlayer definition anchor not found.")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("Full Player patch applied.")