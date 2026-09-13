package com.srnyndrs.android.briefly.data.remote.content.dto

import com.srnyndrs.android.briefly.data.utils.InstantIso8601Serializer
import kotlinx.serialization.*
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@Serializable
data class FeedRequestDto(
    val page: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    val category: String? = null,

    @SerialName("include_filter_options")
    val includeFilterOptions: Boolean = false,
)

@Serializable
data class ExploreRequestDto(
    val page: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    val categories: List<String>? = null,
    val languages: List<String>? = null,

    @SerialName("source_ids")
    val sourceIds: List<String>? = null,

    @SerialName("from")
    val publishedFrom: String? = null,

    val query: String? = null,

    @SerialName("to")
    val publishedTo: String? = null,

    val sort: String? = null,

    @SerialName("include_filter_options")
    val includeFilterOptions: Boolean = false,
)

@Serializable
data class PostListItemsResponseDto(
    val items: List<PostSummaryResponseDto>,
    val total: Long,
    val page: Int = 1,

    @SerialName("page_count")
    val pageCount: Int = 1,

    @SerialName("page_size")
    val pageSize: Int = 20,

    @SerialName("filter_options")
    val filterOptions: FilterOptionsDto? = null,
)

@Serializable
data class FilterOptionsDto(
    val categories: List<String> = emptyList(),
    val languages: List<String> = emptyList(),
    val sources: List<SourceEntry> = emptyList(),
)

@Serializable
data class SourceEntry(
    val id: String,
    val title: String,
)

@Serializable
@OptIn(ExperimentalTime::class)
data class PostSummaryResponseDto(
    @SerialName("post_id")
    val postId: String,

    @SerialName("source_id")
    val sourceId: String? = null,

    val title: String,

    @SerialName("source_title")
    val sourceTitle: String? = null,

    val description: String? = null,

    @SerialName("canonical_url")
    val canonicalUrl: String? = null,

    val language: String? = null,
    val category: String? = null,

    @SerialName("image_ref")
    val imageRef: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("published_at")
    val publishedAt: Instant?,

    @SerialName("has_content")
    val hasContent: Boolean,
)

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
)


@Serializable
@OptIn(ExperimentalTime::class)
data class PostResponseDto(
    @SerialName("post_id")
    val postId: String,

    @SerialName("source_id")
    val sourceId: String? = null,

    val title: String,

    @SerialName("source_title")
    val sourceTitle: String? = null,

    val description: String? = null,

    @SerialName("canonical_url")
    val canonicalUrl: String? = null,

    val language: String? = null,
    val category: String? = null,

    @SerialName("image_ref")
    val imageRef: String? = null,

    @Serializable(with = InstantIso8601Serializer::class)
    @SerialName("published_at")
    val publishedAt: Instant?,

    val content: String? = null,
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

    @SerialName("website_url")
    val websiteUrl: String? = null,

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
    val isSubscribed: Boolean
)
