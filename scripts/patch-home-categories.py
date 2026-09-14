from pathlib import Path
p = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = p.read_text(encoding='utf-8')

# Keep the original four visible categories stable, while filtering the live Supabase catalog by genre.
s = s.replace(
    'val genres = remember(songs) { listOf("همه") + songs.map { it.genre.trim() }.filter { it.isNotBlank() }.distinct().take(8) }',
    'val genres = listOf("همه", "سایر", "ایرانی", "الکترونیک", "بین‌الملل")',
    1,
)
# Prefer explicitly trending songs; if metadata is missing, keep a deterministic 3-card recommendation row.
s = s.replace(
    'val featured = songs.filter { it.isTrending }.ifEmpty { songs }.take(3)',
    'val featured = songs.filter { it.isTrending }.take(3).ifEmpty { songs.filter { it.id in setOf("3", "4", "5") }.take(3) }.ifEmpty { songs.take(3) }',
    1,
)
p.write_text(s, encoding='utf-8')
print('Fixed BeatNova categories and featured recommendations')
