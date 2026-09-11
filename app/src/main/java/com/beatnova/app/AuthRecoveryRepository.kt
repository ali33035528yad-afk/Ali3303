package com.beatnova.app

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

internal object AuthRecoveryRepository {
    private val client = OkHttpClient()
    private val jsonType = "application/json".toMediaType()

    suspend fun send(email: String): Result<String> = withContext(Dispatchers.IO) {
        val base = BuildConfig.SUPABASE_URL.trimEnd('/')
        val key = BuildConfig.SUPABASE_ANON_KEY
        val clean = normalizeEmail(email)
        if (base.isBlank() || key.isBlank()) return@withContext Result.failure(Exception("SUPABASE_CONFIG"))
        if (clean.isBlank()) return@withContext Result.failure(Exception("ایمیل را وارد کن."))
        try {
            val body = JSONObject()
                .put("email", clean)
                .put("redirect_to", "beatnova://auth/recovery")
                .toString()
                .toRequestBody(jsonType)
            val request = Request.Builder()
                .url("$base/auth/v1/recover")
                .post(body)
                .addHeader("apikey", key)
                .addHeader("Content-Type", "application/json")
                .build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    val obj = runCatching { JSONObject(response.body?.string().orEmpty()) }.getOrNull()
                    return@withContext Result.failure(Exception(
                        obj?.optString("msg")?.takeIf { it.isNotBlank() } ?: "AUTH_HTTP_${response.code}"
                    ))
                }
                Result.success("لینک بازیابی رمز به ایمیل شما ارسال شد.")
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun update(accessToken: String, password: String): Result<String> = withContext(Dispatchers.IO) {
        val base = BuildConfig.SUPABASE_URL.trimEnd('/')
        val key = BuildConfig.SUPABASE_ANON_KEY
        if (base.isBlank() || key.isBlank()) return@withContext Result.failure(Exception("SUPABASE_CONFIG"))
        try {
            val body = JSONObject().put("password", password).toString().toRequestBody(jsonType)
            val request = Request.Builder()
                .url("$base/auth/v1/user")
                .patch(body)
                .addHeader("apikey", key)
                .addHeader("Authorization", "Bearer $accessToken")
                .addHeader("Content-Type", "application/json")
                .build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext Result.failure(Exception("AUTH_HTTP_${response.code}"))
                Result.success("رمز عبور با موفقیت تغییر کرد.")
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
