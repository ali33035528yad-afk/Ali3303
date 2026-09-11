@file:OptIn(androidx.media3.common.util.UnstableApi::class)

package com.beatnova.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.datasource.cache.CacheDataSource
import androidx.media3.datasource.cache.NoOpCacheEvictor
import androidx.media3.datasource.cache.SimpleCache
import androidx.media3.database.StandaloneDatabaseProvider
import androidx.media3.exoplayer.offline.Download
import androidx.media3.exoplayer.offline.DownloadManager
import androidx.media3.exoplayer.offline.DownloadNotificationHelper
import androidx.media3.exoplayer.offline.DownloadRequest
import androidx.media3.exoplayer.offline.DownloadService
import androidx.media3.exoplayer.offline.DownloadIndex
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import androidx.media3.exoplayer.source.MediaSource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File
import java.util.concurrent.Executors

private const val DOWNLOAD_CHANNEL_ID = "beatnova_downloads"
private const val DOWNLOAD_NOTIFICATION_ID = 2002

object BeatNovaDownloads {
    private var cache: SimpleCache? = null
    private var manager: DownloadManager? = null
    private var downloadIndex: DownloadIndex? = null
    private var upstreamFactory: DefaultHttpDataSource.Factory? = null
    private val executor = Executors.newFixedThreadPool(2)
    private val _states = MutableStateFlow<Map<String, Download>>(emptyMap())
    val states: StateFlow<Map<String, Download>> = _states.asStateFlow()

    @Synchronized
    fun initialize(context: Context) {
        if (manager != null) return
        val application = context.applicationContext
        createDownloadChannel(application)
        val db = StandaloneDatabaseProvider(application)
        val downloadDir = File(application.filesDir, "beatnova_offline")
        val downloadCache = SimpleCache(downloadDir, NoOpCacheEvictor(), db)
        val upstream = DefaultHttpDataSource.Factory()
        cache = downloadCache
        upstreamFactory = upstream
        manager = DownloadManager(application, db, downloadCache, upstream, executor)
        downloadIndex = manager!!.downloadIndex
        manager!!.addListener(object : DownloadManager.Listener {
            override fun onDownloadChanged(downloadManager: DownloadManager, download: Download, finalException: Exception?) {
                updateState(download)
            }
            override fun onDownloadRemoved(downloadManager: DownloadManager, download: Download) {
                _states.value = _states.value - download.request.id
            }
            override fun onInitialized(downloadManager: DownloadManager) {
                refreshPersistedStates()
            }
        })
        refreshPersistedStates()
    }

    private fun createDownloadChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= 26) {
            context.getSystemService(NotificationManager::class.java).createNotificationChannel(
                NotificationChannel(DOWNLOAD_CHANNEL_ID, "دانلود آهنگ‌ها", NotificationManager.IMPORTANCE_LOW).apply {
                    description = "پیشرفت دانلود آهنگ‌های BeatNova"
                }
            )
        }
    }

    private fun ensure(context: Context) {
        if (manager == null) initialize(context)
    }

    fun add(context: Context, song: Song) {
        ensure(context)
        val request = DownloadRequest.Builder(song.id, Uri.parse(song.audioUrl))
            .setMimeType("audio/mpeg")
            .setData(song.title.toByteArray(Charsets.UTF_8))
            .build()
        DownloadService.sendAddDownload(context.applicationContext, BeatNovaDownloadService::class.java, request, true)
    }

    fun remove(context: Context, songId: String) {
        ensure(context)
        DownloadService.sendRemoveDownload(context.applicationContext, BeatNovaDownloadService::class.java, songId, true)
    }

    fun toggle(context: Context, song: Song) {
        val state = _states.value[song.id]?.state
        if (state == Download.STATE_COMPLETED || state == Download.STATE_DOWNLOADING || state == Download.STATE_QUEUED || state == Download.STATE_STOPPED) {
            remove(context, song.id)
        } else {
            add(context, song)
        }
    }

    fun mediaSourceFactory(context: Context): MediaSource.Factory {
        ensure(context)
        val cacheDataSource = CacheDataSource.Factory()
            .setCache(cache!!)
            .setUpstreamDataSourceFactory(upstreamFactory!!)
        return DefaultMediaSourceFactory(cacheDataSource)
    }

    private fun updateState(download: Download) {
        _states.value = _states.value + (download.request.id to download)
    }

    fun refreshPersistedStates() {
        val index = downloadIndex ?: return
        executor.execute {
            runCatching {
                val cursor = index.getDownloads(intArrayOf())
                val result = mutableMapOf<String, Download>()
                while (cursor.moveToNext()) {
                    val download = cursor.download
                    result[download.request.id] = download
                }
                cursor.close()
                android.os.Handler(android.os.Looper.getMainLooper()).post { _states.value = result }
            }
        }
    }

    fun getManager(context: Context): DownloadManager {
        ensure(context)
        return manager!!
    }
}

