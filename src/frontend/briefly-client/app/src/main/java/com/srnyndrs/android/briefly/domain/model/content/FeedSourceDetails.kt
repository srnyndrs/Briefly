package com.srnyndrs.android.briefly.domain.model.content

data class FeedSourceDetails(
    val id: String,
    val title: String?,
    val description: String? = null,
    val imageUrl: String? = null,
    val favourite: Boolean = false,
    val subscribed: Boolean = false // NOT YET IMPLEMENTED
    //val lastUpdatedAt: Instant
)
