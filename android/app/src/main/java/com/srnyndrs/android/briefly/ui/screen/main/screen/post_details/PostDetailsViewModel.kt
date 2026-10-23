package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.usecase.content.post.GetPostByIdUseCase
import com.srnyndrs.android.briefly.domain.usecase.preferences.GetPreferencesUseCase
import com.srnyndrs.android.briefly.domain.usecase.preferences.MuteKeywordUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel(assistedFactory = PostDetailsViewModel.Factory::class)
class PostDetailsViewModel @AssistedInject constructor(
    @Assisted private val postId: String,
    private val getPostByIdUseCase: GetPostByIdUseCase,
    private val getPreferencesUseCase: GetPreferencesUseCase,
    private val muteKeywordUseCase: MuteKeywordUseCase,
): ViewModel() {

    @AssistedFactory
    interface Factory {
        fun create(postId: String): PostDetailsViewModel
    }

    private val _state = MutableStateFlow(value = PostDetailsState())
    val state = _state.asStateFlow()

    init {
        getArticle()
        getKeywordPreferences()
    }

    fun onEvent(event: PostDetailsEvent) {
        when (event) {
            PostDetailsEvent.RetryLoad -> {
                if (_state.value.details is UiState.Error) getArticle()
            }
            PostDetailsEvent.RetryKeywordPreferences -> {
                if (_state.value.mutedKeywords is UiState.Error) getKeywordPreferences()
            }
            PostDetailsEvent.RetryMuteKeyword -> _state.value.failedKeyword?.let { muteKeyword(keyword = it) }
            is PostDetailsEvent.MuteKeyword -> muteKeyword(keyword = event.keyword)
        }
    }

    private fun getArticle() {
        _state.update { it.copy(details = UiState.Loading) }
        viewModelScope.launch {
            val result = getPostByIdUseCase(postId = postId)
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { article ->
                    _state.update { it.copy(details = UiState.Success(data = article)) }
                },
                onFailure = { exception ->
                    _state.update { it.copy(details = UiState.Error(message = exception.message.orEmpty())) }
                },
            )
        }
    }

    private fun getKeywordPreferences() {
        _state.update { it.copy(mutedKeywords = UiState.Loading) }
        viewModelScope.launch {
            val result = getPreferencesUseCase()
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { preferences ->
                    _state.update {
                        it.copy(mutedKeywords = UiState.Success(data = preferences.mutedKeywords.toSet()))
                    }
                },
                onFailure = { exception ->
                    _state.update { it.copy(mutedKeywords = UiState.Error(message = exception.message.orEmpty())) }
                },
            )
        }
    }

    private fun muteKeyword(keyword: String) {
        val mutedKeywords = (_state.value.mutedKeywords as? UiState.Success)?.data ?: return
        val trimmedKeyword = keyword.trim()
        val alreadyMuted = mutedKeywords.any {
            it.equals(
                other = trimmedKeyword,
                ignoreCase = true,
            )
        }
        if (_state.value.mutingKeyword != null || trimmedKeyword.isEmpty() || alreadyMuted) return
        _state.update {
            it.copy(
                mutingKeyword = trimmedKeyword,
                failedKeyword = null,
            )
        }
        viewModelScope.launch {
            val result = muteKeywordUseCase(keyword = trimmedKeyword)
            currentCoroutineContext().ensureActive()
            result.fold(
                onSuccess = { preferences ->
                    _state.update {
                        it.copy(
                            mutedKeywords = UiState.Success(data = preferences.mutedKeywords.toSet()),
                            mutingKeyword = null,
                        )
                    }
                },
                onFailure = {
                    _state.update {
                        it.copy(
                            mutingKeyword = null,
                            failedKeyword = trimmedKeyword,
                        )
                    }
                },
            )
        }
    }
}
