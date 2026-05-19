package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.ArticleDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedResultItemDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceResultItemDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeResponseDto
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription
import kotlin.time.ExperimentalTime

fun FeedResultItemDto.toDomain(): ArticleItem {
    return ArticleItem(
        id = articleId,
        title = title,
        url = canonicalURL,
        description = description,
        source = sourceTitle,
        category = category,
        imageUrl = imageRef,
        hasContent = hasContent
    )
}

fun FeedSourceResultItemDto.toDomain(): FeedSourceResultItem {
    return FeedSourceResultItem(
        id = feedId,
        url = url,
        title = title,
        favicon = favicon,
        description = description,
        isSubscribed = isSubscribed,
    )
}

@OptIn(ExperimentalTime::class)
fun ArticleDetailsDto.toDomain(): ArticleDetails {
    return ArticleDetails(
        id = articleId,
        title = title,
        content = content,
        imageUrl = imageRef,
        category = category,
        url = canonicalURL,
        publishedAt = publishedAt,
        language = language,
        source = sourceTitle
    )
}

fun FeedSourceDto.toDomain(): FeedSourceResultItem {
    return FeedSourceResultItem(
        id = feedId,
        url = url,
        title = title ?: "",
        favicon = favicon,
        description = description,
        isSubscribed = isSubscribed,
    )
}

@OptIn(ExperimentalTime::class)
fun FeedSourceSubscribeResponseDto.toDomain(): FeedSubscription {
    return FeedSubscription(
        userId = userId,
        sourceId = sourceId,
        createdAt = createdAt
    )
}

fun FeedSourceDetailsDto.toDomain(): FeedSourceDetails {
    return FeedSourceDetails(
        id = feedId,
        title = title,
        description = description,
        imageUrl = favicon
    )
}