class BeatNovaDownloadService : DownloadService(DOWNLOAD_NOTIFICATION_ID, 1000L) {
    override fun getDownloadManager(): DownloadManager = BeatNovaDownloads.getManager(this)

    override fun getScheduler(): androidx.media3.exoplayer.scheduler.Scheduler? = null

    override fun getForegroundNotification(
        downloads: MutableList<Download>,
        notMetRequirements: Int
    ): android.app.Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(this, 2003, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        return DownloadNotificationHelper(this, DOWNLOAD_CHANNEL_ID).buildProgressNotification(
            this, R.drawable.ic_beatnova, pendingIntent, "در حال دانلود آهنگ", downloads, notMetRequirements
        )
    }
}

@Composable
fun BeatNovaDownloadButton(song: Song) {
    val context = LocalContext.current
    val states by BeatNovaDownloads.states.collectAsState()
    val state = states[song.id]?.state
    val icon = when (state) {
        Download.STATE_COMPLETED -> Icons.Default.CheckCircle
        Download.STATE_DOWNLOADING, Download.STATE_QUEUED -> Icons.Default.Downloading
        Download.STATE_FAILED -> Icons.Default.ErrorOutline
        else -> Icons.Default.Download
    }
    val tint = when (state) {
        Download.STATE_COMPLETED -> Color(0xFF7CFFB2)
        Download.STATE_FAILED -> Color(0xFFFF6B8A)
        Download.STATE_DOWNLOADING, Download.STATE_QUEUED -> Color(0xFFFFC857)
        else -> Color(0xFF9699A9)
    }
    IconButton(onClick = { BeatNovaDownloads.toggle(context, song) }) {
        Icon(icon, contentDescription = if (state == Download.STATE_COMPLETED) "حذف دانلود" else "دانلود آهنگ", tint = tint)
    }
}

@Composable
fun BeatNovaSongIcon(song: Song, selected: Boolean) {
    val icons = listOf<ImageVector>(
        Icons.Default.MusicNote,
        Icons.Default.Album,
        Icons.Default.GraphicEq,
        Icons.Default.Headphones,
        Icons.Default.QueueMusic,
        Icons.Default.LibraryMusic,
        Icons.Default.Radio
    )
    val index = kotlin.math.abs(song.title.hashCode() + song.artist.hashCode()) % icons.size
    Icon(if (selected) Icons.Default.GraphicEq else icons[index], null, tint = Color.White, modifier = Modifier.size(25.dp))
}

