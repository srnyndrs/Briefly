package com.srnyndrs.android.briefly.domain.usecase.content.source

import com.srnyndrs.android.briefly.domain.model.content.source.SourceDetails
import com.srnyndrs.android.briefly.domain.repository.content.source.SourceRepository
import javax.inject.Inject

class GetFeedSourceDetailsUseCase @Inject constructor(
    private val repository: SourceRepository,
) {
    suspend operator fun invoke(sourceId: String): Result<SourceDetails> {
        return repository.getFeedSourceDetails(sourceId)
    }
}
