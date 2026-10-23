package com.srnyndrs.android.briefly.data.repository.content

import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.ExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.FeedRequestDto
import com.srnyndrs.android.briefly.data.remote.content.toDomain
import com.srnyndrs.android.briefly.domain.model.content.post.Post
import com.srnyndrs.android.briefly.domain.model.content.post.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.post.PostPagingResult
import com.srnyndrs.android.briefly.domain.model.content.feed.ExploreFeed
import com.srnyndrs.android.briefly.domain.model.content.feed.HomeFeed
import com.srnyndrs.android.briefly.domain.model.content.feed.HomeFeedMetadata
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.HomePostFilter
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow

@OptIn(ExperimentalTime::class)
class ContentRepositoryImpl @Inject constructor(
    private val contentApiService: ContentApiService
): ContentRepository {

    companion object {
        const val PAGE_SIZE = 20
    }

    override fun getHomeFeed(filter: HomePostFilter): HomeFeed {
        val metadata = MutableStateFlow<HomeFeedMetadata?>(null)
        return HomeFeed(
            posts = getHomePostPagingFlow(
                request = FeedRequestDto(
                    includeFilterOptions = true,
                    category = filter.category?.name?.lowercase(),
                ),
                metadata = metadata,
            ),
            metadata = metadata,
        )
    }

    override fun getExploreFeed(filter: ExplorePostFilter): ExploreFeed {
        val metadata = MutableStateFlow<ExploreFilterOptions?>(null)
        val request = ExploreRequestDto(
            query = filter.query,
            sourceIds = filter.sourceIds,
            categories = filter.categories,
            languages = filter.languages,
            publishedFrom = filter.publishedFrom?.toString(),
            publishedTo = filter.publishedTo?.toString(),
            sort = filter.sort,
            includeFilterOptions = true,
        )
        val posts = Pager(
            config = PagingConfig(
                pageSize = PAGE_SIZE,
                initialLoadSize = PAGE_SIZE,
                enablePlaceholders = false
            ),
            pagingSourceFactory = {
                ExploreFeedPagingSource(
                    contentApiService = contentApiService,
                    request = request,
                    metadata = metadata,
                )
            }
        ).flow
        return ExploreFeed(
            posts = posts,
            metadata = metadata,
        )
    }

    private fun getHomePostPagingFlow(
        request: FeedRequestDto,
        metadata: MutableStateFlow<HomeFeedMetadata?>,
    ): Flow<PagingData<Post>> {
        return Pager(
            config = PagingConfig(
                pageSize = PAGE_SIZE,
                initialLoadSize = PAGE_SIZE,
                enablePlaceholders = false
            ),
            pagingSourceFactory = {
                PersonalFeedPagingSource(
                    contentApiService = contentApiService,
                    request = request,
                    metadata = metadata,
                )
            }
        ).flow
    }

    override suspend fun fetchArticles(
        page: Int?,
        pageSize: Int?,
        sourceIds: List<String>?,
        applyUserPreferences: Boolean,
    ): Result<PostPagingResult> {
        return try {
            val response = contentApiService.getExplore(
                ExploreRequestDto(
                    page = page ?: 1,
                    pageSize = pageSize ?: PAGE_SIZE,
                    sourceIds = sourceIds,
                    applyUserPreferences = applyUserPreferences,
                )
            )
            val items = response.items.map { it.toDomain() }
            val result = PostPagingResult(
                page = response.page,
                pageCount = response.pageCount,
                items = items,
            )

            Result.success(result)
        } catch (exception: Exception) {
            Result.failure(exception)
        }
    }

    override suspend fun fetchExploreFilterOptions(): Result<ExploreFilterOptions> {
        return try {
            val response = contentApiService.getExploreFilterOptions()
            // TODO: revisit this error handling
            val options = response.filterOptions
                ?: error("Explore response did not include filter options")
            Result.success(options.toDomain())
        } catch (exception: Exception) {
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