@Composable
fun DownloadsScreen(songs: List<Song>, current: Song?, playing: Boolean, play: (Song) -> Unit) {
    val context = LocalContext.current
    val states by BeatNovaDownloads.states.collectAsState()
    val completed = songs.filter { states[it.id]?.state == Download.STATE_COMPLETED }
    val active = songs.filter {
        when (states[it.id]?.state) {
            Download.STATE_DOWNLOADING, Download.STATE_QUEUED, Download.STATE_FAILED, Download.STATE_STOPPED -> true
            else -> false
        }
    }
    Column(Modifier.fillMaxSize().background(Color(0xFF08090F)).padding(top = 22.dp)) {
        Text("کتابخانه دانلود", color = Color.White, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.padding(horizontal = 20.dp))
        Text("آهنگ‌های ذخیره‌شده برای پخش آفلاین", color = Color(0xFF9699A9), fontSize = 13.sp, modifier = Modifier.padding(horizontal = 20.dp, vertical = 5.dp))
        if (active.isNotEmpty()) {
            Text("در حال دانلود", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp))
            active.forEach { song ->
                DownloadStatusRow(song, states[song.id], onRemove = { BeatNovaDownloads.remove(context, song.id) })
            }
        }
        Text("دانلود شده‌ها • ${completed.size}", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp))
        LazyColumn(contentPadding = PaddingValues(bottom = 24.dp)) {
            if (completed.isEmpty()) {
                item {
                    Column(Modifier.fillMaxWidth().padding(24.dp).clip(RoundedCornerShape(24.dp)).background(Color(0xFF12141D)).padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.CloudDownload, null, tint = Color(0xFFC65CFF), modifier = Modifier.size(44.dp))
                        Spacer(Modifier.height(12.dp))
                        Text("هنوز آهنگی دانلود نشده", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Text("از آیکون دانلود کنار هر آهنگ استفاده کن.", color = Color(0xFF9699A9), fontSize = 12.sp, modifier = Modifier.padding(top = 6.dp))
                    }
                }
            } else {
                items(completed, key = { it.id }) { song ->
                    OfflineSongRow(song, current?.id == song.id, playing && current?.id == song.id, play, onRemove = { BeatNovaDownloads.remove(context, song.id) })
                }
            }
        }
    }
}

@Composable
private fun DownloadStatusRow(song: Song, download: Download?, onRemove: () -> Unit) {
    val percent = download?.percentDownloaded?.takeIf { it >= 0f } ?: 0f
    Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 4.dp).clip(RoundedCornerShape(18.dp)).background(Color(0xFF12141D)).padding(11.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(50.dp).clip(RoundedCornerShape(15.dp)).background(Brush.linearGradient(listOf(Color(0xFF617CFF), Color(0xFFC65CFF)))), contentAlignment = Alignment.Center) { BeatNovaSongIcon(song, false) }
        Spacer(Modifier.width(11.dp))
        Column(Modifier.weight(1f)) {
            Text(song.title, color = Color.White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(if (download?.state == Download.STATE_FAILED) "دانلود ناموفق" else "${percent.toInt()}٪", color = if (download?.state == Download.STATE_FAILED) Color(0xFFFF6B8A) else Color(0xFF9699A9), fontSize = 12.sp)
            LinearProgressIndicator(progress = { percent / 100f }, modifier = Modifier.fillMaxWidth().padding(top = 5.dp))
        }
        IconButton(onClick = onRemove) { Icon(Icons.Default.Close, "لغو دانلود", tint = Color(0xFF9699A9)) }
    }
}

@Composable
private fun OfflineSongRow(song: Song, selected: Boolean, playing: Boolean, play: (Song) -> Unit, onRemove: () -> Unit) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 5.dp).clip(RoundedCornerShape(18.dp)).background(if (selected) Color(0xFF241A35) else Color(0xFF12141D)).clickable { play(song) }.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(54.dp).clip(RoundedCornerShape(16.dp)).background(Brush.linearGradient(listOf(Color(0xFFFF3E9D), Color(0xFFC65CFF)))), contentAlignment = Alignment.Center) { BeatNovaSongIcon(song, selected) }
        Spacer(Modifier.width(11.dp))
        Column(Modifier.weight(1f)) {
            Text(song.title, color = Color.White, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(song.artist, color = Color(0xFF9699A9), fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text("✓ آماده پخش آفلاین", color = Color(0xFF7CFFB2), fontSize = 10.sp, modifier = Modifier.padding(top = 2.dp))
        }
        IconButton(onClick = { play(song) }) { Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, null, tint = Color.White) }
        IconButton(onClick = onRemove) { Icon(Icons.Default.DeleteOutline, "حذف از دانلودها", tint = Color(0xFF9699A9)) }
    }
}
