package com.srnyndrs.android.briefly.ui.screen.main.screen.home

sealed interface HomeEvent {
    data class SelectCategory(val category: String?) : HomeEvent
}
