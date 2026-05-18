package com.srnyndrs.android.briefly.ui.screen.content.screen.article_details

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.BottomSheetScaffold
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SheetValue
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberBottomSheetScaffoldState
import androidx.compose.material3.rememberStandardBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.ui.common.RemoteImageContainer
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.article_details.preview.ArticleDetailsStateProvider
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.toFormattedDateString
import com.srnyndrs.android.briefly.ui.util.toRelativeArticleTime
import kotlinx.coroutines.launch
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalMaterial3Api::class, ExperimentalTime::class)
@Composable
fun ContentDetailsScreen(
    modifier: Modifier = Modifier,
    isLoading: Boolean = false,
    article: ArticleDetails?,
    onEvent: () -> Unit
) {

    val bottomSheetState = rememberStandardBottomSheetState(
        initialValue = SheetValue.PartiallyExpanded,
        skipHiddenState = true
    )
    val sheetState = rememberBottomSheetScaffoldState(
        bottomSheetState = bottomSheetState
    )
    val scrollState = rememberScrollState()

    BottomSheetScaffold(
            modifier = Modifier.then(modifier),
            scaffoldState = sheetState,
            sheetDragHandle = {},
            sheetContent = {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(scrollState)
                        .padding(top = 36.dp, start = 8.dp, end = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    // Category
                    Box(
                        modifier = Modifier
                            .wrapContentWidth()
                            .defaultMinSize(minHeight = 36.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(MaterialTheme.colorScheme.onSurface.copy(0.2f))
                            .padding(horizontal = 8.dp, vertical = 2.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = article?.category ?: "",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurface,
                            fontWeight = FontWeight.Black
                        )
                    }
                    // Title
                    Text(
                        modifier = Modifier.fillMaxWidth(),
                        text = article?.title ?: "",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Black,
                        lineHeight = 28.sp,
                        textAlign = TextAlign.Start,
                        minLines = 1,
                    )
                    //
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = article?.source ?: "",
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Box(
                            modifier = Modifier
                                .size(4.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.onSurface),
                        )
                        Text(
                            text = article?.publishedAt?.toRelativeArticleTime() ?: "",
                            style = MaterialTheme.typography.bodyLarge
                        )
                    }
                    HorizontalDivider(
                        modifier = Modifier.padding(bottom = 12.dp, top = 6.dp),
                        thickness = 1.dp,
                        color = MaterialTheme.colorScheme.onSurface.copy(0.7f)
                    )
                    // Content
                    Text(
                        modifier = Modifier.fillMaxWidth(),
                        text = article?.content ?: "",
                        fontSize = 18.sp,
                        lineHeight = 26.sp,
                        textAlign = TextAlign.Justify
                    )
                }
        },
        sheetSwipeEnabled = true,
        sheetPeekHeight = 564.dp,
        sheetShape = if (bottomSheetState.currentValue == SheetValue.Expanded) {
            RectangleShape
        } else {
            RoundedCornerShape(
                topStart = 24.dp,
                topEnd = 24.dp
            )
        },
        sheetShadowElevation = 24.dp,
        contentColor = MaterialTheme.colorScheme.onSurface,
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(paddingValues),
            contentAlignment = Alignment.BottomCenter
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .requiredHeight(356.dp)
            ) {
                RemoteImageContainer(
                    modifier = Modifier.fillMaxWidth(),
                    imageUrl = article?.imageUrl ?: "",
                    contentScale = ContentScale.Crop
                )
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(0.12f))
                )
            }
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .wrapContentHeight()
                    .padding(vertical = 16.dp, horizontal = 6.dp),
                horizontalAlignment = Alignment.Start,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {

            }
        }
    }
}

@PreviewLightDark
@Composable
fun ContentDetailsScreenPreview(
    @PreviewParameter(ArticleDetailsStateProvider::class) state: ArticleDetailsState
) {
    BrieflyTheme {
        Surface {
            ContentDetailsScreen(
                modifier = Modifier.fillMaxSize(),
                article = (state.details as UiState.Success).data
            ) { }
        }
    }
}
