from pathlib import Path

P = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = P.read_text(encoding='utf-8')

# The source now contains the real Adivery Compose integration. Keep the CI patch
# idempotent so it never re-inserts the old provider-neutral placeholder slots.
if 'BeatNovaAdiveryBanner' in s:
    print('Adivery banner integration already present; no legacy ads patch needed.')
    raise SystemExit(0)


def replace_once(old: str, new: str, label: str):
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'Expected source fragment not found: {label}')
    s = s.replace(old, new, 1)

replace_once(
    'val context = LocalContext.current; val player = remember { ExoPlayer.Builder(context).setMediaSourceFactory(BeatNovaDownloads.mediaSourceFactory(context)).build() };',
    'val context = LocalContext.current; AdManager.initialize(context); val player = remember { ExoPlayer.Builder(context).setMediaSourceFactory(BeatNovaDownloads.mediaSourceFactory(context)).build() };',
    'initialize AdManager',
)

replace_once(
    'item { HeroCard(songs.size, current != null && playing) }; item { SectionHeader("کشف موسیقی", "ویژه شما") };',
    'item { HeroCard(songs.size, current != null && playing) }; item { BeatNovaBannerAdSlot() }; item { SectionHeader("کشف موسیقی", "ویژه شما") };',
    'home banner slot',
)

replace_once(
    'else -> items(songs.take(30), key = { it.id }) { song -> SongRow(song, current?.id == song.id, song.id in favorites, play, favorite) }',
    'else -> { songs.take(30).forEachIndexed { index, song -> item(key = song.id) { SongRow(song, current?.id == song.id, song.id in favorites, play, favorite) }; if (index == 4) item(key = "native-ad-slot") { BeatNovaNativeAdSlot() } } }',
    'native ad slot',
)

replace_once(
    '@Composable private fun SettingsScreen(onAccount: () -> Unit) {',
    '@Composable private fun BeatNovaBannerAdSlot() {\n    val context = LocalContext.current\n    if (!AdManager.shouldShowAds(context)) return\n    Card(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Panel)) {\n        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {\n            Icon(Icons.Default.Campaign, null, tint = Purple, modifier = Modifier.size(22.dp))\n            Spacer(Modifier.width(10.dp))\n            Column(Modifier.weight(1f)) { Text("تبلیغ", color = Muted, fontSize = 10.sp, fontWeight = FontWeight.Bold); Text("جایگاه Banner آماده اتصال به شبکه تبلیغاتی", color = White, fontSize = 12.sp) }\n        }\n    }\n}\n\n@Composable private fun BeatNovaNativeAdSlot() {\n    val context = LocalContext.current\n    if (!AdManager.shouldShowAds(context)) return\n    Card(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 7.dp), shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Panel)) {\n        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {\n            Icon(Icons.Default.Campaign, null, tint = Purple, modifier = Modifier.size(24.dp))\n            Spacer(Modifier.width(10.dp))\n            Column(Modifier.weight(1f)) { Text("تبلیغ", color = Muted, fontSize = 10.sp, fontWeight = FontWeight.Bold); Text("جایگاه Native آماده اتصال به شبکه تبلیغاتی", color = White, fontSize = 12.sp) }\n        }\n    }\n}\n\n@Composable private fun SettingsScreen(onAccount: () -> Unit) {',
    'ad slot composables',
)

replace_once(
    'SettingRow("درباره BeatNova", "نسخه 1.2.0", Icons.Default.Info)',
    'SettingRow("درباره BeatNova", "سازنده: علی ساحلی • نسخه ${BuildConfig.VERSION_NAME}", Icons.Default.Info)',
    'logged-out about',
)

replace_once(
    'Text("درباره BeatNova", color = White, fontSize = 18.sp, fontWeight = FontWeight.Bold)\n        Text("نسخه 1.2.0", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))',
    'Text("درباره BeatNova", color = White, fontSize = 18.sp, fontWeight = FontWeight.Bold)\n        Text("سازنده: علی ساحلی", color = White, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 6.dp))\n        Text("نسخه ${BuildConfig.VERSION_NAME}", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp))\n        Text("BeatNova؛ پخش و مدیریت موسیقی مجاز با کتابخانه شخصی و دانلود آفلاین.", color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))',
    'logged-in about',
)

P.write_text(s, encoding='utf-8')
print('Applied provider-neutral ads architecture and About/creator section.')
