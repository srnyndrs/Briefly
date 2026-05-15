package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.FeedSourceResultItem
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.ExploreFeedSourcesUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class FeedSearchViewModel @Inject constructor(
    private val exploreFeedSourcesUseCase: ExploreFeedSourcesUseCase
): ViewModel() {

    private val _state = MutableStateFlow<UiState<List<FeedSourceResultItem>>>(UiState.Idle)
    val state = _state.asStateFlow()

    fun exploreFeedSources(url: String) = viewModelScope.launch {
        _state.value = UiState.Loading
        exploreFeedSourcesUseCase(url).fold(
            onSuccess = { results ->
                _state.value = UiState.Success(data = results)
            },
            onFailure = { exception ->
                _state.value = UiState.Error(message = exception.message ?: "Unknown error")
            }
        )
    }

}
