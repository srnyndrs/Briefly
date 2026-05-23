package com.srnyndrs.android.briefly.data.remote.content.dto

import com.srnyndrs.android.briefly.data.utils.InstantIso8601Serializer
import kotlinx.serialization.*
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@Serializable
data class FeedResultDto(
    val items: List<FeedResultItemDto>,
    val total: Long
)

@Serializable
@OptIn(ExperimentalTime::class)
data class FeedResultItemDto(
    @SerialName("article_id")
    val articleId: String,
    val title: String,
    @SerialName("source_title")
    val sourceTitle: String? = null,
    val description: String? = null,
    @SerialName("canonical_url")
    val canonicalURL: String? = null,
    val language: String? = null,
    val category: String? = null,
    @SerialName("image_ref")
    val imageRef: String? = null,
    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("published_at")
    val publishedAt: Instant,
    @SerialName("has_content")
    val hasContent: Boolean,
)

@Serializable
data class FeedSourceSubscribeRequestDto(
    @SerialName("source_id")
    val sourceId: String,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class FeedSourceSubscribeResponseDto(
    @SerialName("user_id")
    val userId: String,
    @SerialName("source_id")
    val sourceId: String,
    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("created_at")
    val createdAt: Instant,
)

@Serializable
data class FeedSourceExploreRequestDto(
    val url: String,
)

@Serializable
data class FeedSourceResultItemDto(
    @SerialName("feed_id")
    val feedId: String,
    val url: String,
    val title: String,
    @SerialName("content_type")
    val contentType: String? = null,
    val favicon: String? = null,
    val description: String? = null,
    @SerialName("is_subscribed")
    val isSubscribed: Boolean,
)


@Serializable
@OptIn(ExperimentalTime::class)
data class ArticleDetailsDto (
    @SerialName("article_id")
    val articleId: String,
    @SerialName("source_id")
    val sourceId: String? = null,
    val title: String,
    @SerialName("source_title")
    val sourceTitle: String? = null,
    val description: String? = null,
    @SerialName("canonical_url")
    val canonicalURL: String? = null,
    val language: String? = null,
    val category: String? = null,
    @SerialName("image_ref")
    val imageRef: String? = null,
    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("published_at")
    val publishedAt: Instant,
    val content: String? = null,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class FeedSourceDto (
    @SerialName("feed_id")
    val feedId: String,

    @SerialName("user_id")
    val userId: String,

    val url: String,
    val title: String? = null,
    val description: String? = null,
    val favicon: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("last_crawled_at")
    val lastCrawledAt: Instant,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("next_crawl_scheduled_at")
    val nextCrawlScheduledAt: Instant,

    @SerialName("last_crawl_succeeded")
    val lastCrawlSucceeded: Boolean,

    @SerialName("consecutive_failures")
    val consecutiveFailures: Long,

    @SerialName("health_score")
    val healthScore: Double,

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
data class FeedSourceDetailsDto(
    @SerialName("feed_id")
    val feedId: String,

    @SerialName("user_id")
    val userId: String,

    val url: String,
    val title: String? = null,
    val description: String? = null,
    val favicon: String? = null,

    @SerialName("website_url")
    val websiteUrl: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("last_crawled_at")
    val lastCrawledAt: Instant,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("next_crawl_scheduled_at")
    val nextCrawlScheduledAt: Instant,

    @SerialName("last_crawl_succeeded")
    val lastCrawlSucceeded: Boolean = false,

    @SerialName("consecutive_failures")
    val consecutiveFailures: Long,

    @SerialName("health_score")
    val healthScore: Float,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("created_at")
    val createdAt: Instant,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("updated_at")
    val updatedAt: Instant,

    @SerialName("is_subscribed")
    val isSubscribed: Boolean
)
