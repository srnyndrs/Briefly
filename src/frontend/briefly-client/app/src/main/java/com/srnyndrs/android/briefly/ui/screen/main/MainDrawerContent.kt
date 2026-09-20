package com.srnyndrs.android.briefly.ui.screen.main

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemColors
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.Cog6Tooth
import com.composables.icons.heroicons.solid.ArrowRightOnRectangle
import com.composables.icons.heroicons.solid.Home
import com.composables.icons.heroicons.solid.MagnifyingGlass
import com.composables.icons.heroicons.solid.Newspaper
import com.composables.icons.heroicons.solid.Rss
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.TopAppBar
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainRoutes
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun MainDrawerContent(
    modifier: Modifier = Modifier,
    currentRoute: String?,
    onDrawerEvent: (MainDrawerContentEvent) -> Unit
) {

    val scrollState = rememberScrollState()
    val itemColors = NavigationDrawerItemDefaults.colors(
        selectedContainerColor = MaterialTheme.colorScheme.onSurface
            .copy(0.125f),
        unselectedContainerColor = MaterialTheme.colorScheme.surface,
    )

    Column(
        modifier = Modifier.then(modifier)
            .padding(horizontal = 16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        Spacer(Modifier.height(12.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                modifier = Modifier.size(32.dp),
                imageVector = Heroicons.Solid.Newspaper,
                contentDescription = null // TODO
            )
            Text(
                modifier = Modifier.padding(16.dp),
                text = stringResource(R.string.app_name),
                style = MaterialTheme.typography.titleLarge,
            )
        }
        HorizontalDivider(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp)),
            thickness = 2.dp,
            color = MaterialTheme.colorScheme.onSurface
        )
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            NavigationDrawerItem(
                colors = itemColors,
                label = {
                    Text(
                        text = "Home"
                    )
                },
                selected = currentRoute == MainRoutes.Home.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.Home,
                        contentDescription = null
                    )
                },
                onClick = {
                    onDrawerEvent(MainDrawerContentEvent.NavigateHomeScreen)
                }
            )
            NavigationDrawerItem(
                colors = itemColors,
                label = {
                    Text(
                        text = "Explore"
                    )
                },
                selected = currentRoute == MainRoutes.Explore.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.MagnifyingGlass,
                        contentDescription = null
                    )
                },
                onClick = {
                    onDrawerEvent(MainDrawerContentEvent.NavigateExploreScreen)
                }
            )
        }
        HorizontalDivider(
            thickness = 1.dp,
            color = MaterialTheme.colorScheme.onSurface.copy(0.125f)
        )
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            NavigationDrawerItem(
                colors = itemColors,
                label = {
                    Text(
                        text = "Feed Sources"
                    )
                },
                selected = currentRoute == MainRoutes.FeedSources.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.Rss,
                        contentDescription = null
                    )
                },
                onClick = {
                    onDrawerEvent(MainDrawerContentEvent.NavigateFeedsScreen)
                }
            )
        }
        HorizontalDivider(
            thickness = 1.dp,
            color = MaterialTheme.colorScheme.onSurface.copy(0.125f)
        )
        NavigationDrawerItem(
            colors = itemColors,
            label = {
                Text(
                    text = "Settings"
                )
            },
            selected = currentRoute == MainRoutes.Settings.route,
            icon = {
                Icon(
                    imageVector = Heroicons.Outline.Cog6Tooth,
                    contentDescription = null // TODO
                )
            },
            onClick = {
                onDrawerEvent(MainDrawerContentEvent.NavigateSettingsScreen)
            }
        )
        NavigationDrawerItem(
            colors = itemColors,
            label = {
                Text(
                    text = "Sign Out"
                )
            },
            selected = false,
            icon = {
                Icon(
                    imageVector = Heroicons.Solid.ArrowRightOnRectangle,
                    contentDescription = null // TODO
                )
            },
            onClick = {
                onDrawerEvent(MainDrawerContentEvent.SignOutUser)
            }
        )
    }
}

sealed class MainDrawerContentEvent {
    data object NavigateHomeScreen: MainDrawerContentEvent()
    data object NavigateExploreScreen: MainDrawerContentEvent()
    data object NavigateFeedsScreen: MainDrawerContentEvent()
    data object NavigateSettingsScreen: MainDrawerContentEvent()
    data object SignOutUser: MainDrawerContentEvent()
}

@PreviewLightDark
@Composable
fun MainDrawerContentPreview() {
    BrieflyTheme {
        ModalNavigationDrawer(
            drawerState = rememberDrawerState(initialValue = DrawerValue.Open),
            drawerContent = {
                ModalDrawerSheet(
                    modifier = Modifier.requiredWidth(320.dp)
                ) {
                    MainDrawerContent(
                        modifier = Modifier.fillMaxWidth(),
                        currentRoute = "home"
                    ) { _ -> }
                }
            }
        ) {
            Scaffold(
                modifier = Modifier.fillMaxSize(),
                topBar = {
                    TopAppBar(
                        modifier = Modifier.fillMaxWidth(),
                        onMenuSelect = {}
                    ) { }
                }
            ) { paddingValues ->
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                ) {

                }
            }
        }
    }
}
