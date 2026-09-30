package com.srnyndrs.android.briefly.data.remote.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.model.content.source.Subscription
import kotlin.time.ExperimentalTime

fun SourceDiscoveryResultDto.toDomain(): SourceDiscoveryResult {
    return SourceDiscoveryResult(
        id = url,
        url = url,
        title = title ?: url,
        faviconUrl = favicon,
        description = description,
        isSubscribed = false,
    )
}

fun SourceResponseDto.toDomain(): Source {
    return Source(
        id = sourceId,
        url = url,
        title = title ?: "", // TODO: revisit default value
        faviconUrl = favicon,
        description = description,
        verified = verified,
        isSubscribed = isSubscribed,
    )
}

@OptIn(ExperimentalTime::class)
fun SubscriptionResponseDto.toDomain(): Subscription {
    return Subscription(
        userId = userId,
        sourceId = sourceId,
        createdAt = createdAt,
    )
}

@OptIn(ExperimentalTime::class)
fun SourceDetailsResponseDto.toDomain(): SourceDetails {
    return SourceDetails(
        id = sourceId,
        title = title,
        description = description,
        siteUrl = siteUrl,
        faviconUrl = favicon,
        isSubscribed = isSubscribed,
        verified = verified,
        lastUpdatedAt = updatedAt,
    )
}
