package com.srnyndrs.android.briefly.ui.screen.main.screen.home.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.PostPagingResult
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.home.HomeState
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
class HomeStateProvider: PreviewParameterProvider<HomeState> {
    override val values = sequenceOf(
        HomeState(
            result = UiState.Loading
        ),
        HomeState(
            result = UiState.Success(
                PostPagingResult(
                    page = 1,
                    count = 3,
                    items = listOf(
                        Post(
                            id = "1",
                            title = "Itthon Ä‚Â©s EurÄ‚Ĺ‚pÄ‚Ë‡ban is duplÄ‚Ë‡zna a kÄ‚Â­nai Ä‚Ĺ‚riÄ‚Ë‡s, amely MagyarorszÄ‚Ë‡gon mÄ‚Ë‡r elÄąâ€zi a TeslÄ‚Ë‡t",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "KÄ‚Ä˝lfÄ‚Â¶ld",
                            source = "24.hu"
                        ),
                        Post(
                            id = "2",
                            title = "BÄ‚Â©rfizetÄ‚Â©si problÄ‚Â©ma: egy hÄ‚Â©vÄ‚Â­zi hÄ‚Ë‡romcsillagos szÄ‚Ë‡lloda dolgozÄ‚Ĺ‚i nem kaptÄ‚Ë‡k meg fizetÄ‚Â©sÄ‚Ä˝ket",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "BelfÄ‚Â¶ld",
                            source = "Telex"
                        ),
                        Post(
                            id = "3",
                            title = "ElÄ‚Ë‡rulta az ETO edzÄąâ€je, hol folytatja a pÄ‚Ë‡lyafutÄ‚Ë‡sÄ‚Ë‡t",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "Foci",
                            source = "24.hu"
                        ),
                        Post(
                            id = "4",
                            title = "\"Biztos, hogy nem\" Ă˘â‚¬â€ś Havasi Bertalan karrierjÄ‚Â©nek emlÄ‚Â©kÄ‚Â©re",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "BelfÄ‚Â¶ld",
                            source = "24.hu"
                        ),
                        Post(
                            id = "5",
                            title = "Tragikus balesetben halt meg az elsÄąâ€ magyar kirÄ‚Ë‡lynÄąâ€",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "TÄ‚Â¶rtÄ‚Â©nelem",
                            source = "Telex"
                        ),
                        Post(
                            id = "6",
                            title = "\"Ä‚Ĺ¤me nÄ‚Â©hÄ‚Ë‡ny emlÄ‚Â©keztetÄąâ€ a luxusrÄ‚Ĺ‚l, amit Ä‚Â¶n tegnap letagadott a kÄ‚Â¶zlemÄ‚Â©nyben\" Ă˘â‚¬â€ś Magyar PÄ‚Â©ter fotÄ‚Ĺ‚kkal Ä‚Ä˝zent a KÄ‚Ĺźria elnÄ‚Â¶kÄ‚Â©nek",
                            description = "This is really important",
                            imageUrl = "asd",
                            category = "BelfÄ‚Â¶ld",
                            source = "24.hu"
                        )
                    )
                )
            )
        )
    )
}
