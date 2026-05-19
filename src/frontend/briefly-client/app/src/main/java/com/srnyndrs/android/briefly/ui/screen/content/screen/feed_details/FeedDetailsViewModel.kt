package com.srnyndrs.android.briefly.ui.screen.content.screen.feed_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.feed_source.GetFeedSourceDetailsUseCase
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

@HiltViewModel(assistedFactory = FeedDetailsViewModel.FeedDetailsViewModelFactory::class)
class FeedDetailsViewModel @AssistedInject constructor(
    @Assisted private val sourceId: String,
    private val getFeedSourceDetailsUseCase: GetFeedSourceDetailsUseCase
): ViewModel() {

    @AssistedFactory
    interface FeedDetailsViewModelFactory {
        fun create(sourceId: String): FeedDetailsViewModel
    }

    private val _state = MutableStateFlow(FeedDetailsState())
    val state = _state.asStateFlow()
        .onStart {
            fetchFeedDetails()
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5_000),
            FeedDetailsState()
        )

    fun onEvent(event: FeedDetailsEvent) {
        when(event) {
            FeedDetailsEvent.FollowFeed -> TODO()
            FeedDetailsEvent.UnfollowFeed -> TODO()
        }
    }

    private fun fetchFeedDetails() = viewModelScope.launch {
        _state.value = _state.value.copy(
            feedDetails = UiState.Loading
        )
        getFeedSourceDetailsUseCase(sourceId).fold(
            onSuccess = { data ->
                _state.value = _state.value.copy(
                    feedDetails = UiState.Success(data)
                )
            },
            onFailure = { exception ->
                _state.value = _state.value.copy(
                    feedDetails = UiState.Error(exception.message ?: "Unknown error occurred")
                )
            }
        )
    }

    private fun fetchFeedArticles() = viewModelScope.launch {

    }

}
