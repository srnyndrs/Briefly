package com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.preview

import androidx.compose.ui.tooling.preview.PreviewParameterProvider
import com.srnyndrs.android.briefly.domain.model.content.PostDetails
import com.srnyndrs.android.briefly.ui.model.UiState
import com.srnyndrs.android.briefly.ui.screen.main.screen.post_details.PostDetailsState
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

class PostDetailsStateProvider: PreviewParameterProvider<PostDetailsState> {
    @OptIn(ExperimentalTime::class)
    override val values: Sequence<PostDetailsState>
        get() = sequenceOf(
            PostDetailsState(
                details = UiState.Loading
            ),
            PostDetailsState(
                details = UiState.Success(
                    data = PostDetails(
                        id = "1",
                        title = "Bejelentette az ÁKK: csökken a két legnépszerűbb állampapír kamata",
                        source = "Telex",
                        category = "Gazdaság",
                        url = "https://telex.hu/gazdasag/2026/05/18/akk-allamadossag-kezelo-kozpont-csokkenti-a-lakossagi-allampapirok-kamatait-fixmap-map-plusz",
                        publishedAt = Instant.parse("2026-05-18T12:36:11Z"),
                        imageUrl = "https://assets.telex.hu/images/20260518/1779107664-temp-llr9dqsr1br51afppmh_facebook.jpg",
                        content = "Május 22. péntektől egységesen 0,5 százalékponttal csökkenti a fix kamatozású lakossági állampapírok kamatszintjét az Államadósság-kezelő Központ (ÁKK) – jelentették be sajtóközleményükben. Az eddig ismert sorozatokat csütörtökig lehet még megvenni. A már megvásárolt állampapírok kamatozása nem változik, a bejelentés azt jelenti, hogy péntektől alacsonyabb kamaton lehet majd új papírokat venni.\n\n" +
                                "A változás érinti:\n\n" +
                                "a FixMÁP-ot, amelynek a kamatszintje 7 százalékról 6,5 százalékra csökken;\n\n" +
                                "a MÁP Pluszt, amelynek a kamatozása a 6,5-7,5 közötti sávból a 6-7 százalék közötti sávba vált át;\n\n" +
                                "a nyomdai MÁP Pluszt, ami az 5,5-6,75 közötti lépcsőről hanyatlik le az 5-6,25 százalék közötti szintre;\n\n" +
                                "a KTJ-I.-t, aminek a kamatszintje 5,5-ről 5 százalékra csökken;\n\n" +
                                "és a KTJ-II.-t, aminek a kamatszintje 6-ról 5 százalékra csökken.\n\n" +
                                "Ezek közül az elmúlt években egyértelműen a FixMÁP és a MÁP Plusz voltak a legnépszerűbbek. Ezeket a jelenlegi formában 2025 októberében vezette be az ÁKK, azóta ötéves futamidőben lehet őket vásárolni. A különbség kettejük között az, hogy:\n\n" +
                                "a FixMÁP egész végig egységesen kamatozik és negyedévente fizet kamatot;\n\n" +
                                "a MÁP Plusz kamatszintje fokozatosan, évről évre nő 0,25 százalékponttal, és a kamatot visszaforgatja közben saját magába.\n\n" +
                                "Az ÁKK bejelentése szerint ezek a feltételek nem változnak, csak mindegyik fix kamatozású sorozat kamatszintje csökken.\n\n" +
                                "A legtöbb állampapírt idő előtt egy egyszázalékos díj ellenében lehet eladni. A MÁP Plusznak ehhez képest van egy olyan előnye, hogy évente egyszer, egy ötnapos időtartamban ingyen vissza lehet váltani. A mostani bejelentéssel ezek a feltételek sem változnak.\n\n" +
                                "Az inflációhoz kötött (prémium állampapír) és piaci folyamatokhoz kötött (bónusz állampapír) kamatait a mostani bejelentés nem érinti.\n\n" +
                                "A kamatcsökkentést az ÁKK azzal magyarázza, hogy az elmúlt időszakban jelentősen megváltozott a magyarországi kamatkörnyezet, és a magyar állam mind a kötvénypiacon, mind a többi pénzügyi piacon a korábbinál alacsonyabb kamattal tud hitelt felvenni. Bár a közlemény nem tér ki erre, ennek az oka, hogy a külföldi befektetők sokkal szívesebben adnak pénzt az euró bevezetését ígérő Magyar-kormánynak, mint az Orbán-kormánynak."
                    )
                )
            )
        )
}
