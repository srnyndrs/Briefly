package com.srnyndrs.android.briefly.ui.navigation

import kotlinx.serialization.Serializable

@Serializable
sealed class Graph {
    @Serializable
    data object Auth: Graph()

    @Serializable
    data object Main: Graph()

}

@Serializable
sealed class Screen {
    @Serializable
    data object Auth: Screen()

    @Serializable
    data object Main: Screen()

}
