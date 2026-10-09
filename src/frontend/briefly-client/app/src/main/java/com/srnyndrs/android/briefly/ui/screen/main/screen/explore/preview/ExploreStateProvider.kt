package com.srnyndrs.android.briefly.ui.screen.main.screen.explore.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import androidx.paging.PagingData
import com.srnyndrs.android.briefly.domain.model.content.ExploreFilterOptions
import com.srnyndrs.android.briefly.domain.model.content.FilterSource
import com.srnyndrs.android.briefly.domain.model.content.Post
import com.srnyndrs.android.briefly.domain.model.content.filter.ExplorePostFilter
import com.srnyndrs.android.briefly.ui.screen.main.screen.explore.ExploreState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
class ExploreStateProvider : PreviewParameterProvider<Pair<ExploreState, Flow<PagingData<Post>>>> {
    override val values = sequenceOf(
        ExploreState(
            query = "",
            filter = ExplorePostFilter(
                categories = null,
                languages = null,
                sort = null,
            ),
            filterOptions = ExploreFilterOptions(
                categories = listOf("politics", "finance"),
                languages = listOf("hu"),
                sources = listOf(
                    FilterSource("1", "444.hu"),
                    FilterSource("2", "24.hu"),
                    FilterSource("3", "Telex"),
                ),
            ),
        ) to flowOf(
            PagingData.from(
                data = listOf(
                    Post(
                        id = "f4c972b3-2637-452a-9c2c-fb5162ee172b",
                        title = "Franciaországban bezárt az iskolák negyede a tüntetések miatt, Belgiumban vízágyúval oszlatják a diákokat, Trump konteózik",
                        description = "A két szomszédos országban ismét erőszakossá váltak a tüntetések, miközben Donald Trump amerikai elnök a nagy népességcsere-elméletet terjeszti a helyzetről.",
                        imageUrl = "https://assets.4cdn.hu/kraken/8OroXBNor2zbGWB0s-lg.jpeg",
                        categories = listOf("politics"),
                        source = "444.hu"
                    ),
                    Post(
                        id = "aeb91df2-7e10-41c2-926a-22332dc7df6c",
                        title = "Török Gábor: Adóemelés és adócsökkentés történik egyszerre",
                        description = "Így látja a politikai elemző a kormány adóügyi bejelentéseit, köztük a KATA újragondolását.\nThe post Török Gábor: Adóemelés és adócsökkentés történik egyszerre first appeared on 24.hu.",
                        imageUrl = "https://s.24.hu/app/uploads/2026/10/central-1093093691-e1791305206826-1024x577.jpg",
                        categories = listOf("finance"),
                        source = "24.hu"
                    ),
                    Post(
                        id = "a50c3170-a622-4098-a3de-1a85427c7efa",
                        title = "Hankó Balázsnak egy cellatársa van, korrektek vele a börtönben",
                        description = "A volt kulturális minisztert a múlt héten tartóztatták le, a helyzetéről a védője mondott pár dolgot.\nThe post Hankó Balázsnak egy cellatársa van, korrektek vele a börtönben first appeared on 24.hu.",
                        imageUrl = "https://s.24.hu/app/uploads/2026/10/central-1139852025-e1791215941507-1024x577-1.jpg",
                        categories = listOf("politics"),
                        source = "24.hu"
                    ),
                    Post(
                        id = "7c288d92-b478-475e-b22c-681d5fac80e1",
                        title = "Drogért és ételért lopott e-rollereket",
                        description = "A 26 éves B. R. Dominik Pilisvörösvárról, Solymárról és a környező megállóhelyekről vitte el a rollereket.",
                        imageUrl = "https://assets.4cdn.hu/kraken/8OrnzmLyOL7aLECqs-lg.jpeg",
                        categories = listOf("politics"),
                        source = "444.hu"
                    ),
                    Post(
                        id = "de30c2d0-7615-4276-8d5b-1cf5ee0c4963",
                        title = "Új programmal fogja támogatni az EU a hadiipari újítások átültetését a gyakorlatba",
                        description = "A szokásosnál gyorsabb elbírálás mellett 115 millió euróval segítenék az új technológiák alkalmazását. A Fidesz–KDNP-ből üdvözölték a kezdeményezést, de bírálták Ukrajna bevonását.",
                        imageUrl = "https://assets.telex.hu/images/20261006/1791304238-temp-249r1jqo4fmh7pealjl_cimlap-normal.jpg",
                        categories = listOf("finance"),
                        source = "Telex"
                    )
                )
            )
        )
    )
}
