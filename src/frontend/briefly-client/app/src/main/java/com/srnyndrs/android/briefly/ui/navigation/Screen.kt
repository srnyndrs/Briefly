package com.srnyndrs.android.briefly.ui.navigation

import kotlinx.serialization.Serializable

@Serializable
sealed class Graph {
    @Serializable
    data object Auth: Graph()

    @Serializable
    data object Main: Graph()

    @Serializable
    data object Profile: Graph()
}

@Serializable
sealed class Screen {
    @Serializable
    data object Auth: Screen()

    @Serializable
    data object Content: Screen()

    @Serializable
    data object Profile: Screen()
}
