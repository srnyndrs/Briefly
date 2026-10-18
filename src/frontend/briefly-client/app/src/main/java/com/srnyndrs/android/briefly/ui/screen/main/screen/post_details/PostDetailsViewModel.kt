package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.profile.ProfileData
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticleByIdUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetProfileUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.UpdatePreferencesUseCase
import com.srnyndrs.android.briefly.ui.model.UiState
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel(assistedFactory = PostDetailsViewModel.Factory::class)
class PostDetailsViewModel @AssistedInject constructor(
    @Assisted private val postId: String,
    private val getArticleByIdUseCase: GetArticleByIdUseCase,
    private val getProfileUseCase: GetProfileUseCase,
    private val updatePreferencesUseCase: UpdatePreferencesUseCase,
): ViewModel() {

    @AssistedFactory
    interface Factory {
        fun create(postId: String): PostDetailsViewModel
    }

    private val _state = MutableStateFlow(PostDetailsState())
    val state = _state.asStateFlow()

    private var profile: ProfileData? = null

    init {
        getArticle(postId)
        getProfile()
    }

    fun onEvent(event: PostDetailsEvent) = viewModelScope.launch {
        when (event) {
            PostDetailsEvent.RetryLoad -> {
                if (_state.value.details is UiState.Error) getArticle(postId)
            }
            is PostDetailsEvent.MuteKeyword -> {
                val keyword = event.keyword

                profile?.let { profile ->
                    updatePreferencesUseCase(
                        preferences = profile.preferences.copy(
                            mutedKeywords = profile.preferences.mutedKeywords + keyword
                        )
                    )
                }
            }
        }
    }

    private fun getArticle(postId: String) = viewModelScope.launch {
        _state.value = _state.value.copy(details = UiState.Loading)
        getArticleByIdUseCase(postId).fold(
            onSuccess = { article ->
                _state.value = _state.value.copy(details = UiState.Success(data = article))
            },
            onFailure = { exception ->
                _state.value = _state.value.copy(
                    details = UiState.Error(message = exception.message ?: "Unknown error occurred"),
                )
            }
        )
    }

    private fun getProfile() = viewModelScope.launch {
        getProfileUseCase().fold(
            onSuccess = { profile ->
                this@PostDetailsViewModel.profile = profile
            },
            onFailure = {
                profile = null
            }
        )
    }

}
