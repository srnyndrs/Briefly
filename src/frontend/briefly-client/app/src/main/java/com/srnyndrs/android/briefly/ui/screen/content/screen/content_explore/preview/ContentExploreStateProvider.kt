package com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.ArticleItem
import com.srnyndrs.android.briefly.domain.model.content.ArticlePagingResult
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.content.screen.content_explore.ContentExploreState

class ContentExploreStateProvider: PreviewParameterProvider<ContentExploreState> {
    override val values = sequenceOf(
        ContentExploreState(
            result = UiState.Loading
        ),
        ContentExploreState(
            result = UiState.Success(
                ArticlePagingResult(
                    page = 1,
                    count = 3,
                    items = listOf(
                        ArticleItem(
                            id = "1",
                            title = "Itthon és Európában is duplázna a kínai óriás, amely Magyarországon már előzi a Teslát",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Külföld",
                            source = "24.hu"
                        ),
                        ArticleItem(
                            id = "2",
                            title = "Bérfizetési probléma: egy hévízi háromcsillagos szálloda dolgozói nem kapták meg fizetésüket",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Belföld",
                            source = "Telex"
                        ),
                        ArticleItem(
                            id = "3",
                            title = "Elárulta az ETO edzője, hol folytatja a pályafutását",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Foci",
                            source = "24.hu"
                        ),
                        ArticleItem(
                            id = "4",
                            title = "\"Biztos, hogy nem\" – Havasi Bertalan karrierjének emlékére",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Belföld",
                            source = "24.hu"
                        ),
                        ArticleItem(
                            id = "5",
                            title = "Tragikus balesetben halt meg az első magyar királynő",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Történelem",
                            source = "Telex"
                        ),
                        ArticleItem(
                            id = "6",
                            title = "\"Íme néhány emlékeztető a luxusról, amit ön tegnap letagadott a közleményben\" – Magyar Péter fotókkal üzent a Kúria elnökének",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Belföld",
                            source = "24.hu"
                        )
                    )
                )
            )
        )
    )
}