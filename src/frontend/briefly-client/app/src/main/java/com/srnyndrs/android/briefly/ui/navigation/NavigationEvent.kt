package com.srnyndrs.android.briefly.ui.navigation

sealed class NavigationEvent {
    data object NavigateToAuthScreen: NavigationEvent()
    data object NavigateToMainScreen: NavigationEvent()
    data object NavigateToProfileScreen: NavigationEvent()
}
