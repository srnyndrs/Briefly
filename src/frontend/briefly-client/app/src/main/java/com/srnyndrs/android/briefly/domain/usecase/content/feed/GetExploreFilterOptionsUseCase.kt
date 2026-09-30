package com.srnyndrs.android.briefly.domain.usecase.content.feed

import com.srnyndrs.android.briefly.domain.model.content.feed.filter.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetExploreFilterOptionsUseCase @Inject constructor(
    private val repository: ContentRepository,
) {
    suspend operator fun invoke(): Result<ExploreFilterOptions> {
        return repository.fetchExploreFilterOptions()
    }
}
