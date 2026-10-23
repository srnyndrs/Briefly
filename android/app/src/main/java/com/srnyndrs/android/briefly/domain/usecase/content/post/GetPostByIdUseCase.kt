package com.srnyndrs.android.briefly.domain.usecase.content.post

import com.srnyndrs.android.briefly.domain.model.content.post.PostDetails
import com.srnyndrs.android.briefly.domain.repository.content.ContentRepository
import javax.inject.Inject

class GetPostByIdUseCase @Inject constructor(
    private val repository: ContentRepository
) {
    suspend operator fun invoke(postId: String): Result<PostDetails> {
        return repository.getArticleById(postId)
    }
}
