package com.srnyndrs.android.briefly.domain.usecase.content.feed_source

import com.srnyndrs.android.briefly.domain.model.content.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class DiscoverFeedSourceUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(url: String): Result<List<SourceDiscoveryResult>> {
        return repository.discoverFeedSources(url)
    }
}
