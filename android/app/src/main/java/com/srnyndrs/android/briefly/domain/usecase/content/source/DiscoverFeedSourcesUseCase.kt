package com.srnyndrs.android.briefly.domain.usecase.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import javax.inject.Inject

class DiscoverFeedSourcesUseCase @Inject constructor(
    private val repository: SourceRepository,
) {
    suspend operator fun invoke(url: String): Result<List<SourceDiscoveryResult>> {
        return repository.discoverFeedSources(url = url.trim())
    }
}
