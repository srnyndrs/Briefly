package com.srnyndrs.android.briefly.domain.usecase.content.source

import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import javax.inject.Inject

class UnsubscribeFeedSourceUseCase @Inject constructor(
    private val repository: SourceRepository,
) {
    suspend operator fun invoke(sourceId: String): Result<String> {
        return repository.unsubscribeFeedSource(sourceId)
    }
}
