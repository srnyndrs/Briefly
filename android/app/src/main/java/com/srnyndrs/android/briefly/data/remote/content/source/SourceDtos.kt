package com.srnyndrs.android.briefly.data.remote.content.source

import com.srnyndrs.android.briefly.data.util.InstantIso8601Serializer
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlinx.serialization.*

@Serializable
data class SubscriptionCreateRequestDto(
    @SerialName("source_id")
    val sourceId: String,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class SubscriptionResponseDto(
    @SerialName("user_id")
    val userId: String,

    @SerialName("source_id")
    val sourceId: String,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("created_at")
    val createdAt: Instant,
)

@Serializable
data class SourceDiscoverRequestDto(
    val url: String,
)

@Serializable
data class SourceDiscoveryResultDto(
    val url: String,
    val title: String? = null,

    @SerialName("content_type")
    val contentType: String? = null,

    val favicon: String? = null,
    val description: String? = null,

    @SerialName("site_url")
    val siteUrl: String? = null,

    @SerialName("site_name")
    val siteName: String? = null,

    @SerialName("language")
    val language: String? = null,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class SourceResponseDto(
    @SerialName("source_id")
    val sourceId: String,

    val url: String,
    val title: String? = null,
    val description: String? = null,
    val favicon: String? = null,
    val verified: Boolean = false,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("last_crawled_at")
    val lastCrawledAt: Instant?,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("next_crawl_scheduled_at")
    val nextCrawlScheduledAt: Instant,

    @SerialName("last_crawl_succeeded")
    val lastCrawlSucceeded: Boolean,

    @SerialName("consecutive_failures")
    val consecutiveFailures: Long,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("created_at")
    val createdAt: Instant,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("updated_at")
    val updatedAt: Instant,

    @SerialName("is_subscribed")
    val isSubscribed: Boolean,
)

@OptIn(ExperimentalTime::class)
@Serializable
data class SourceDetailsResponseDto(
    @SerialName("source_id")
    val sourceId: String,

    val url: String,
    val title: String? = null,
    val description: String? = null,
    val favicon: String? = null,
    val verified: Boolean = false,

    @SerialName("site_url")
    val siteUrl: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("last_crawled_at")
    val lastCrawledAt: Instant?,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("next_crawl_scheduled_at")
    val nextCrawlScheduledAt: Instant,

    @SerialName("last_crawl_succeeded")
    val lastCrawlSucceeded: Boolean = false,

    @SerialName("consecutive_failures")
    val consecutiveFailures: Long,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("created_at")
    val createdAt: Instant,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("updated_at")
    val updatedAt: Instant,

    @SerialName("is_subscribed")
    val isSubscribed: Boolean,
)
