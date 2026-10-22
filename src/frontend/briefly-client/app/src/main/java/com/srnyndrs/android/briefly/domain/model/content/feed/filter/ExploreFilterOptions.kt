package com.srnyndrs.android.briefly.domain.model.content.feed.filter

data class ExploreFilterOptions(
    val categories: List<String> = emptyList(),
    val languages: List<String> = emptyList(),
    val authors: List<String> = emptyList(),
    val keywords: List<String> = emptyList(),
    val sources: List<FilterSource> = emptyList(),
)
