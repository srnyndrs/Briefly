package com.srnyndrs.android.briefly.domain.usecase.content.feed

import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.filter.HomePostFilter
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class GetHomePostPagingFlowUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    operator fun invoke(filter: HomePostFilter = HomePostFilter()): Flow<PagingData<Post>> {
        return repository.getHomePostPagingFlow(filter)
    }
}
