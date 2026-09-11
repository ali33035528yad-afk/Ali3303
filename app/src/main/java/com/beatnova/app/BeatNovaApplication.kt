package com.beatnova.app

import android.app.Application

class BeatNovaApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        AdManager.initialize(this)
    }
}
