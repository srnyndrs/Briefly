package com.srnyndrs.android.briefly.domain.usecase.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.Source
import com.srnyndrs.android.briefly.domain.model.content.source.SourceDiscoveryResult
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import javax.inject.Inject

class CreateFeedSourceUseCase @Inject constructor(
    private val repository: SourceRepository,
) {
    suspend operator fun invoke(source: SourceDiscoveryResult): Result<Source> {
        return repository.createFeedSource(source)
    }
}
