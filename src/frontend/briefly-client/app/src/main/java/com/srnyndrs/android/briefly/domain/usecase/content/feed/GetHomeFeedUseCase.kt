package com.srnyndrs.android.briefly.domain.usecase.content.feed

import com.srnyndrs.android.briefly.domain.model.content.HomeFeed
import com.srnyndrs.android.briefly.domain.model.content.filter.HomePostFilter
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetHomeFeedUseCase @Inject constructor(
    private val repository: ContentRepository,
) {
    operator fun invoke(filter: HomePostFilter = HomePostFilter()): HomeFeed {
        return repository.getHomeFeed(filter)
    }
}
