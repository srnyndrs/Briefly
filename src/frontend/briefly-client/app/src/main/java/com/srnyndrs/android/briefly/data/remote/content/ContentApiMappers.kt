package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.PostResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.PostSummaryResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceDetailsResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceDiscoveryResultDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SubscriptionResponseDto
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.domain.model.content.Subscription
import com.srnyndrs.android.briefly.data.remote.content.dto.FilterOptionsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.SourceEntry
import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.FilterSource
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
fun PostSummaryResponseDto.toDomain(): Post {
    return Post(
        id = postId,
        title = title,
        url = canonicalUrl,
        description = description,
        source = sourceTitle,
        category = category,
        imageUrl = imageRef,
        publishDate = publishedAt,
        hasContent = hasContent,
    )
}

fun SourceDiscoveryResultDto.toDomain(): SourceDiscoveryResult {
    return SourceDiscoveryResult(
        id = url,
        url = url,
        title = title ?: url,
        favicon = favicon,
        description = description,
        isSubscribed = false,
    )
}

@OptIn(ExperimentalTime::class)
fun PostResponseDto.toDomain(): PostDetails {
    return PostDetails(
        id = postId,
        sourceId = sourceId,
        title = title,
        content = content,
        author = author,
        keywords = keywords,
        imageUrl = imageRef,
        category = category,
        url = canonicalUrl,
        publishedAt = publishedAt ?: Instant.fromEpochMilliseconds(0),
        language = language,
        source = sourceTitle
    )
}

fun SourceResponseDto.toDomain(): Source {
    return Source(
        id = sourceId,
        url = url,
        title = title ?: "",
        favicon = favicon,
        description = description,
        isSubscribed = isSubscribed,
    )
}

@OptIn(ExperimentalTime::class)
fun SubscriptionResponseDto.toDomain(): Subscription {
    return Subscription(
        userId = userId,
        sourceId = sourceId,
        createdAt = createdAt
    )
}

@OptIn(ExperimentalTime::class)
fun SourceDetailsResponseDto.toDomain(): SourceDetails {
    return SourceDetails(
        id = sourceId,
        title = title,
        description = description,
        websiteUrl = websiteUrl,
        imageUrl = favicon,
        subscribed = isSubscribed,
        followed = false, // TODO
        lastUpdatedAt = updatedAt
    )
}

fun SourceEntry.toDomain(): FilterSource {
    return FilterSource(
        id = id,
        title = title,
    )
}

fun FilterOptionsDto.toDomain(): ExploreFilterOptions {
    return ExploreFilterOptions(
        categories = categories,
        languages = languages,
        authors = authors,
        keywords = keywords,
        sources = sources.map { it.toDomain() },
    )
}

