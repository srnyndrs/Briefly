package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.ArticleDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedResultItemDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceResultItemDto
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem

fun FeedResultItemDto.toDomain(): ArticleItem {
    return ArticleItem(
        id = articleID,
        title = title,
        description = "Description goes here", // TODO
        source = null, // TODO
        imageUrl = imageRef,
    )
}

fun FeedSourceResultItemDto.toDomain(): FeedSourceResultItem {
    return FeedSourceResultItem(
        url = url,
        title = title,
        favicon = favicon,
        description = description
    )
}

fun ArticleDetailsDto.toDomain(): ArticleDetails {
    return ArticleDetails(
        id = articleId,
        title = title,
        content = content ?: "Content goes here", // TODO
        imageUrl = imageRef
    )
}
