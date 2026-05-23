package com.srnyndrs.android.briefly.ui.screen.content.screen

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.Scaffold
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.srnyndrs.android.briefly.ui.common.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.content.components.DrawerContent
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentNavigationGraph
import com.srnyndrs.android.briefly.ui.screen.content.navigation.ContentScreens
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import kotlinx.coroutines.launch

@Composable
fun ContentScreen(
    onNavigateProfile: () -> Unit
) {

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()

    val interactDrawer = {
        scope.launch {
            drawerState.apply {
                if (isClosed) open() else close()
            }
        }
    }

    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    var isTopBarShow by remember { mutableStateOf(true) }

    LaunchedEffect(currentRoute) {
        isTopBarShow = currentRoute !in listOf(
            ContentScreens.ArticleDetails.route,
            ContentScreens.FeedSourceDetails.route,
        )
    }

    ModalNavigationDrawer(

        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet {
                ModalDrawerSheet(
                    modifier = Modifier.requiredWidth(320.dp)
                ) {
                    DrawerContent(
                        modifier = Modifier.fillMaxWidth(),
                        currentRoute = currentRoute
                    ) { route ->
                        navController.navigate(route) {
                            launchSingleTop = true
                            restoreState = true
                            popUpTo(navController.graph.startDestinationId) {
                                saveState = true
                            }
                        }
                        scope.launch { drawerState.close() }
                    }
                }
            }
        },
    ) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = {
                AnimatedVisibility(
                    visible = isTopBarShow
                ) {
                    TopAppBar(
                        modifier = Modifier.fillMaxWidth(),
                        onMenuSelect = { interactDrawer() },
                        onProfileSelect = onNavigateProfile
                    )
                }
            }
        ) { innerPadding ->
            ContentNavigationGraph(
                modifier = Modifier
                    .fillMaxSize()
                    .let {
                        if(isTopBarShow) {
                            it.padding(innerPadding)
                        } else {
                            it.padding(top = 0.dp)
                        }
                    },
                navController = navController
            )
        }
    }
}

@PreviewLightDark
@Composable
fun ContentScreenPreview() {
    BrieflyTheme {
        ContentScreen(
            onNavigateProfile = { }
        )
    }
}
