package com.srnyndrs.android.briefly.ui.screen.main

sealed interface MainEvent {
    data object SignOut : MainEvent
}
