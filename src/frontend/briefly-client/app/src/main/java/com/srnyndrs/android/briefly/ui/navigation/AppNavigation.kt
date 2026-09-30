package com.srnyndrs.android.briefly.ui.navigation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.navigation
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.auth.AuthState
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthScreen
import com.srnyndrs.android.briefly.ui.screen.auth.screen.AuthViewModel
import com.srnyndrs.android.briefly.ui.screen.main.MainScreen
import com.srnyndrs.android.briefly.ui.screen.main.MainViewModel
import com.srnyndrs.android.briefly.ui.screen.profile.ProfileScreen
import com.srnyndrs.android.briefly.ui.screen.profile.ProfileViewModel

@Composable
fun AppNavigation(
    modifier: Modifier = Modifier,
    viewModel: AppViewModel,
    navController: NavHostController,
) {

    val authState by viewModel.authState.collectAsStateWithLifecycle()

    when (authState) {
        AuthState.Loading -> {
            SessionSplash(
                modifier = Modifier.then(modifier)
            )
        }
        AuthState.Unavailable -> {
            Box(
                modifier = Modifier.then(modifier),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Text(
                        text = stringResource(R.string.session_unavailable),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                    Button(onClick = viewModel::refreshSession) {
                        Text(text = stringResource(R.string.session_retry))
                    }
                }
            }
        }
        AuthState.Authenticated,
        AuthState.Unauthenticated -> {
            LaunchedEffect(authState) {
                when (authState) {
                    AuthState.Authenticated -> {
                        navController.navigate(Graph.Main) {
                            launchSingleTop = true
                            popUpTo(Graph.Auth) {
                                inclusive = true
                            }
                        }
                    }
                    AuthState.Unauthenticated -> {
                        navController.navigate(Graph.Auth) {
                            launchSingleTop = true
                            popUpTo(Graph.Main) {
                                inclusive = true
                            }
                        }
                    }
                    AuthState.Loading,
                    AuthState.Unavailable -> Unit
                }
            }

            NavHost(
                modifier = modifier,
                navController = navController,
                startDestination = when (authState) {
                    AuthState.Authenticated -> Graph.Main
                    AuthState.Unauthenticated -> Graph.Auth
                    AuthState.Loading,
                    AuthState.Unavailable -> error("Session state must select a navigation graph")
                },
            ) {
                authGraph(modifier = Modifier.fillMaxSize())
                mainGraph(
                    modifier = Modifier.fillMaxSize(),
                    onProfileNavigation = {
                        navController.navigate(Graph.Profile)
                    },
                )
                profileGraph(modifier = Modifier.fillMaxSize())
            }
        }
    }
}

fun NavGraphBuilder.authGraph(
    modifier: Modifier = Modifier,
) {
    navigation<Graph.Auth>(startDestination = Screen.Auth) {
        composable<Screen.Auth> {
            val viewModel: AuthViewModel = hiltViewModel()
            val state by viewModel.state.collectAsStateWithLifecycle()

            AuthScreen(
                modifier = modifier,
                state = state,
                onAuthEvent = viewModel::onEvent,
            )
        }
    }
}

fun NavGraphBuilder.mainGraph(
    modifier: Modifier = Modifier,
    onProfileNavigation: () -> Unit,
) {
    navigation<Graph.Main>(startDestination = Screen.Main) {
        composable<Screen.Main> {
            val viewModel = hiltViewModel<MainViewModel>()

            MainScreen(
                modifier = modifier,
                onProfileNavigation = onProfileNavigation,
                onLogout = viewModel::logoutUser,
            )
        }
    }
}

fun NavGraphBuilder.profileGraph(
    modifier: Modifier = Modifier,
) {
    navigation<Graph.Profile>(startDestination = Screen.Profile) {
        composable<Screen.Profile> {
            val viewModel = hiltViewModel<ProfileViewModel>()
            val state by viewModel.state.collectAsStateWithLifecycle()

            ProfileScreen(
                modifier = modifier,
                state = state,
            )
        }
    }
}
