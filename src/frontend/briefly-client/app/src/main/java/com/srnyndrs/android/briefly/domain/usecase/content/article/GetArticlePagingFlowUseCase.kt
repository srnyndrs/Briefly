package com.srnyndrs.android.briefly.domain.usecase.content.article

import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class GetArticlePagingFlowUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    operator fun invoke(sourceIds: List<String>? = null): Flow<PagingData<ArticleItem>> {
        return repository.getArticlePagingFlow(sourceIds)
    }
}
