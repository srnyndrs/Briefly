package com.srnyndrs.android.briefly.data.remote.content.model

data class FeedRequest(
    val page: Int = 1,
    val pageSize: Int = 20,
    val subscribedOnly: Boolean,
    val useProfile: Boolean,
    val query: String? = null,
    val categories: List<String>? = null,
    val languages: List<String>? = null,
    val sourceIds: List<String>? = null,
    val publishedFrom: String? = null,
    val publishedTo: String? = null,
    val sort: String? = null,
)
