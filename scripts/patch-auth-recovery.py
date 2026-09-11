from pathlib import Path

src = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = src.read_text()

# The auth-recovery UI/deep-link code is already committed in MainActivity.
# This CI patch only normalizes pasted email addresses and is intentionally
# idempotent so repeated workflow runs never duplicate imports or declarations.
old = '''private fun normalizeEmail(value: String): String = value
    .trim()
    .replace(Regex("[\\u200B-\\u200D\\uFEFF]"), "")
    .replace(Regex("\\s+"), "")
    .lowercase(Locale.ROOT)'''
new = '''private fun normalizeEmail(value: String): String = value
    .trim()
    .replace(Regex("[\\p{Cf}\\p{Z}]"), "")
    .replace(Regex("\\s+"), "")
    .lowercase(Locale.ROOT)'''
if old in s:
    s = s.replace(old, new)

src.write_text(s)
