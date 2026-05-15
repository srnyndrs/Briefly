package com.srnyndrs.android.briefly.ui.screen.content.screen.article_details

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.KeyboardArrowLeft
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonColors
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ArticleDetailsScreen(
    modifier: Modifier = Modifier,
    state: UiState<ArticleDetails>,
) {

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier.then(modifier)
            .verticalScroll(scrollState),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        when(state) {
            is UiState.Success -> {
                val article = state.data

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Header Overlay
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.TopCenter
                    ) {
                        // Image
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .aspectRatio(16f / 9)
                                .background(
                                    MaterialTheme.colorScheme.onSurface.copy(0.4f)
                                ),
                            contentAlignment = Alignment.Center,
                        ) {
                            article.imageUrl?.let { url ->
                                RemoteImageContainer(
                                    modifier = Modifier.fillMaxSize(),
                                    imageUrl = url,
                                    contentScale = ContentScale.Crop
                                )
                            } ?:
                                Image(
                                    imageVector = Icons.Default.Info,
                                    contentDescription = null
                                )
                        }
                        // TODO: reposition top bar
                        // Bar
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            // Return button
                            IconButton(
                                modifier = Modifier
                                    .size(48.dp)
                                    .clip(RoundedCornerShape(5.dp)),
                                colors = IconButtonColors(
                                    containerColor = MaterialTheme.colorScheme.onSurface.copy(0.4f),
                                    contentColor = MaterialTheme.colorScheme.surface,
                                    disabledContainerColor = MaterialTheme.colorScheme.onSurface.copy(0.4f),
                                    disabledContentColor = MaterialTheme.colorScheme.onSurface,
                                ),
                                onClick = {
                                    // TODO: return previous page
                                }
                            ) {
                                Icon(
                                    modifier = Modifier.size(24.dp),
                                    imageVector = Icons.Default.KeyboardArrowLeft,
                                    contentDescription = null
                                )
                            }
                            // Source
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(5.dp))
                                    .background(
                                        MaterialTheme.colorScheme.onSurface.copy(0.05f)
                                    )
                                    .padding(vertical = 3.dp, horizontal = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {

                                Text(
                                    text = "Source", // TODO
                                    color = MaterialTheme.colorScheme.onSurface,
                                    style = MaterialTheme.typography.bodyMedium,
                                    textDecoration = TextDecoration.Underline
                                )
                            }
                            // External button
                            IconButton(
                                modifier = Modifier
                                    .size(48.dp)
                                    .clip(RoundedCornerShape(5.dp)),
                                colors = IconButtonColors(
                                    containerColor = MaterialTheme.colorScheme.onSurface.copy(0.4f),
                                    contentColor = MaterialTheme.colorScheme.surface,
                                    disabledContainerColor = MaterialTheme.colorScheme.onSurface.copy(0.4f),
                                    disabledContentColor = MaterialTheme.colorScheme.onSurface,
                                ),
                                onClick = {
                                    // TODO: external link
                                }
                            ) {
                                Icon(
                                    modifier = Modifier.size(24.dp),
                                    imageVector = Icons.Default.KeyboardArrowUp,
                                    contentDescription = null
                                )
                            }
                        }
                    }
                    // Content
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 6.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        // Title
                        Text(
                            modifier = Modifier.fillMaxWidth(),
                            text = article.title,
                            style = MaterialTheme.typography.headlineMedium,
                            textAlign = TextAlign.Start,
                            minLines = 1,
                        )
                        // Divider
                        HorizontalDivider(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            thickness = 2.dp,
                            color = MaterialTheme.colorScheme.onSurface,
                        )
                        // Description
                        Text(
                            modifier = Modifier.fillMaxWidth(0.98f),
                            text = article.content,
                            style = MaterialTheme.typography.bodyLarge,
                            lineHeight = 26.sp,
                            textAlign = TextAlign.Justify,
                        )
                    }
                }
            }
            is UiState.Error -> {
                // TODO: handle error state
                Text(
                    modifier = Modifier.fillMaxWidth(),
                    text = state.message,
                    textAlign = TextAlign.Center,
                    color = MaterialTheme.colorScheme.error,
                )
            }
            is UiState.Loading -> {
                LinearProgressIndicator()
            }
            else -> {
                // Show nothing on IDLE
            }
        }
    }
}

@PreviewLightDark
@Composable
fun ArticleDetailsScreenPreview() {
    BrieflyTheme {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            /*topBar = {
                TopAppBar(
                    onMenuSelect = {}
                ) { }
            }*/
        ) { paddingValues ->
            ArticleDetailsScreen(
                modifier = Modifier.padding(paddingValues),
                state = UiState.Idle
            )
        }
    }
}