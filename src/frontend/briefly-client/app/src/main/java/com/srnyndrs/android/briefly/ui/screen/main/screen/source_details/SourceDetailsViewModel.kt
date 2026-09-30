package com.srnyndrs.android.briefly.ui.screen.main.screen.source_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.post.GetPostsUseCase
import com.srnyndrs.android.briefly.domain.usecase.content.source.SourceUseCases
import com.srnyndrs.android.briefly.domain.usecase.preferences.GetPreferencesUseCase
import com.srnyndrs.android.briefly.domain.usecase.preferences.SetSourceBlockedUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlin.time.ExperimentalTime
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel(assistedFactory = SourceDetailsViewModel.SourceDetailsViewModelFactory::class)
class SourceDetailsViewModel @AssistedInject constructor(
    @Assisted private val sourceId: String,
    private val sourceUseCases: SourceUseCases,
    private val getPostsUseCase: GetPostsUseCase,
    private val getPreferencesUseCase: GetPreferencesUseCase,
    private val setSourceBlockedUseCase: SetSourceBlockedUseCase,
): ViewModel() {

    @AssistedFactory
    interface SourceDetailsViewModelFactory {
        fun create(sourceId: String): SourceDetailsViewModel
    }

    private val _state = MutableStateFlow(value = SourceDetailsState())
    val state = _state.asStateFlow()

    init {
        fetchBlockStatus()
        fetchSourceDetails()
        fetchFeedArticles()
    }

    fun onEvent(event: SourceDetailsEvent) {
        when (event) {
            SourceDetailsEvent.RetryBlockStatus -> {
                if (_state.value.blockStatus is UiState.Error) fetchBlockStatus()
            }
            SourceDetailsEvent.ToggleBlock -> changeBlockState()
            SourceDetailsEvent.RetryFeedDetails -> {
                if (_state.value.feedDetails is UiState.Error) fetchSourceDetails()
            }
            SourceDetailsEvent.RetryArticles -> {
                if (_state.value.articles is UiState.Error) fetchFeedArticles()
            }
            SourceDetailsEvent.ToggleSubscribe -> changeSubscription()
        }
    }

    private fun fetchBlockStatus() = viewModelScope.launch {
        _state.update { it.copy(blockStatus = UiState.Loading) }
        getPreferencesUseCase().fold(
            onSuccess = { preferences ->
                _state.update {
                    it.copy(blockStatus = UiState.Success(data = sourceId in preferences.blockedSourceIds))
                }
            },
            onFailure = { exception ->
                _state.update { it.copy(blockStatus = UiState.Error(message = exception.message.orEmpty())) }
            },
        )
    }

    private fun changeBlockState() {
        val blocked = (_state.value.blockStatus as? UiState.Success)?.data ?: return
        if (_state.value.isUpdatingBlock) return
        _state.update {
            it.copy(
                isUpdatingBlock = true,
                blockUpdateFailed = false,
            )
        }
        viewModelScope.launch {
            setSourceBlockedUseCase(
                sourceId = sourceId,
                blocked = !blocked,
            ).fold(
                onSuccess = { preferences ->
                    _state.update {
                        it.copy(
                            blockStatus = UiState.Success(data = sourceId in preferences.blockedSourceIds),
                            isUpdatingBlock = false,
                        )
                    }
                },
                onFailure = {
                    _state.update {
                        it.copy(
                            isUpdatingBlock = false,
                            blockUpdateFailed = true,
                        )
                    }
                },
            )
        }
    }

    private fun fetchSourceDetails() = viewModelScope.launch {
        _state.update { it.copy(feedDetails = UiState.Loading) }
        sourceUseCases.getFeedSourceDetailsUseCase(sourceId = sourceId).fold(
            onSuccess = { data ->
                _state.update { it.copy(feedDetails = UiState.Success(data = data)) }
            },
            onFailure = { exception ->
                _state.update { it.copy(feedDetails = UiState.Error(message = exception.message.orEmpty())) }
            },
        )
    }

    private fun fetchFeedArticles() = viewModelScope.launch {
        _state.update { it.copy(articles = UiState.Loading) }
        getPostsUseCase(
            sourceIds = listOf(sourceId),
            applyUserPreferences = false,
        ).fold(
            onSuccess = { (_, _, items) ->
                _state.update { it.copy(articles = UiState.Success(data = items)) }
            },
            onFailure = { exception ->
                _state.update { it.copy(articles = UiState.Error(message = exception.message.orEmpty())) }
            },
        )
    }

    @OptIn(ExperimentalTime::class)
    private fun changeSubscription() {
        val details = (_state.value.feedDetails as? UiState.Success)?.data ?: return
        if (_state.value.isUpdatingSubscription) return
        val subscribed = !details.isSubscribed
        _state.update {
            it.copy(
                isUpdatingSubscription = true,
                subscriptionUpdateFailed = false,
            )
        }
        viewModelScope.launch {
            val result = if (subscribed) {
                sourceUseCases.subscribeFeedSourceUseCase(sourceId = sourceId).map { }
            } else {
                sourceUseCases.unsubscribeFeedSourceUseCase(sourceId = sourceId).map { }
            }
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = {
                    _state.update { current ->
                        val latest = current.feedDetails as? UiState.Success
                        current.copy(
                            feedDetails = latest?.let {
                                UiState.Success(data = it.data.copy(isSubscribed = subscribed))
                            } ?: current.feedDetails,
                            isUpdatingSubscription = false,
                        )
                    }
                },
                onFailure = {
                    _state.update {
                        it.copy(
                            isUpdatingSubscription = false,
                            subscriptionUpdateFailed = true,
                        )
                    }
                },
            )
        }
    }
}
