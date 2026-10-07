package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.domain.model.profile.ProfileData
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticleByIdUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetPreferenceOptionsUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.GetProfileUseCase
import com.srnyndrs.android.briefly.domain.usecase.profile.UpdatePreferencesUseCase
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
    @Assisted private val postId: String,
    private val getArticleByIdUseCase: GetArticleByIdUseCase,
    private val getProfileUseCase: GetProfileUseCase,
    private val updatePreferencesUseCase: UpdatePreferencesUseCase,
): ViewModel() {

    @AssistedFactory
    interface Factory {
        fun create(postId: String): PostDetailsViewModel
    }

    private val _state = MutableStateFlow<UiState<PostDetails>>(UiState.Idle)
    val state = _state.asStateFlow()
        .onStart {
            getArticle(postId)
            getProfile()
        }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000L),
            UiState.Loading
        )

    private val _profileState = MutableStateFlow<ProfileData?>(null)
    val profileState = _profileState.asStateFlow()

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

    private fun getProfile() = viewModelScope.launch {
        getProfileUseCase().fold(
            onSuccess = { profile ->
                _profileState.value = profile
            },
            onFailure = {
                _profileState.value = null
            }
        )
    }

    fun onEvent(event: PostDetailsEvent) = viewModelScope.launch {
        when(event) {
            is PostDetailsEvent.MuteKeyword -> {
                val keyword = event.keyword

                profileState.value?.let { profile ->
                    updatePreferencesUseCase(
                        preferences = profile.preferences.copy(
                            mutedKeywords = profile.preferences.mutedKeywords + keyword
                        )
                    )
                }
            }
        }
    }

}
