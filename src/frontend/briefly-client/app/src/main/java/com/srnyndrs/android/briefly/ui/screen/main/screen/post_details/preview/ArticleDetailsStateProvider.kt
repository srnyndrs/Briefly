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
                        title = "Bejelentette az Ă„â€šĂ‚ÂKK: csĂ„â€šĂ‚Â¶kken a kĂ„â€šĂ‚Â©t legnĂ„â€šĂ‚Â©pszerĂ„Ä…Ă‚Â±bb Ă„â€šĂ‹â€ˇllampapĂ„â€šĂ‚Â­r kamata",
                        source = "Telex",
                        category = "GazdasĂ„â€šĂ‹â€ˇg",
                        url = "https://telex.hu/gazdasag/2026/05/18/akk-allamadossag-kezelo-kozpont-csokkenti-a-lakossagi-allampapirok-kamatait-fixmap-map-plusz",
                        publishedAt = Instant.parse("2026-05-18T12:36:11Z"),
                        imageUrl = "https://assets.telex.hu/images/20260518/1779107664-temp-llr9dqsr1br51afppmh_facebook.jpg",
                        content = "MĂ„â€šĂ‹â€ˇjus 22. pĂ„â€šĂ‚Â©ntektĂ„Ä…Ă˘â‚¬Âl egysĂ„â€šĂ‚Â©gesen 0,5 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©kponttal csĂ„â€šĂ‚Â¶kkenti a fix kamatozĂ„â€šĂ‹â€ˇsĂ„â€šÄąĹş lakossĂ„â€šĂ‹â€ˇgi Ă„â€šĂ‹â€ˇllampapĂ„â€šĂ‚Â­rok kamatszintjĂ„â€šĂ‚Â©t az Ă„â€šĂ‚ÂllamadĂ„â€šÄąâ€šssĂ„â€šĂ‹â€ˇg-kezelĂ„Ä…Ă˘â‚¬Â KĂ„â€šĂ‚Â¶zpont (Ă„â€šĂ‚ÂKK) Ä‚ËĂ˘â€šÂ¬Ă˘â‚¬Ĺ› jelentettĂ„â€šĂ‚Â©k be sajtĂ„â€šÄąâ€škĂ„â€šĂ‚Â¶zlemĂ„â€šĂ‚Â©nyĂ„â€šĂ„Ëťkben. Az eddig ismert sorozatokat csĂ„â€šĂ„ËťtĂ„â€šĂ‚Â¶rtĂ„â€šĂ‚Â¶kig lehet mĂ„â€šĂ‚Â©g megvenni. A mĂ„â€šĂ‹â€ˇr megvĂ„â€šĂ‹â€ˇsĂ„â€šĂ‹â€ˇrolt Ă„â€šĂ‹â€ˇllampapĂ„â€šĂ‚Â­rok kamatozĂ„â€šĂ‹â€ˇsa nem vĂ„â€šĂ‹â€ˇltozik, a bejelentĂ„â€šĂ‚Â©s azt jelenti, hogy pĂ„â€šĂ‚Â©ntektĂ„Ä…Ă˘â‚¬Âl alacsonyabb kamaton lehet majd Ă„â€šÄąĹşj papĂ„â€šĂ‚Â­rokat venni." +
                                "" +
                                "A vĂ„â€šĂ‹â€ˇltozĂ„â€šĂ‹â€ˇs Ă„â€šĂ‚Â©rinti:" +
                                "" +
                                "a FixMĂ„â€šĂ‚ÂP-ot, amelynek a kamatszintje 7 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©krĂ„â€šÄąâ€šl 6,5 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©kra csĂ„â€šĂ‚Â¶kken;" +
                                "" +
                                "a MĂ„â€šĂ‚ÂP Pluszt, amelynek a kamatozĂ„â€šĂ‹â€ˇsa a 6,5-7,5 kĂ„â€šĂ‚Â¶zĂ„â€šĂ‚Â¶tti sĂ„â€šĂ‹â€ˇvbĂ„â€šÄąâ€šl a 6-7 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©k kĂ„â€šĂ‚Â¶zĂ„â€šĂ‚Â¶tti sĂ„â€šĂ‹â€ˇvba vĂ„â€šĂ‹â€ˇlt Ă„â€šĂ‹â€ˇt;" +
                                "" +
                                "na nyomdai MĂ„â€šĂ‚ÂP Pluszt, ami az 5,5-6,75 kĂ„â€šĂ‚Â¶zĂ„â€šĂ‚Â¶tti lĂ„â€šĂ‚Â©pcsĂ„Ä…Ă˘â‚¬ÂrĂ„Ä…Ă˘â‚¬Âl hanyatlik le az 5-6,25 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©k kĂ„â€šĂ‚Â¶zĂ„â€šĂ‚Â¶tti szintre;" +
                                "" +
                                "a KTJ-I.-t, aminek a kamatszintje 5,5-rĂ„Ä…Ă˘â‚¬Âl 5 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©kra csĂ„â€šĂ‚Â¶kken;" +
                                "" +
                                "Ă„â€šĂ‚Â©s a KTJ-II.-t, aminek a kamatszintje 6-rĂ„â€šÄąâ€šl 5 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©kra csĂ„â€šĂ‚Â¶kken." +
                                "" +
                                "Ezek kĂ„â€šĂ‚Â¶zĂ„â€šĂ„Ëťl az elmĂ„â€šÄąĹşlt Ă„â€šĂ‚Â©vekben egyĂ„â€šĂ‚Â©rtelmĂ„Ä…Ă‚Â±en a FixMĂ„â€šĂ‚ÂP Ă„â€šĂ‚Â©s a MĂ„â€šĂ‚ÂP Plusz voltak a legnĂ„â€šĂ‚Â©pszerĂ„Ä…Ă‚Â±bbek. Ezeket a jelenlegi formĂ„â€šĂ‹â€ˇban 2025 oktĂ„â€šÄąâ€šberĂ„â€šĂ‚Â©ben vezette be az Ă„â€šĂ‚ÂKK, azĂ„â€šÄąâ€šta Ă„â€šĂ‚Â¶tĂ„â€šĂ‚Â©ves futamidĂ„Ä…Ă˘â‚¬Âben lehet Ă„Ä…Ă˘â‚¬Âket vĂ„â€šĂ‹â€ˇsĂ„â€šĂ‹â€ˇrolni. A kĂ„â€šĂ„ËťlĂ„â€šĂ‚Â¶nbsĂ„â€šĂ‚Â©g kettejĂ„â€šĂ„Ëťk kĂ„â€šĂ‚Â¶zĂ„â€šĂ‚Â¶tt az, hogy:" +
                                "" +
                                "a FixMĂ„â€šĂ‚ÂP egĂ„â€šĂ‚Â©sz vĂ„â€šĂ‚Â©gig egysĂ„â€šĂ‚Â©gesen kamatozik Ă„â€šĂ‚Â©s negyedĂ„â€šĂ‚Â©vente fizet kamatot;" +
                                "" +
                                "a MĂ„â€šĂ‚ÂP Plusz kamatszintje fokozatosan, Ă„â€šĂ‚Â©vrĂ„Ä…Ă˘â‚¬Âl Ă„â€šĂ‚Â©vre nĂ„Ä…Ă˘â‚¬Â 0,25 szĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©kponttal, Ă„â€šĂ‚Â©s a kamatot visszaforgatja kĂ„â€šĂ‚Â¶zben sajĂ„â€šĂ‹â€ˇt magĂ„â€šĂ‹â€ˇba." +
                                "" +
                                "Az Ă„â€šĂ‚ÂKK bejelentĂ„â€šĂ‚Â©se szerint ezek a feltĂ„â€šĂ‚Â©telek nem vĂ„â€šĂ‹â€ˇltoznak, csak mindegyik fix kamatozĂ„â€šĂ‹â€ˇsĂ„â€šÄąĹş sorozat kamatszintje csĂ„â€šĂ‚Â¶kken." +
                                "" +
                                "A legtĂ„â€šĂ‚Â¶bb Ă„â€šĂ‹â€ˇllampapĂ„â€šĂ‚Â­rt idĂ„Ä…Ă˘â‚¬Â elĂ„Ä…Ă˘â‚¬Âtt egy egyszĂ„â€šĂ‹â€ˇzalĂ„â€šĂ‚Â©kos dĂ„â€šĂ‚Â­j ellenĂ„â€šĂ‚Â©ben lehet eladni. A MĂ„â€šĂ‚ÂP Plusznak ehhez kĂ„â€šĂ‚Â©pest van egy olyan elĂ„Ä…Ă˘â‚¬Ânye, hogy Ă„â€šĂ‚Â©vente egyszer, egy Ă„â€šĂ‚Â¶tnapos idĂ„Ä…Ă˘â‚¬Âtartamban ingyen vissza lehet vĂ„â€šĂ‹â€ˇltani. A mostani bejelentĂ„â€šĂ‚Â©ssel ezek a feltĂ„â€šĂ‚Â©telek sem vĂ„â€šĂ‹â€ˇltoznak." +
                                "" +
                                "Az inflĂ„â€šĂ‹â€ˇciĂ„â€šÄąâ€šhoz kĂ„â€šĂ‚Â¶tĂ„â€šĂ‚Â¶tt (prĂ„â€šĂ‚Â©mium Ă„â€šĂ‹â€ˇllampapĂ„â€šĂ‚Â­r) Ă„â€šĂ‚Â©s piaci folyamatokhoz kĂ„â€šĂ‚Â¶tĂ„â€šĂ‚Â¶tt (bĂ„â€šÄąâ€šnusz Ă„â€šĂ‹â€ˇllampapĂ„â€šĂ‚Â­r) kamatait a mostani bejelentĂ„â€šĂ‚Â©s nem Ă„â€šĂ‚Â©rinti." +
                                "" +
                                "A kamatcsĂ„â€šĂ‚Â¶kkentĂ„â€šĂ‚Â©st az Ă„â€šĂ‚ÂKK azzal magyarĂ„â€šĂ‹â€ˇzza, hogy az elmĂ„â€šÄąĹşlt idĂ„Ä…Ă˘â‚¬Âszakban jelentĂ„Ä…Ă˘â‚¬Âsen megvĂ„â€šĂ‹â€ˇltozott a magyarorszĂ„â€šĂ‹â€ˇgi kamatkĂ„â€šĂ‚Â¶rnyezet, Ă„â€šĂ‚Â©s a magyar Ă„â€šĂ‹â€ˇllam mind a kĂ„â€šĂ‚Â¶tvĂ„â€šĂ‚Â©nypiacon, mind a tĂ„â€šĂ‚Â¶bbi pĂ„â€šĂ‚Â©nzĂ„â€šĂ„Ëťgyi piacon a korĂ„â€šĂ‹â€ˇbbinĂ„â€šĂ‹â€ˇl alacsonyabb kamattal tud hitelt felvenni. BĂ„â€šĂ‹â€ˇr a kĂ„â€šĂ‚Â¶zlemĂ„â€šĂ‚Â©ny nem tĂ„â€šĂ‚Â©r ki erre, ennek az oka, hogy a kĂ„â€šĂ„ËťlfĂ„â€šĂ‚Â¶ldi befektetĂ„Ä…Ă˘â‚¬Âk sokkal szĂ„â€šĂ‚Â­vesebben adnak pĂ„â€šĂ‚Â©nzt az eurĂ„â€šÄąâ€š bevezetĂ„â€šĂ‚Â©sĂ„â€šĂ‚Â©t Ă„â€šĂ‚Â­gĂ„â€šĂ‚Â©rĂ„Ä…Ă˘â‚¬Â Magyar-kormĂ„â€šĂ‹â€ˇnynak, mint az OrbĂ„â€šĂ‹â€ˇn-kormĂ„â€šĂ‹â€ˇnynak."
                    )
                )
            )
        )
}