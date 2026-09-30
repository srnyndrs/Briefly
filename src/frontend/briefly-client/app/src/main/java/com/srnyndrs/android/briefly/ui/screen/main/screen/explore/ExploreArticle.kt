package com.srnyndrs.android.briefly.ui.screen.main.screen.explore

import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExplorePostFilter
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
data class ExploreArticle(
    val post: Post,
    val filter: ExplorePostFilter,
)
