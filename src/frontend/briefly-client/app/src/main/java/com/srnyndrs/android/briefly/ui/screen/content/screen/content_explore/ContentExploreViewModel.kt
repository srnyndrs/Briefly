package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.usecase.content.article.GetArticlePagingFlowUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

@HiltViewModel
class ContentExploreViewModel @Inject constructor(
    private val getArticlePagingFlowUseCase: GetArticlePagingFlowUseCase
): ViewModel() {

    val articles: Flow<PagingData<ArticleItem>> = getArticlePagingFlowUseCase()
        .cachedIn(viewModelScope)
}