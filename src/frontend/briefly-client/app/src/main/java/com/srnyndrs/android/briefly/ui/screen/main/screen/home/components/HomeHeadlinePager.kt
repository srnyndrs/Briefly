package com.srnyndrs.android.briefly.ui.screen.main.screen.home.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.ui.components.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.components.ShimmerItem
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.HomeState
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.preview.HomeStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.flow.Flow

@Composable
fun HomeHeadlinePager(
    modifier: Modifier = Modifier,
    headlines: List<Post>,
    onHeadlineSelected: (Post) -> Unit,
) {

    val pagerState = rememberPagerState { headlines.size }

    Column(
        modifier = Modifier.then(modifier)
    ) {
        HorizontalPager(
            modifier = Modifier
                .fillMaxWidth()
                .requiredHeight(356.dp),
            state = pagerState,
            pageSpacing = 12.dp,
        ) { page ->

            val article = headlines[page]

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .clickable { onHeadlineSelected(article) },
                verticalArrangement = Arrangement.Top,
            ) {
                ShimmerItem(
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(16f / 9)
                        .padding(bottom = 12.dp)
                        .background(
                            MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
                        )
                        .border(
                            width = 1.dp,
                            color = MaterialTheme.colorScheme.onSurface,
                            shape = RectangleShape,
                        ),
                    isLoading = false,
                    contentAlignment = Alignment.BottomCenter,
                ) {
                    article.imageUrl?.let { imageUrl ->
                        RemoteImageContainer(
                            modifier = Modifier.fillMaxSize(),
                            imageUrl = imageUrl,
                        )
                    }
                }
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text(
                        modifier = Modifier.fillMaxWidth(),
                        text = article.source.orEmpty(),
                        style = MaterialTheme.typography.labelLarge,
                    )
                    Text(
                        modifier = Modifier.fillMaxWidth(),
                        text = article.title,
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Black,
                        maxLines = 3,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        modifier = Modifier.fillMaxWidth(),
                        text = article.description.orEmpty(),
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
        }

        Row(
            modifier = Modifier
                .padding(vertical = 12.dp)
                .fillMaxWidth()
                .requiredHeight(32.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            repeat(pagerState.pageCount) { page ->
                HorizontalDivider(
                    modifier = Modifier
                        .weight(1f / pagerState.pageCount)
                        .clip(RoundedCornerShape(3.dp)),
                    thickness = if (pagerState.currentPage == page) 3.dp else 1.dp,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
                )
                if (page < pagerState.pageCount - 1) {
                    Spacer(
                        modifier = Modifier.requiredWidth(3.dp)
                    )
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun HomeHeadlinePagerPreview(
    @PreviewParameter(HomeStateProvider::class) state: Pair<HomeState, Flow<PagingData<Post>>>
) {
    BrieflyTheme {
        Surface {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(6.dp)
            ) {
                HomeHeadlinePager(
                    modifier = Modifier.fillMaxWidth(),
                    headlines = state.first.headlines,
                ) {}
            }
        }
    }
}
