package com.srnyndrs.android.briefly.domain.model.content

data class FeedSourceResultItem(
    val url: String,
    val title: String,
    val favicon: String? = null,
    val description: String? = null
)
