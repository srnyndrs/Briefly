package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticleByIdUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel(assistedFactory = PostDetailsViewModel.Factory::class)
class PostDetailsViewModel @AssistedInject constructor(
    private val getArticleByIdUseCase: GetArticleByIdUseCase,
    @Assisted private val postId: String
): ViewModel() {

    @AssistedFactory
    interface Factory {
        fun create(postId: String): PostDetailsViewModel
    }

    private val _state = MutableStateFlow<UiState<PostDetails>>(UiState.Idle)
    val state = _state.asStateFlow()
        .onStart {
            getArticle(postId)
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000L),
            UiState.Loading
        )

    private fun getArticle(postId: String) = viewModelScope.launch {
        _state.value = UiState.Loading
        getArticleByIdUseCase(postId).fold(
            onSuccess = { article ->
                _state.value = UiState.Success(data = article)
            },
            onFailure = { exception ->
                _state.value = UiState.Error(message = exception.message ?: "Unknown error occurred")
            }
        )
    }
}
