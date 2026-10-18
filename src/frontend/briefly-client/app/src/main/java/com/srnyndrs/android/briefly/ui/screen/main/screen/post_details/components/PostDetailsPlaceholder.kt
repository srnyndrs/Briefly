package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.ChevronLeft
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.ShimmerGroup
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun PostDetailsPlaceholder(
    modifier: Modifier = Modifier,
    onBack: () -> Unit,
) {
    ShimmerGroup {
        Box(modifier = modifier) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState()),
            ) {
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .requiredHeight(356.dp),
                    isLoading = true,
                ) {}
                Surface(
                    modifier = Modifier
                        .padding(top = 316.dp)
                        .fillMaxWidth(),
                    shape = RoundedCornerShape(
                        topStart = 24.dp,
                        topEnd = 24.dp,
                    ),
                    shadowElevation = 24.dp,
                ) {
                    Column(
                        modifier = Modifier.padding(
                            top = 22.dp,
                            start = 12.dp,
                            end = 12.dp,
                        ),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(36.dp),
                            isLoading = true,
                            cornerRadius = 8.dp,
                        ) {}
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(48.dp),
                            isLoading = true,
                            cornerRadius = 3.dp,
                        ) {}
                        ShimmerItem(
                            modifier = Modifier
                                .fillMaxWidth()
                                .requiredHeight(26.dp),
                            isLoading = true,
                            cornerRadius = 3.dp,
                        ) {}
                        repeat(5) {
                            ShimmerItem(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .requiredHeight(24.dp),
                                isLoading = true,
                                cornerRadius = 3.dp,
                            ) {}
                        }
                        Spacer(modifier = Modifier.requiredHeight(72.dp))
                    }
                }
            }
            IconButton(
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(12.dp)
                    .size(48.dp)
                    .clip(CircleShape),
                onClick = onBack,
                colors = IconButtonDefaults.iconButtonColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.7f),
                    contentColor = MaterialTheme.colorScheme.onSurface,
                ),
            ) {
                Icon(
                    modifier = Modifier.size(28.dp),
                    imageVector = Heroicons.Outline.ChevronLeft,
                    contentDescription = stringResource(R.string.navigate_back),
                )
            }
        }
    }
}

@PreviewLightDark
@Composable
private fun PostDetailsPlaceholderPreview() {
    BrieflyTheme {
        Surface {
            PostDetailsPlaceholder(
                modifier = Modifier.fillMaxSize(),
                onBack = {},
            )
        }
    }
}
