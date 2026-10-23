package com.srnyndrs.android.briefly.domain.usecase.content.post

import com.srnyndrs.android.briefly.domain.model.content.post.PostPagingResult
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetPostsUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(
        page: Int? = 1,
        pageSize: Int? = 20,
        sourceIds: List<String>? = null,
        applyUserPreferences: Boolean = true,
    ): Result<PostPagingResult> {
        return repository.fetchArticles(
            page = page,
            pageSize = pageSize,
            sourceIds = sourceIds,
            applyUserPreferences = applyUserPreferences,
        )
    }
}
