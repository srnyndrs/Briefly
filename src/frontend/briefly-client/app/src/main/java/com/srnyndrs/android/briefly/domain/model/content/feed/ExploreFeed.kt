package com.srnyndrs.android.briefly.domain.model.content.feed

import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

data class ExploreFeed(
    val posts: Flow<PagingData<Post>>,
    val metadata: StateFlow<ExploreFilterOptions?>,
)
