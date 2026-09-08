package com.srnyndrs.android.briefly.domain.model.content

data class PostPagingResult(
    val page: Int,
    val count: Int,
    val items: List<Post>,
)
