package com.srnyndrs.android.briefly.domain.usecase.content.article

import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class GetHomePostPagingFlowUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    operator fun invoke(): Flow<PagingData<Post>> {
        return repository.getHomePostPagingFlow()
    }
}

class GetExplorePostPagingFlowUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    operator fun invoke(filter: ExplorePostFilter): Flow<PagingData<Post>> {
        return repository.getExplorePostPagingFlow(filter)
    }
}
