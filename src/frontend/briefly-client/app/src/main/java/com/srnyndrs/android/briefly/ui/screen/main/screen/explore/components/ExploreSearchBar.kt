package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredHeight
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.composables.icons.heroicons.Heroicons
import com.composables.icons.heroicons.outline.AdjustmentsHorizontal
import com.composables.icons.heroicons.solid.AdjustmentsHorizontal
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.ui.components.SearchTextField
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme

@Composable
fun ExploreSearchBar(
    modifier: Modifier = Modifier,
    query: String,
    hasActiveFilters: Boolean,
    activeFilterCount: Int,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    onOpenFilter: () -> Unit,
) {
    val buttonShape = RoundedCornerShape(22.dp)

    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        SearchTextField(
            modifier = Modifier.weight(1f),
            value = query,
            onValueChange = onQueryChange,
            placeholder = stringResource(R.string.explore_search_placeholder),
            onSearch = onSearch,
        )

        Box(
            modifier = Modifier
                .size(58.dp)
                .clip(buttonShape)
                .border(
                    width = 1.dp,
                    color = MaterialTheme.colorScheme.onSurface,
                    shape = buttonShape,
                )
                .background(
                    if (hasActiveFilters) {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.15f)
                    } else {
                        MaterialTheme.colorScheme.surface
                    }
                )
                .clickable(onClick = onOpenFilter),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                modifier = Modifier.size(26.dp),
                imageVector = if (hasActiveFilters) {
                    Heroicons.Solid.AdjustmentsHorizontal
                } else {
                    Heroicons.Outline.AdjustmentsHorizontal
                },
                contentDescription = stringResource(R.string.explore_filter_button_cd),
                tint = MaterialTheme.colorScheme.onSurface,
            )

            if (hasActiveFilters && activeFilterCount > 0) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .offset(x = (-6).dp, y = 6.dp)
                        .size(18.dp)
                        .clip(CircleShape)
                        .background(MaterialTheme.colorScheme.onSurface),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = activeFilterCount.toString(),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                        ),
                        color = MaterialTheme.colorScheme.surface,
                    )
                }
            }
        }
    }
}

@PreviewLightDark
@Composable
fun ExploreSearchBarPreview() {
    BrieflyTheme {
        Surface {
            ExploreSearchBar(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                query = "Technology",
                hasActiveFilters = true,
                activeFilterCount = 3,
                onQueryChange = {},
                onSearch = {},
                onOpenFilter = {},
            )
        }
    }
}

