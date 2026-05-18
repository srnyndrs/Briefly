package com.srnyndrs.android.briefly.data.repository.content

import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeRequestDto
import com.srnyndrs.android.briefly.data.remote.content.toDomain
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import io.ktor.http.HttpStatusCode
import javax.inject.Inject

class ContentRepositoryImpl @Inject constructor(
    private val contentApiService: ContentApiService
): ContentRepository {

    override suspend fun fetchArticles(limit: Long?, offset: Long?): Result<List<ArticleItem>> {
        return try {
            val response = contentApiService.getFeeds()
            val items = response.items.map { it.toDomain() }

            Result.success(items)
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun fetchFeedSources(query: String?): Result<List<FeedSourceResultItem>> {
        return try {
            val response = contentApiService.getFeedSources(query)
            val result = response.map { it.toDomain() }

            Result.success(result)
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun getFeedSourceSubscriptions(): Result<List<FeedSubscription>> {
        return try {
            val response = contentApiService.getFeedSourceSubscriptions()
            val result = response.map { it.toDomain() }

            Result.success(result)
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun subscribeFeedSource(sourceId: String): Result<FeedSubscription> {
        return try {
            val request = FeedSourceSubscribeRequestDto(sourceId)
            val response = contentApiService.subscribeFeedSource(request)

            Result.success(response.toDomain())
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun unsubscribeFeedSource(sourceId: String): Result<String> {
        return try {
            when(val response = contentApiService.unsubscribeFeedSource(sourceId)) {
                HttpStatusCode.NoContent -> {
                    Result.success(sourceId)
                }
                else -> {
                    val exception = Exception(response.description)
                    Result.failure(exception)
                }
            }
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun exploreFeedSources(url: String): Result<List<FeedSourceResultItem>> {
        return try {
            val response = contentApiService.exploreFeedSource(
                FeedSourceExploreRequestDto(url = url)
            )
            val result = response.map { it.toDomain() }

            Result.success(result)
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun getArticleById(articleId: String): Result<ArticleDetails> {
        return try {
            val response = contentApiService.getArticleById(articleId)
            val result = response.toDomain()

            Result.success(result)
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

}
