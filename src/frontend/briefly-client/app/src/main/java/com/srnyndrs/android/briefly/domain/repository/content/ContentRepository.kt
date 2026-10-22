package com.srnyndrs.android.briefly.domain.repository.content

import com.srnyndrs.android.briefly.domain.model.content.post.PostDetails
import com.srnyndrs.android.briefly.domain.model.content.post.PostPagingResult
import com.srnyndrs.android.briefly.domain.model.content.feed.ExploreFeed
import com.srnyndrs.android.briefly.domain.model.content.feed.HomeFeed
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.model.content.feed.filter.HomePostFilter

interface ContentRepository {
    fun getHomeFeed(filter: HomePostFilter): HomeFeed
    fun getExploreFeed(filter: ExplorePostFilter): ExploreFeed
    suspend fun fetchArticles(
        page: Int? = 1,
        pageSize: Int? = 20,
        sourceIds: List<String>? = null,
        applyUserPreferences: Boolean = true,
    ): Result<PostPagingResult>
    suspend fun fetchExploreFilterOptions(): Result<ExploreFilterOptions>
    suspend fun getArticleById(postId: String): Result<PostDetails>
}
