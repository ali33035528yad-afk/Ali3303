package com.beatnova.app

import android.view.ViewGroup
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.adivery.sdk.AdiveryAdListener
import com.adivery.sdk.AdiveryBannerAdView
import com.adivery.sdk.BannerSize

@Composable
fun BeatNovaAdiveryBanner(
    placementId: String,
    modifier: Modifier = Modifier,
    onAdEvent: (String) -> Unit = {},
) {
    key(placementId) {
        val currentOnAdEvent = rememberUpdatedState(onAdEvent)
        AndroidView(
            modifier = modifier,
            factory = { context ->
                AdiveryBannerAdView(context).apply {
                    layoutParams = ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                    )
                    setPlacementId(placementId)
                    setBannerSize(BannerSize.BANNER)
                    setBannerAdListener(object : AdiveryAdListener() {
                        override fun onAdLoaded() = currentOnAdEvent.value("onAdLoaded")
                        override fun onAdShown() = currentOnAdEvent.value("onAdShown")
                        override fun onAdClicked() = currentOnAdEvent.value("onAdClicked")
                        override fun onError(reason: String) = currentOnAdEvent.value("onError: $reason")
                    })
                    loadAd()
                }
            },
        )
    }
}
