package com.srnyndrs.android.briefly.ui.screen.main.navigation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.srnyndrs.android.briefly.ui.components.UiStateContainer
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.PostDetailsViewModel
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.PostDetailsScreen
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.HomeScreen
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.HomeViewModel
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreScreen
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreViewModel
import com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.SourceDetailsScreen
import com.srnyndrs.android.briefly.ui.screen.main.screen.source_details.SourceDetailsViewModel
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesScreen
import com.srnyndrs.android.briefly.ui.screen.main.screen.feed_sources.FeedSourcesViewModel
import com.srnyndrs.android.briefly.ui.util.openCustomTab

import androidx.paging.compose.collectAsLazyPagingItems
import com.srnyndrs.android.briefly.ui.screen.main.screen.settings.SettingsScreen

@Composable
fun MainNavigationGraph(
    modifier: Modifier = Modifier,
    navController: NavHostController,
) {

    val context = LocalContext.current
    val handleNavigationEvent = { event: MainNavigationEvent ->
        when(event) {
            is MainNavigationEvent.ShowPostDetails -> {
                navController.navigate(MainRoutes.PostDetails.createRoute(event.postId))
            }
            is MainNavigationEvent.ShowSourceDetails -> {
                navController.navigate(MainRoutes.SourceDetails.createRoute(event.sourceId))
            }
            is MainNavigationEvent.OpenCustomTab -> {
                event.url?.let {
                    openCustomTab(context, it)
                } ?: Unit
            }
            MainNavigationEvent.NavigateBack -> {
                if (navController.previousBackStackEntry != null) {
                    navController.popBackStack()
                }
            }
        }
    }

    NavHost(
        modifier = Modifier.then(modifier),
        navController = navController,
        startDestination = MainRoutes.Home.route
    ) {
        composable(
            route = MainRoutes.Home.route
        ) {

            val viewModel = hiltViewModel<HomeViewModel>()
            val articles = viewModel.articles.collectAsLazyPagingItems()

            HomeScreen(
                modifier = Modifier.fillMaxSize(),
                articles = articles,
                onNavigationEvent = handleNavigationEvent
            )
        }

        composable(
            route = MainRoutes.FeedSources.route
        ) {

            val viewModel = hiltViewModel<FeedSourcesViewModel>()
            val state by viewModel.state.collectAsStateWithLifecycle()

            FeedSourcesScreen(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 12.dp, vertical = 6.dp),
                state = state,
                onNavigationEvent = handleNavigationEvent,
                onEvent = viewModel::onEvent
            )
        }
        composable(
            route = MainRoutes.Explore.route
        ) {
            ExploreScreen(
                modifier = Modifier.fillMaxSize(),
                viewModel = hiltViewModel<ExploreViewModel>(),
                onNavigationEvent = handleNavigationEvent,
            )
        }
        composable(
            route = MainRoutes.PostDetails.route,
            arguments = listOf(
                navArgument(MainRoutes.ARTICLE_ID_ARG) { type = NavType.StringType },
            ),
        ) { entry ->

            val postId = entry.arguments?.getString(MainRoutes.ARTICLE_ID_ARG)
            postId?.let {
                val viewModel = hiltViewModel<PostDetailsViewModel, PostDetailsViewModel.Factory>(
                    creationCallback = { factory -> factory.create(postId) }
                )

                val state by viewModel.state.collectAsStateWithLifecycle()

                UiStateContainer(
                    modifier = Modifier.fillMaxSize(),
                    state = state
                ) { data, isLoading ->
                    PostDetailsScreen(
                        modifier = Modifier.fillMaxSize(),
                        isLoading = isLoading,
                        article = data,
                        onNavigationEvent = handleNavigationEvent
                    )
                }
            } ?: Column {
                // TODO: handle null state
            }
        }
        composable(
            route = MainRoutes.SourceDetails.route,
            arguments = listOf(
                navArgument(MainRoutes.FEED_SOURCE_ID_ARG) { type = NavType.StringType },
            ),
        ) { entry ->
            val sourceId = entry.arguments?.getString(MainRoutes.FEED_SOURCE_ID_ARG)
            sourceId?.let {
                val viewModel = hiltViewModel<SourceDetailsViewModel, SourceDetailsViewModel.SourceDetailsViewModelFactory>(
                    creationCallback = { factory -> factory.create(sourceId) }
                )
                val state by viewModel.state.collectAsStateWithLifecycle()

                SourceDetailsScreen(
                    modifier = Modifier.fillMaxSize(),
                    state = state,
                    onNavigationEvent = handleNavigationEvent,
                    onEvent = viewModel::onEvent
                )
            }
        }
        composable(
            route = MainRoutes.Settings.route,
        ) {
            SettingsScreen(
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}
