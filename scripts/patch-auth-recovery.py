from pathlib import Path

src = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = src.read_text()

# The auth-recovery UI/deep-link code is already committed in MainActivity.
# This CI patch only hardens email normalization and input handling.
# It is intentionally idempotent so repeated workflow runs never duplicate code.
old = '''private fun normalizeEmail(value: String): String = value
    .trim()
    .replace(Regex("[\\p{Cf}\\p{Z}]"), "")
    .replace(Regex("\\s+"), "")
    .lowercase(Locale.ROOT)'''
new = '''private fun normalizeEmail(value: String): String = value
    .trim()
    .filter { it.code in 33..126 }
    .replace(Regex("\\s+"), "")
    .lowercase(Locale.ROOT)'''
if old in s:
    s = s.replace(old, new)
else:
    old_legacy = '''private fun normalizeEmail(value: String): String = value
    .trim()
    .replace(Regex("[\\u200B-\\u200D\\uFEFF]"), "")
    .replace(Regex("\\s+"), "")
    .lowercase(Locale.ROOT)'''
    if old_legacy in s:
        s = s.replace(old_legacy, new)

# Normalize pasted/typed input immediately as well as on submit.
s = s.replace('onValueChange = { email = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("ایمیل") }',
              'onValueChange = { email = normalizeEmail(it) }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("ایمیل") }')

src.write_text(s)