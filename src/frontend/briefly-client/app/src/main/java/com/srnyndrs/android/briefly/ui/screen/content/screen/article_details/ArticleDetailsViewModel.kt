package com.srnyndrs.android.briefly.ui.screen.content.screen.article_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.ArticleDetails
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

@HiltViewModel(assistedFactory = ArticleDetailsViewModel.Factory::class)
class ArticleDetailsViewModel @AssistedInject constructor(
    private val getArticleByIdUseCase: GetArticleByIdUseCase,
    @Assisted private val articleId: String
): ViewModel() {

    @AssistedFactory
    interface Factory {
        fun create(articleId: String): ArticleDetailsViewModel
    }

    private val _state = MutableStateFlow<UiState<ArticleDetails>>(UiState.Idle)
    val state = _state.asStateFlow()
        .onStart {
            getArticle(articleId)
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000L),
            UiState.Loading
        )

    private fun getArticle(articleId: String) = viewModelScope.launch {
        _state.value = UiState.Loading
        getArticleByIdUseCase(articleId).fold(
            onSuccess = { article ->
                _state.value = UiState.Success(data = article)
            },
            onFailure = { exception ->
                _state.value = UiState.Error(message = exception.message ?: "Unknown error occurred")
            }
        )
    }
}