package com.srnyndrs.android.briefly.domain.model.content.post

data class PostPagingResult(
    val page: Int,
    val pageCount: Int,
    val items: List<Post>,
)
