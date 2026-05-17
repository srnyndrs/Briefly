package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.ArticleDetailsDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedResultDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceResultItemDto
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.put
import io.ktor.client.request.setBody

class ContentApiService (
    private val client: HttpClient
) {
    suspend fun getFeeds(limit: Long? = null, offset: Long? = null): FeedResultDto {
        return client.get("feed") {
            parameter("limit", limit ?: 20)
            parameter("offset", offset ?: 0)
        }.body()
    }

    suspend fun getFeedSources(): List<FeedSourceDto> {
        return client.get("sources")
            .body()
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
