package com.srnyndrs.android.briefly.domain.model.content

import androidx.paging.PagingData
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

data class HomeFeedMetadata(
    val headlines: List<Post>,
    val categories: List<String>,
)

data class HomeFeed(
    val posts: Flow<PagingData<Post>>,
    val metadata: StateFlow<HomeFeedMetadata?>,
)
