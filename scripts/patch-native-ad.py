from pathlib import Path

p = Path("app/src/main/java/com/beatnova/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

old = '''@Composable private fun BeatNovaNativeAdSlot() {
    val context = LocalContext.current
    if (!AdManager.shouldShowAds(context)) return
    Card(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 7.dp), shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Panel)) {
        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Campaign, null, tint = Purple, modifier = Modifier.size(24.dp))
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) { Text("تبلیغ", color = Muted, fontSize = 10.sp, fontWeight = FontWeight.Bold); Text("جایگاه Native بعد از ساخت Placement فعال می‌شود", color = White, fontSize = 12.sp) }
        }
    }
}
'''

new = '''@Composable private fun BeatNovaNativeAdSlot() {
    // Until a dedicated Native placement is configured in Adivery, reuse the
    // verified Banner placement here instead of showing a fake placeholder.
    BeatNovaBannerAdSlot()
}
'''

if old in s:
    p.write_text(s.replace(old, new), encoding="utf-8")
    print("Replaced Native placeholder with the configured Adivery Banner slot.")
elif 'Until a dedicated Native placement is configured in Adivery' in s:
    print("Native placeholder replacement already applied.")
else:
    raise SystemExit("Expected Native ad placeholder was not found; refusing to modify the source.")
