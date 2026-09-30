package com.srnyndrs.android.briefly.domain.usecase.content.feed

import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import kotlin.time.ExperimentalTime


@OptIn(ExperimentalTime::class)
class GetExplorePostPagingFlowUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    operator fun invoke(filter: ExplorePostFilter = ExplorePostFilter()): Flow<PagingData<Post>> {
        return repository.getExplorePostPagingFlow(filter)
    }
}
