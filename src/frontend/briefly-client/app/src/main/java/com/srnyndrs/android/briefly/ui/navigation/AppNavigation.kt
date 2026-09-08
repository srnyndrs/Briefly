package com.srnyndrs.android.briefly.ui.navigation

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.navigation
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthScreen
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthViewModel
import com.srnyndrs.android.briefly.ui.screen.content.screen.ContentScreen
import com.srnyndrs.android.briefly.ui.screen.content.screen.ContentViewModel
import com.srnyndrs.android.briefly.ui.screen.profile.screen.ProfileScreen

@Composable
fun AppNavigation(
    modifier: Modifier = Modifier,
    navController: NavHostController
) {

    val onNavigationEvent = { event: NavigationEvent ->
        when(event) {
            is NavigationEvent.NavigateToAuthScreen -> {
                navController.navigate(Graph.Auth) {
                    popUpTo(Graph.Main) { inclusive = true }
                }
            }
            is NavigationEvent.NavigateToMainScreen -> {
                navController.navigate(Graph.Main) {
                    popUpTo(Graph.Auth) { inclusive = true }
                }
            }
            is NavigationEvent.NavigateToProfileScreen -> {
                navController.navigate(Graph.Profile)
            }
        }
    }

    NavHost(
        modifier = Modifier.then(modifier),
        navController = navController,
        startDestination = Graph.Auth
    ) {
        authGraph(
            modifier = Modifier.fillMaxSize(),
            onNavigationEvent = onNavigationEvent
        )
        mainGraph(
            modifier = Modifier.fillMaxSize(),
            onNavigationEvent = onNavigationEvent
        )
        profileGraph(
            modifier = Modifier.fillMaxSize(),
            onNavigationEvent = onNavigationEvent
        )
    }
}

fun NavGraphBuilder.authGraph(
    modifier: Modifier = Modifier,
    onNavigationEvent: (NavigationEvent) -> Unit
) {
    navigation<Graph.Auth>(
        startDestination = Screen.Auth
    ) {
        composable<Screen.Auth> {
            val viewModel: AuthViewModel = hiltViewModel()
            val state by viewModel.state.collectAsStateWithLifecycle()

            AuthScreen(
                modifier = Modifier.then(modifier),
                state = state,
                onSuccess = {
                    onNavigationEvent(NavigationEvent.NavigateToMainScreen)
                },
                onAuthEvent = viewModel::onEvent
            )
        }
    }
}

fun NavGraphBuilder.mainGraph(
    modifier: Modifier = Modifier,
    onNavigationEvent: (NavigationEvent) -> Unit
) {
    navigation<Graph.Main>(
        startDestination = Screen.Content
    ) {
        composable<Screen.Content> {
            val viewModel = hiltViewModel<ContentViewModel>()
            val logoutState by viewModel.logoutState.collectAsStateWithLifecycle()

            LaunchedEffect(logoutState) {
                if (logoutState is AuthState.Unauthenticated) {
                    onNavigationEvent(NavigationEvent.NavigateToAuthScreen)
                }
            }

            ContentScreen(
                modifier = Modifier.then(modifier),
                onLogout = {
                    viewModel.logoutUser()
                },
                onNavigateProfile = {
                    onNavigationEvent(NavigationEvent.NavigateToProfileScreen)
                }
            )
        }
    }
}

fun NavGraphBuilder.profileGraph(
    modifier: Modifier = Modifier,
    onNavigationEvent: (NavigationEvent) -> Unit
) {
    navigation<Graph.Profile>(
        startDestination = Screen.Profile
    ) {
        composable<Screen.Profile> {
            ProfileScreen(
                modifier = Modifier.then(modifier)
            )
        }
    }
}
