from pathlib import Path

src = Path('app/src/main/java/com/beatnova/app/MainActivity.kt')
s = src.read_text()
s = s.replace('import android.content.pm.PackageManager\n', 'import android.content.pm.PackageManager\nimport android.net.Uri\n')
s = s.replace('private object NotificationBus { var toggle: () -> Unit = {} }\n', 'private object NotificationBus { var toggle: () -> Unit = {} }\nprivate object AuthRecoveryBus { var url by mutableStateOf<String?>(null) }\n')
s = s.replace('override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); createNotificationChannel(this);', 'override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); AuthRecoveryBus.url = intent?.dataString; createNotificationChannel(this);')
s = s.replace('override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); if (intent.action == ACTION_PLAY_PAUSE) NotificationBus.toggle() }', 'override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent); AuthRecoveryBus.url = intent.dataString; if (intent.action == ACTION_PLAY_PAUSE) NotificationBus.toggle() }')
needle = 'class MainActivity : ComponentActivity {'
methods = '''private object AuthRecoveryRepository {
    private val client = OkHttpClient()
    private val jsonType = "application/json".toMediaType()
    suspend fun send(email: String): Result<String> = withContext(Dispatchers.IO) {
        val base = BuildConfig.SUPABASE_URL.trimEnd('/')
        val key = BuildConfig.SUPABASE_ANON_KEY
        val clean = normalizeEmail(email)
        if (base.isBlank() || key.isBlank()) return@withContext Result.failure(Exception("SUPABASE_CONFIG"))
        if (clean.isBlank()) return@withContext Result.failure(Exception("ایمیل را وارد کن."))
        try {
            val body = JSONObject().put("email", clean).put("redirect_to", "beatnova://auth/recovery").toString().toRequestBody(jsonType)
            val request = Request.Builder().url("$base/auth/v1/recover").post(body).addHeader("apikey", key).addHeader("Content-Type", "application/json").build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    val obj = runCatching { JSONObject(response.body?.string().orEmpty()) }.getOrNull()
                    return@withContext Result.failure(Exception(obj?.optString("msg")?.takeIf { it.isNotBlank() } ?: "AUTH_HTTP_${response.code}"))
                }
                Result.success("لینک بازیابی رمز به ایمیل شما ارسال شد.")
            }
        } catch (e: Exception) { Result.failure(e) }
    }
    suspend fun update(accessToken: String, password: String): Result<String> = withContext(Dispatchers.IO) {
        val base = BuildConfig.SUPABASE_URL.trimEnd('/')
        val key = BuildConfig.SUPABASE_ANON_KEY
        if (base.isBlank() || key.isBlank()) return@withContext Result.failure(Exception("SUPABASE_CONFIG"))
        try {
            val body = JSONObject().put("password", password).toString().toRequestBody(jsonType)
            val request = Request.Builder().url("$base/auth/v1/user").patch(body).addHeader("apikey", key).addHeader("Authorization", "Bearer $accessToken").addHeader("Content-Type", "application/json").build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext Result.failure(Exception("AUTH_HTTP_${response.code}"))
                Result.success("رمز عبور با موفقیت تغییر کرد.")
            }
        } catch (e: Exception) { Result.failure(e) }
    }
}

'''
s = s.replace(needle, methods + needle)
s = s.replace('@Composable private fun BeatNovaApp() {', '@Composable private fun BeatNovaApp() {\n    val recoveryUrl = AuthRecoveryBus.url')
s = s.replace('if (showAuth) { AuthScreen(onBack = { showAuth = false }) } else Column', 'if (recoveryUrl?.startsWith("beatnova://auth/recovery") == true) { PasswordRecoveryScreen(recoveryUrl = recoveryUrl, onDone = { AuthRecoveryBus.url = null }) } else if (showAuth) { AuthScreen(onBack = { showAuth = false }) } else Column')
start = s.index('@Composable private fun AuthScreen(onBack: () -> Unit) {')
end = s.index('@Composable private fun HomeScreen', start)
auth = '''@Composable private fun AuthScreen(onBack: () -> Unit) {
    val scope = rememberCoroutineScope(); var register by remember { mutableStateOf(true) }; var email by remember { mutableStateOf("") }; var password by remember { mutableStateOf("") }; var busy by remember { mutableStateOf(false) }; var message by remember { mutableStateOf<String?>(null) }; var success by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().background(Bg).padding(22.dp)) {
        IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "بازگشت", tint = White) }
        Spacer(Modifier.height(10.dp)); Text(if (register) "ثبت‌نام در BeatNova" else "ورود به BeatNova", color = White, fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Text("حساب خودت را بساز و کتابخانه‌ات را شخصی‌تر کن", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp, bottom = 22.dp))
        OutlinedTextField(value = email, onValueChange = { email = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("ایمیل") }, leadingIcon = { Icon(Icons.Default.Email, null) }, shape = RoundedCornerShape(16.dp))
        Spacer(Modifier.height(12.dp)); OutlinedTextField(value = password, onValueChange = { password = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("رمز عبور") }, leadingIcon = { Icon(Icons.Default.Lock, null) }, visualTransformation = PasswordVisualTransformation(), shape = RoundedCornerShape(16.dp))
        if (!register) { Spacer(Modifier.height(8.dp)); TextButton(onClick = { val clean = normalizeEmail(email); if (clean.isBlank()) { message = "ایمیل را وارد کن."; return@TextButton }; busy = true; message = null; success = false; scope.launch { AuthRecoveryRepository.send(clean).onSuccess { message = it; success = true }.onFailure { message = it.message ?: "خطا در ارسال لینک بازیابی" }; busy = false } }) { Text("فراموشی رمز عبور؟", color = Purple) } }
        Spacer(Modifier.height(10.dp)); Button(onClick = { val cleanEmail = normalizeEmail(email); if (cleanEmail.isBlank() || password.length < 6) { message = if (cleanEmail.isBlank()) "ایمیل را وارد کن." else "رمز عبور باید حداقل ۶ کاراکتر باشد."; return@Button }; email = cleanEmail; busy = true; message = null; success = false; scope.launch { val result = if (register) AuthRepository.signUp(cleanEmail, password) else AuthRepository.signIn(cleanEmail, password); busy = false; result.onSuccess { message = it; success = true }.onFailure { message = it.message ?: "خطا در احراز هویت" } } }, enabled = !busy, modifier = Modifier.fillMaxWidth().height(52.dp), shape = RoundedCornerShape(16.dp)) { if (busy) CircularProgressIndicator(modifier = Modifier.size(22.dp), color = White) else Text(if (register) "ثبت‌نام" else "ورود", fontWeight = FontWeight.Bold) }
        message?.let { Spacer(Modifier.height(14.dp)); Text(it, color = if (success) Purple else Pink, fontSize = 13.sp) }
        Spacer(Modifier.height(20.dp)); Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) { Text(if (register) "قبلاً حساب داری؟ " else "حساب نداری؟ ", color = Muted); Text(if (register) "ورود" else "ثبت‌نام", color = Purple, fontWeight = FontWeight.Bold, modifier = Modifier.clickable { register = !register; message = null; success = false }) }
    }
}

@Composable private fun PasswordRecoveryScreen(recoveryUrl: String, onDone: () -> Unit) {
    val token = remember(recoveryUrl) { Uri.parse(recoveryUrl).fragment?.split("&")?.mapNotNull { part -> val kv = part.split("=", limit = 2); if (kv.size == 2) kv[0] to Uri.decode(kv[1]) else null }?.toMap()?.get("access_token").orEmpty() }
    val scope = rememberCoroutineScope(); var password by remember { mutableStateOf("") }; var confirm by remember { mutableStateOf("") }; var busy by remember { mutableStateOf(false) }; var message by remember { mutableStateOf<String?>(null) }; var success by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().background(Bg).padding(22.dp)) {
        Text("تغییر رمز عبور", color = White, fontSize = 28.sp, fontWeight = FontWeight.ExtraBold); Spacer(Modifier.height(8.dp)); Text("رمز جدید را برای حساب BeatNova انتخاب کن.", color = Muted)
        Spacer(Modifier.height(22.dp)); OutlinedTextField(value = password, onValueChange = { password = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("رمز جدید") }, visualTransformation = PasswordVisualTransformation())
        Spacer(Modifier.height(12.dp)); OutlinedTextField(value = confirm, onValueChange = { confirm = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("تکرار رمز جدید") }, visualTransformation = PasswordVisualTransformation())
        Spacer(Modifier.height(18.dp)); Button(onClick = { when { token.isBlank() -> message = "لینک بازیابی نامعتبر یا منقضی شده است."; password.length < 6 -> message = "رمز عبور باید حداقل ۶ کاراکتر باشد."; password != confirm -> message = "تکرار رمز با رمز جدید یکسان نیست."; else -> { busy = true; message = null; scope.launch { AuthRecoveryRepository.update(token, password).onSuccess { message = it; success = true }.onFailure { message = it.message ?: "تغییر رمز انجام نشد" }; busy = false } } } }, enabled = !busy, modifier = Modifier.fillMaxWidth().height(52.dp)) { if (busy) CircularProgressIndicator(modifier = Modifier.size(22.dp), color = White) else Text("ذخیره رمز جدید") }
        message?.let { Spacer(Modifier.height(14.dp)); Text(it, color = if (success) Purple else Pink) }
        if (success) { Spacer(Modifier.height(14.dp)); TextButton(onClick = onDone) { Text("بازگشت به ورود", color = Purple) } }
    }
}

'''
s = s[:start] + auth + s[end:]
src.write_text(s)

manifest = Path('app/src/main/AndroidManifest.xml')
m = manifest.read_text()
needle = '''            <intent-filter>\n                <action android:name="android.intent.action.MAIN" />\n                <category android:name="android.intent.category.LAUNCHER" />\n            </intent-filter>'''
replacement = needle + '''\n            <intent-filter>\n                <action android:name="android.intent.action.VIEW" />\n                <category android:name="android.intent.category.DEFAULT" />\n                <category android:name="android.intent.category.BROWSABLE" />\n                <data android:scheme="beatnova" android:host="auth" android:pathPrefix="/recovery" />\n            </intent-filter>'''
if 'android:scheme="beatnova"' not in m:
    m = m.replace(needle, replacement)
manifest.write_text(m)
