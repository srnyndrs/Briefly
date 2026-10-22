package com.srnyndrs.android.briefly.domain.usecase.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import javax.inject.Inject

class GetFeedSourcesUseCase @Inject constructor(
    private val repository: SourceRepository,
) {
    suspend operator fun invoke(query: String? = null): Result<List<Source>> {
        return repository.fetchFeedSources(query)
    }
}
