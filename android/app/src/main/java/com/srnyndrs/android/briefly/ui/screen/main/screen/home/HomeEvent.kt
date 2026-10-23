package com.srnyndrs.android.briefly.ui.screen.main.screen.home

import com.srnyndrs.android.briefly.domain.model.content.Category

sealed interface HomeEvent {
    data class SelectCategory(val category: Category?) : HomeEvent
}
