package com.srnyndrs.android.briefly.ui.common

import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.ui.util.shimmer

@Composable
fun ShimmerItem(
    modifier: Modifier = Modifier,
    isLoading: Boolean = false,
    cornerRadius: Dp = 0.dp,
    contentAlignment: Alignment = Alignment.TopStart,
    content: @Composable () -> Unit
) {
    Box(
        modifier = Modifier
            .then(modifier)
            .shimmer(isLoading, cornerRadius),
        contentAlignment = contentAlignment
    ) {
        if (!isLoading) content()
    }
}
