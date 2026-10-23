package com.srnyndrs.android.briefly.ui.screen.main.components.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
class PostPreviewProvider : PreviewParameterProvider<Post> {
    override val values = sequenceOf(
        Post(
            id = "battery-research",
            title = "Researchers improve recovery of materials from used batteries",
            description = "A new process recovers more reusable material while consuming less energy.",
            sourceTitle = "Daily Science",
            categories = listOf(Category.SCIENCE, Category.TECHNOLOGY),
            publishedAt = Instant.parse(input = "2026-10-19T08:00:00Z"),
        ),
        Post(
            id = "library-hours",
            title = "Local libraries extend their weekend opening hours",
            description = "The new schedule gives residents more time to use study spaces and borrow books.",
            sourceTitle = "City Journal",
            categories = emptyList(),
            imageUrl = "https://example.com/library.jpg",
            publishedAt = Instant.parse(input = "2026-10-18T12:00:00Z"),
        ),
    )
}
