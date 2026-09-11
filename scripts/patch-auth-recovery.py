from pathlib import Path

src = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = src.read_text()

# The auth-recovery UI/deep-link code is already committed in MainActivity.
# This CI patch hardens email input and makes successful Supabase auth visible
# and persistent in the app's Settings screen.
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

# Add a small persistent local auth-session store. Supabase returns access and
# refresh tokens for a successful session; we keep them locally so the UI can
# restore the signed-in account after the auth screen is closed/reopened.
if 'private object AuthSession {' not in s:
    marker = 'private object AuthRepository {'
    auth_session = '''private object AuthSession {
    private const val PREFS = "beatnova_auth"
    private const val KEY_EMAIL = "email"
    private const val KEY_ACCESS = "access_token"
    private const val KEY_REFRESH = "refresh_token"
    private var prefs: android.content.SharedPreferences? = null

    fun init(context: Context) {
        prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    }

    val email: String?
        get() = prefs?.getString(KEY_EMAIL, null)?.takeIf { it.isNotBlank() }

    fun save(email: String, accessToken: String, refreshToken: String) {
        prefs?.edit()
            ?.putString(KEY_EMAIL, email)
            ?.putString(KEY_ACCESS, accessToken)
            ?.putString(KEY_REFRESH, refreshToken)
            ?.apply()
    }

    fun clear() {
        prefs?.edit()?.clear()?.apply()
    }
}

'''
    s = s.replace(marker, auth_session + marker, 1)

# Initialize the session store before Compose starts.
s = s.replace('override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); AuthRecoveryBus.url = intent?.dataString;',
              'override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); AuthSession.init(this); AuthRecoveryBus.url = intent?.dataString;', 1)

# Persist the Supabase session whenever Auth returns an access token.
old_token = '''val token = obj?.optString("access_token").orEmpty()
                if (saveToken && token.isNotBlank()) return@withContext Result.success("ورود موفق بود")
                if (token.isNotBlank()) return@withContext Result.success("ثبت‌نام موفق بود؛ وارد حساب شدی")'''
new_token = '''val token = obj?.optString("access_token").orEmpty()
                val refreshToken = obj?.optString("refresh_token").orEmpty()
                val returnedEmail = obj?.optJSONObject("user")?.optString("email")?.takeIf { it.isNotBlank() } ?: cleanEmail
                if (token.isNotBlank()) {
                    AuthSession.save(returnedEmail, token, refreshToken)
                    if (saveToken) return@withContext Result.success("ورود موفق بود")
                    return@withContext Result.success("ثبت‌نام موفق بود؛ وارد حساب شدی")
                }'''
if old_token in s:
    s = s.replace(old_token, new_token, 1)

# Keep the logged-in account in Compose state and show a real account screen
# instead of the generic "ثبت‌نام / ورود" card after successful sign-in.
s = s.replace('var tab by remember { mutableIntStateOf(0) }; var songs by remember { mutableStateOf(emptyList<Song>()) };',
              'var tab by remember { mutableIntStateOf(0) }; var loggedInEmail by remember { mutableStateOf(AuthSession.email) }; var songs by remember { mutableStateOf(emptyList<Song>()) };', 1)
s = s.replace('else if (showAuth) { AuthScreen(onBack = { showAuth = false }) } else Column',
              'else if (showAuth) { AuthScreen(onBack = { showAuth = false }, onAuthSuccess = { loggedInEmail = AuthSession.email; showAuth = false }) } else Column', 1)
s = s.replace('else -> SettingsScreen { showAuth = true } } }',
              'else -> if (loggedInEmail.isNullOrBlank()) SettingsScreen { showAuth = true } else LoggedInSettingsScreen(loggedInEmail!!, onLogout = { AuthSession.clear(); loggedInEmail = null }) } }', 1)

# Auth screen reports a successful session to the parent so the Settings tab
# immediately reflects the signed-in account.
s = s.replace('@Composable private fun AuthScreen(onBack: () -> Unit) {',
              '@Composable private fun AuthScreen(onBack: () -> Unit, onAuthSuccess: () -> Unit) {', 1)
s = s.replace('result.onSuccess { message = it; success = true }.onFailure { message = it.message ?: "خطا در احراز هویت" }',
              'result.onSuccess { message = it; success = true; if (it.contains("ورود موفق") || it.contains("ثبت‌نام موفق")) onAuthSuccess() }.onFailure { message = it.message ?: "خطا در احراز هویت" }', 1)

# Add the authenticated Settings screen once, before the recovery screen.
if 'private fun LoggedInSettingsScreen(' not in s:
    marker = '@Composable private fun PasswordRecoveryScreen('
    account_screen = '''@Composable private fun LoggedInSettingsScreen(email: String, onLogout: () -> Unit) {
    Column(Modifier.fillMaxSize().background(Bg).padding(horizontal = 22.dp, vertical = 18.dp)) {
        Text("تنظیمات", color = White, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(bottom = 24.dp))
        Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = Panel)) {
            Column(Modifier.fillMaxWidth().padding(20.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(58.dp).clip(RoundedCornerShape(18.dp)).background(Purple.copy(alpha = 0.18f)), contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.AccountCircle, contentDescription = null, tint = Purple, modifier = Modifier.size(34.dp))
                    }
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f)) {
                        Text("حساب کاربری", color = White, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                        Text(email, color = Muted, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
                Spacer(Modifier.height(18.dp))
                Text("وضعیت: وارد شده", color = Purple, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(14.dp))
                OutlinedButton(onClick = onLogout, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
                    Icon(Icons.Default.Logout, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("خروج از حساب")
                }
            }
        }
        Spacer(Modifier.height(18.dp))
        Text("کیفیت پخش", color = White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Text("بهینه برای اینترنت موبایل", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
        Spacer(Modifier.height(18.dp))
        Text("ظاهر برنامه", color = White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Text("تم تیره BeatNova", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
        Spacer(Modifier.height(18.dp))
        Text("درباره BeatNova", color = White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Text("نسخه 1.2.0", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
    }
}

'''
    s = s.replace(marker, account_screen + marker, 1)

src.write_text(s)