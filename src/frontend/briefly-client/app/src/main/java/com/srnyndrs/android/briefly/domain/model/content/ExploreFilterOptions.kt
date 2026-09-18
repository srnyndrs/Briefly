package com.srnyndrs.android.briefly.domain.model.content

import androidx.paging.PagingData
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

data class FilterSource(
    val id: String,
    val title: String,
)

data class ExploreFilterOptions(
    val categories: List<String> = emptyList(),
    val languages: List<String> = emptyList(),
    val sources: List<FilterSource> = emptyList(),
)

data class ExploreFeed(
    val posts: Flow<PagingData<Post>>,
    val metadata: StateFlow<ExploreFilterOptions?>,
)

