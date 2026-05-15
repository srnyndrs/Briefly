package com.srnyndrs.android.briefly.data.repository.content

import com.srnyndrs.android.briefly.data.remote.content.ContentApiService
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedSourceExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.toDomain
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
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
