package com.srnyndrs.android.briefly.ui.components

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import com.srnyndrs.android.briefly.ui.util.LocalShimmerProgress
import com.srnyndrs.android.briefly.ui.util.rememberShimmerProgress

@Composable
fun ShimmerGroup(content: @Composable () -> Unit) {
    val progress = LocalShimmerProgress.current ?: rememberShimmerProgress()
    CompositionLocalProvider(LocalShimmerProgress provides progress) {
        content()
    }
}
