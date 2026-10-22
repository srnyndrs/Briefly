package com.srnyndrs.android.briefly.data.remote.content

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.parameter

class ContentApiService(
    private val client: HttpClient,
) {

    companion object {
        private const val BASE_FEED_PATH = "feed"
        private const val BASE_EXPLORE_PATH = "explore"
        private const val BASE_POSTS_PATH = "posts"
    }

    suspend fun getFeed(request: FeedRequestDto): PersonalFeedResponseDto {
        return client.get(BASE_FEED_PATH) {
            parameter("include_filter_options", request.includeFilterOptions)
            parameter("page", request.page)
            parameter("page_size", request.pageSize)
            request.category?.let {
                parameter("category", it)
            }
        }.body()
    }

    suspend fun getExplore(request: ExploreRequestDto): PostListItemsResponseDto {
        return client.get(BASE_EXPLORE_PATH) {
            parameter("apply_user_preferences", request.applyUserPreferences)
            parameter("include_filter_options", request.includeFilterOptions)
            parameter("page", request.page)
            parameter("page_size", request.pageSize)
            request.query?.let {
                parameter("query", it)
            }
            request.categories?.forEach {
                parameter("categories", it)
            }
            request.languages?.forEach {
                parameter("languages", it)
            }
            request.sourceIds?.forEach { id ->
                parameter("source_ids", id)
            }
            request.publishedFrom?.let {
                parameter("from", it)
            }
            request.publishedTo?.let {
                parameter("to", it)
            }
            if (request.query.isNullOrBlank()) {
                request.sort?.let {
                    parameter("sort", it)
                }
            }
        }.body()
    }

    suspend fun getExploreFilterOptions(): PostListItemsResponseDto {
        return getExplore(
            ExploreRequestDto(
                page = 1,
                pageSize = 1,
                includeFilterOptions = true,
            )
        )
    }

    suspend fun getPostById(postId: String): PostResponseDto {
        return client.get("$BASE_POSTS_PATH/$postId")
            .body()
    }

}
