package com.srnyndrs.android.briefly.ui.screen.main.screen.home.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.R
import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.ui.components.SelectionChip
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.stringResId

private const val MAX_VISIBLE_CATEGORIES = 5

@Composable
fun HomeCategorySelector(
    modifier: Modifier = Modifier,
    categories: List<Category>,
    selectedCategory: Category?,
    onCategorySelected: (Category?) -> Unit,
) {

    val visibleCategories = categories
        .take(MAX_VISIBLE_CATEGORIES)
        .let { visible ->
            if (selectedCategory != null && selectedCategory !in visible) {
                visible + selectedCategory
            } else {
                visible
            }
        }

    LazyRow(
        modifier = Modifier.then(modifier),
        horizontalArrangement = Arrangement.spacedBy(space = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        item(key = "all") {
            SelectionChip(
                label = stringResource(id = R.string.home_category_all),
                selected = selectedCategory == null,
                onClick = { onCategorySelected(null) },
            )
        }
        items(
            count = visibleCategories.size,
            key = { index -> visibleCategories[index] },
        ) { index ->

            val category = visibleCategories[index]

            SelectionChip(
                label = stringResource(id = category.stringResId),
                selected = selectedCategory == category,
                onClick = { onCategorySelected(category) },
            )
        }
    }
}

@PreviewLightDark
@Composable
fun HomeCategorySelectorPreview() {
    BrieflyTheme {
        Surface {
            HomeCategorySelector(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(
                        horizontal = 6.dp,
                        vertical = 18.dp,
                    ),
                categories = Category.entries,
                selectedCategory = Category.POLITICS,
            ) {}
        }
    }
}
