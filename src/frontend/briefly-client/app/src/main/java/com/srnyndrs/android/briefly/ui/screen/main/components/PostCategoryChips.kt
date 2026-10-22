package com.srnyndrs.android.briefly.ui.screen.main.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.PreviewLightDark
import androidx.compose.ui.unit.dp
import com.srnyndrs.android.briefly.domain.model.content.Category
import com.srnyndrs.android.briefly.ui.theme.BrieflyTheme
import com.srnyndrs.android.briefly.ui.util.stringResId

@Composable
fun PostCategoryChips(
    modifier: Modifier = Modifier,
    categories: List<Category>,
    maxLines: Int = Int.MAX_VALUE,
) {
    if (categories.isEmpty()) return

    FlowRow(
        modifier = Modifier.then(modifier),
        maxLines = maxLines,
        horizontalArrangement = Arrangement.spacedBy(space = 6.dp),
        verticalArrangement = Arrangement.spacedBy(space = 4.dp),
    ) {
        categories.forEach { category ->
            Surface(
                shape = RoundedCornerShape(size = 5.dp),
                color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f),
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
            ) {
                Text(
                    modifier = Modifier.padding(
                        horizontal = 8.dp,
                        vertical = 4.dp,
                    ),
                    text = stringResource(id = category.stringResId),
                    style = MaterialTheme.typography.labelMedium,
                )
            }
        }
    }
}

@PreviewLightDark
@Composable
fun PostCategoryChipsPreview() {
    BrieflyTheme {
        PostCategoryChips(categories = listOf(Category.SCIENCE, Category.HEALTH))
    }
}
