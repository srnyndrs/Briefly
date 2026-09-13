package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.usecase.content.feed.GetHomePostPagingFlowUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getHomePostPagingFlowUseCase: GetHomePostPagingFlowUseCase
): ViewModel() {

    val articles: Flow<PagingData<Post>> = getHomePostPagingFlowUseCase()
        .cachedIn(viewModelScope)
}
