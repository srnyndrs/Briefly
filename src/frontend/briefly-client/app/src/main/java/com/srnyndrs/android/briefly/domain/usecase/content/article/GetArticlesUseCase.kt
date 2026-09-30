package com.srnyndrs.android.briefly.domain.usecase.content.article

import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetArticlesUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(
        page: Int? = 1,
        pageSize: Int? = 20,
        sourceIds: List<String>? = null
    ): Result<PostPagingResult> {
        return repository.fetchArticles(page, pageSize, sourceIds)
    }
}
