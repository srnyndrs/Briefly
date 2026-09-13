package com.srnyndrs.android.briefly.data.repository.content

import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.dto.SubscriptionCreateRequestDto
import com.srnyndrs.android.briefly.data.remote.content.toDomain
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.domain.model.content.SourceDetails
import com.srnyndrs.android.briefly.domain.model.content.Source
import com.srnyndrs.android.briefly.domain.model.content.Subscription
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import io.ktor.http.HttpStatusCode
import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.data.remote.content.dto.ExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedRequestDto
import com.srnyndrs.android.briefly.domain.model.content.filter.HomePostFilter
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
class ContentRepositoryImpl @Inject constructor(
    private val contentApiService: ContentApiService
): ContentRepository {

    companion object {
        const val PAGE_SIZE = 20
    }

    override fun getHomePostPagingFlow(filter: HomePostFilter): Flow<PagingData<Post>> = getHomePostPagingFlow(
        FeedRequestDto(
            includeFilterOptions = true,
            category = filter.category
        )
    )

    override fun getExplorePostPagingFlow(filter: ExplorePostFilter): Flow<PagingData<Post>> = getExplorePostPagingFlow(
        ExploreRequestDto(
            query = filter.query,
            sourceIds = filter.sourceIds,
            categories = filter.categories,
            languages = filter.languages,
            publishedFrom = filter.publishedFrom?.toString(),
            publishedTo = filter.publishedTo?.toString(),
            sort = filter.sort,
        )
    )

    private fun getHomePostPagingFlow(request: FeedRequestDto): Flow<PagingData<Post>> {
        return Pager(
            config = PagingConfig(
                pageSize = PAGE_SIZE,
                initialLoadSize = PAGE_SIZE,
                enablePlaceholders = false
            ),
            pagingSourceFactory = {
                PersonalFeedPagingSource(contentApiService, request)
            }
        ).flow
    }

    private fun getExplorePostPagingFlow(request: ExploreRequestDto): Flow<PagingData<Post>> {
        return Pager(
            config = PagingConfig(
                pageSize = PAGE_SIZE,
                initialLoadSize = PAGE_SIZE,
                enablePlaceholders = false
            ),
            pagingSourceFactory = {
                ExploreFeedPagingSource(contentApiService, request)
            }
        ).flow
    }

    override suspend fun fetchArticles(
        page: Int?,
        pageSize: Int?,
        sourceIds: List<String>?
    ): Result<PostPagingResult> {
        return try {
            val response = contentApiService.getExplore(
                ExploreRequestDto(
                    page = page ?: 1,
                    pageSize = pageSize ?: PAGE_SIZE,
                    sourceIds = sourceIds,
                )
            )
            val items = response.items.map { it.toDomain() }
            val result = PostPagingResult(
                page = response.page,
                count = response.pageCount,
                items = items,
            )

            Result.success(result)
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun fetchFeedSources(query: String?): Result<List<Source>> {
        return try {
            val response = contentApiService.getFeedSources(query)
            val result = response.map { it.toDomain() }

            Result.success(result)
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun getFeedSourceSubscriptions(): Result<List<Subscription>> {
        return try {
            val response = contentApiService.getFeedSourceSubscriptions()
            val result = response.map { it.toDomain() }

            Result.success(result)
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun getFeedSourceDetails(sourceId: String): Result<SourceDetails> {
        return try {
            val response = contentApiService.getFeedSourceDetails(sourceId)
            val result = response.toDomain()

            Result.success(result)
        }  catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun subscribeFeedSource(sourceId: String): Result<Subscription> {
        return try {
            val request = SubscriptionCreateRequestDto(sourceId)
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

    override suspend fun getArticleById(postId: String): Result<PostDetails> {
        return try {
            val response = contentApiService.getPostById(postId)
            val result = response.toDomain()

            Result.success(result)
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

}
