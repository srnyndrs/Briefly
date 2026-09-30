package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.PostDetails
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.PostDetailsState
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
class PostDetailsStateProvider : PreviewParameterProvider<PostDetailsState> {
    private val ready = PostDetailsState(
        details = UiState.Success(
            data = PostDetails(
                id = "article",
                title = "New battery recycling research opens the way to cleaner manufacturing",
                sourceTitle = "Example News",
                sourceId = "source",
                categories = listOf(Category.SCIENCE, Category.TECHNOLOGY, Category.ENVIRONMENT),
                url = "https://example.com/battery-recycling",
                publishedAt = Instant.parse(input = "2026-10-19T12:00:00Z"),
                content = "Researchers have developed a process that recovers more material from used batteries.\n\n" +
                    "The team will test the process at a larger scale over the coming months.",
                keywords = listOf("batteries", "recycling", "research"),
                author = "Alex Taylor",
            ),
        ),
        mutedKeywords = UiState.Success(data = emptySet()),
    )

    override val values = sequenceOf(
        PostDetailsState(details = UiState.Loading),
        PostDetailsState(details = UiState.Error(message = "Preview failure")),
        ready,
        ready.copy(mutedKeywords = UiState.Loading),
        ready.copy(mutedKeywords = UiState.Error(message = "Preview failure")),
        ready.copy(mutingKeyword = "batteries"),
        ready.copy(failedKeyword = "batteries"),
        ready.copy(mutedKeywords = UiState.Success(data = setOf("batteries"))),
    )
}
