package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.ArticleDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedResultDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceResultItemDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeResponseDto
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.delete
import io.ktor.client.request.get
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.put
import io.ktor.client.request.setBody
import io.ktor.http.HttpStatusCode

class ContentApiService (
    private val client: HttpClient
) {
    suspend fun getFeeds(limit: Long? = null, offset: Long? = null): FeedResultDto {
        return client.get("feed") {
            parameter("limit", limit ?: 20)
            parameter("offset", offset ?: 0)
            parameter("subscribed_only", true)
        }.body()
    }

    suspend fun getFeedSources(query: String? = null): List<FeedSourceDto> {
        return client.get("sources") {
            parameter("q", query ?: "")
        }.body()
    }

    suspend fun getFeedSourceSubscriptions(): List<FeedSourceSubscribeResponseDto> {
        return client.get("me/subscriptions")
            .body()
    }

    suspend fun subscribeFeedSource(request: FeedSourceSubscribeRequestDto): FeedSourceSubscribeResponseDto {
        return client.post("me/subscriptions") {
            setBody(request)
        }.body()
    }

    suspend fun unsubscribeFeedSource(sourceId: String): HttpStatusCode {
        return client.delete("me/subscriptions/${sourceId}")
            .status
    }

    suspend fun exploreFeedSource(request: FeedSourceExploreRequestDto): List<FeedSourceResultItemDto>{
        return client.post("sources/explore") {
            setBody(request)
        }.body()
    }

    suspend fun getArticleById(articleId: String): ArticleDetailsDto {
        return client.get("feed/articles/${articleId}")
            .body()
    }

}
