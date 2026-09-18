package com.srnyndrs.android.briefly.domain.usecase.content.feed

import com.srnyndrs.android.briefly.domain.model.content.ExploreFeed
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
class GetExploreFeedUseCase @Inject constructor(
    private val repository: ContentRepository,
) {
    operator fun invoke(filter: ExplorePostFilter = ExplorePostFilter()): ExploreFeed {
        return repository.getExploreFeed(filter)
    }
}

