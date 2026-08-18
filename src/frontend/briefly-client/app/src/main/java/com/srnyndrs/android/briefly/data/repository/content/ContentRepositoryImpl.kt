package com.srnyndrs.android.briefly.data.repository.content

import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceSubscribeRequestDto
import com.srnyndrs.android.briefly.data.remote.content.toDomain
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceDetails
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSubscription
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import io.ktor.http.HttpStatusCode
import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class ContentRepositoryImpl @Inject constructor(
    private val contentApiService: ContentApiService
): ContentRepository {

    companion object {
        const val PAGE_SIZE = 20
    }

    override fun getArticlePagingFlow(sourceIds: List<String>?): Flow<PagingData<ArticleItem>> {
        return Pager(
            config = PagingConfig(
                pageSize = PAGE_SIZE,
                initialLoadSize = PAGE_SIZE,
                enablePlaceholders = false
            ),
            pagingSourceFactory = {
                ArticlePagingSource(contentApiService, sourceIds)
            }
        ).flow
    }

    override suspend fun fetchArticles(
        page: Int?,
        pageSize: Int?,
        sourceIds: List<String>?
    ): Result<ArticlePagingResult> {
        return try {
            val response = contentApiService.getFeeds(page, pageSize, sourceIds)
            val items = response.items.map { it.toDomain() }
            val result = ArticlePagingResult(
                page = response.page,
                count = response.pageCount,
                items = items,
            )

            Result.success(result)
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

    override suspend fun getFeedSourceDetails(sourceId: String): Result<FeedSourceDetails> {
        return try {
            val response = contentApiService.getFeedSourceDetails(sourceId)
            val result = response.toDomain()

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
