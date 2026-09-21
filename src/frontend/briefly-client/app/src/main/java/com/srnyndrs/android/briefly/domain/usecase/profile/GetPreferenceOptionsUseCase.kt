package com.srnyndrs.android.briefly.domain.usecase.profile

import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetPreferenceOptionsUseCase @Inject constructor(
    private val repository: ContentRepository,
) {
    suspend operator fun invoke(): Result<ExploreFilterOptions> {
        return repository.fetchExploreFilterOptions()
    }
}
