package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticlesUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ContentExploreViewModel @Inject constructor(
    private val getArticlesUseCase: GetArticlesUseCase
): ViewModel() {

    private val _state = MutableStateFlow(ContentExploreState())
    val state = _state.asStateFlow()
        .onStart {
            fetchArticles()
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000L),
            ContentExploreState()
        )

    private fun fetchArticles() = viewModelScope.launch {
        _state.value = _state.value.copy(
            result = UiState.Loading
        )
        getArticlesUseCase().fold(
            onSuccess = { result ->
                _state.value = _state.value.copy(
                    result = UiState.Success(data = result)
                )
            },
            onFailure = { exception ->
                _state.value = _state.value.copy(
                    result = UiState.Error(message = exception.message ?: "Unknown error")
                )
            }
        )
    }


}