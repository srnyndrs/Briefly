package com.srnyndrs.android.briefly.data.remote.content.dto

import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class FeedResultDto (
    val items: List<FeedResultItemDto>,
    val total: Long
)

@Serializable
data class FeedResultItemDto (
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
    @SerialName("published_at")
    val publishedAt: String? = null // ISO-format
)

@Serializable
data class FeedSourceExploreRequestDto(
    val url: String,
)

@Serializable
data class FeedSourceResultItemDto(
    val url: String,
    val title: String,
    @SerialName("content_type")
    val contentType: String? = null,
    val favicon: String? = null,
    val description: String? = null
)


@Serializable
data class ArticleDetailsDto (
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
    @SerialName("published_at")
    val publishedAt: String? = null, // ISO-format
    val content: String? = null,
)

@Serializable
data class FeedSourceDto (
    @SerialName("feed_id")
    val feedId: String,

    @SerialName("user_id")
    val userId: String,

    val url: String,
    val title: String? = null,
    val description: String? = null,
    val favicon: String? = null,

    @SerialName("last_crawled_at")
    val lastCrawledAt: String? = null,

    @SerialName("next_crawl_scheduled_at")
    val nextCrawlScheduledAt: String,

    @SerialName("last_crawl_succeeded")
    val lastCrawlSucceeded: Boolean,

    @SerialName("consecutive_failures")
    val consecutiveFailures: Long,

    @SerialName("health_score")
    val healthScore: Double,

    @SerialName("created_at")
    val createdAt: String,

    @SerialName("updated_at")
    val updatedAt: String
)
