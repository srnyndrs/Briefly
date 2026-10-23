package com.srnyndrs.android.briefly.ui.screen.main

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
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
import com.srnyndrs.android.briefly.ui.screen.main.navigation.MainRoutes
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun MainDrawerContent(
    modifier: Modifier = Modifier,
    currentRoute: String?,
    isSigningOut: Boolean,
    onDrawerEvent: (MainDrawerContentEvent) -> Unit,
) {
    val itemColors = NavigationDrawerItemDefaults.colors(
        selectedContainerColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.125f),
        unselectedContainerColor = MaterialTheme.colorScheme.surface,
    )
    Column(
        modifier = Modifier
            .then(modifier)
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    modifier = Modifier.size(32.dp),
                    imageVector = Heroicons.Solid.Newspaper,
                    contentDescription = null,
                )
                Text(
                    modifier = Modifier.padding(16.dp),
                    text = stringResource(R.string.app_name),
                    style = MaterialTheme.typography.titleLarge,
                )
            }
            HorizontalDivider(thickness = 2.dp)
            NavigationDrawerItem(
                colors = itemColors,
                label = { Text(text = stringResource(R.string.main_home)) },
                selected = currentRoute == MainRoutes.Home.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.Home,
                        contentDescription = null,
                    )
                },
                onClick = { onDrawerEvent(MainDrawerContentEvent.NavigateHomeScreen) },
            )
            NavigationDrawerItem(
                colors = itemColors,
                label = { Text(text = stringResource(R.string.main_explore)) },
                selected = currentRoute == MainRoutes.Explore.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.MagnifyingGlass,
                        contentDescription = null,
                    )
                },
                onClick = { onDrawerEvent(MainDrawerContentEvent.NavigateExploreScreen) },
            )
            HorizontalDivider()
            NavigationDrawerItem(
                colors = itemColors,
                label = { Text(text = stringResource(R.string.main_feed_sources)) },
                selected = currentRoute == MainRoutes.FeedSources.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.Rss,
                        contentDescription = null,
                    )
                },
                onClick = { onDrawerEvent(MainDrawerContentEvent.NavigateFeedsScreen) },
            )
            HorizontalDivider()
            NavigationDrawerItem(
                colors = itemColors,
                label = { Text(text = stringResource(R.string.main_settings)) },
                selected = currentRoute == MainRoutes.Settings.route,
                icon = {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Outline.Cog6Tooth,
                        contentDescription = null,
                    )
                },
                onClick = { onDrawerEvent(MainDrawerContentEvent.NavigateSettingsScreen) },
            )
        }
        TextButton(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .height(56.dp),
            enabled = !isSigningOut,
            colors = ButtonDefaults.textButtonColors(
                contentColor = MaterialTheme.colorScheme.onSurfaceVariant,
            ),
            contentPadding = PaddingValues(horizontal = 16.dp),
            onClick = { onDrawerEvent(MainDrawerContentEvent.SignOutUser) },
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (isSigningOut) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = LocalContentColor.current,
                        strokeWidth = 2.dp,
                    )
                } else {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        imageVector = Heroicons.Solid.ArrowRightOnRectangle,
                        contentDescription = null,
                    )
                }
                Text(
                    text = stringResource(
                        if (isSigningOut) R.string.main_signing_out else R.string.main_sign_out,
                    ),
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }
    }
}

sealed interface MainDrawerContentEvent {
    data object NavigateHomeScreen : MainDrawerContentEvent
    data object NavigateExploreScreen : MainDrawerContentEvent
    data object NavigateFeedsScreen : MainDrawerContentEvent
    data object NavigateSettingsScreen : MainDrawerContentEvent
    data object SignOutUser : MainDrawerContentEvent
}

@PreviewLightDark
@Composable
fun MainDrawerContentPreview() {
    BrieflyTheme {
        Surface {
            MainDrawerContent(
                modifier = Modifier.fillMaxSize(),
                currentRoute = MainRoutes.Home.route,
                isSigningOut = false,
                onDrawerEvent = {},
            )
        }
    }
}
