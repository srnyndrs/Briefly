package com.srnyndrs.android.briefly.data.remote.content

import com.srnyndrs.android.briefly.data.remote.content.dto.ExploreRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.FeedRequestDto
import com.srnyndrs.android.briefly.data.remote.content.dto.PersonalFeedResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.PostResponseDto
import com.srnyndrs.android.briefly.data.remote.content.dto.PostSummaryResponseDto
import com.srnyndrs.android.briefly.data.remote.profile.toPatchDto
import com.srnyndrs.android.briefly.domain.model.profile.ProfilePreferences
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.time.ExperimentalTime

@OptIn(ExperimentalTime::class)
class ContentCategoryContractTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun summaryPreservesBothCategories() {
        val post = json.decodeFromString<PostSummaryResponseDto>(
            """{"post_id":"one","title":"Research","published_at":null,
                "has_content":true,"categories":["science","health"]}""",
        ).toDomain()

        assertEquals(listOf("science", "health"), post.categories)
        assertTrue(post.hasContent)
    }

    @Test
    fun unenrichedSummaryKeepsExternalArticleReadable() {
        val post = json.decodeFromString<PostSummaryResponseDto>(
            """{"post_id":"one","title":"Article","published_at":null,
                "has_content":false,"categories":[],"source_category":"Publisher label",
                "canonical_url":"https://example.com/article"}""",
        ).toDomain()

        assertTrue(post.categories.isEmpty())
        assertEquals("Article", post.title)
        assertEquals("https://example.com/article", post.url)
        assertFalse(post.hasContent)
    }

    @Test
    fun missingCategoriesDefaultToEmpty() {
        val summary = json.decodeFromString<PostSummaryResponseDto>(
            """{"post_id":"one","title":"Article","published_at":null,"has_content":true}""",
        ).toDomain()
        val detail = json.decodeFromString<PostResponseDto>(
            """{"post_id":"one","title":"Article","published_at":null,"content":"Body"}""",
        ).toDomain()

        assertTrue(summary.categories.isEmpty())
        assertTrue(detail.categories.isEmpty())
        assertEquals("Body", detail.content)
    }

    @Test
    fun detailsPreserveEmptyAndMultipleCategories() {
        for (categories in listOf(emptyList(), listOf("science", "health"))) {
            val payload = PostResponseDto(
                postId = "one",
                title = "Article",
                publishedAt = null,
                content = "Readable body",
                categories = categories,
            )
            val article = json.decodeFromString<PostResponseDto>(json.encodeToString(payload)).toDomain()

            assertEquals(categories, article.categories)
            assertEquals("Readable body", article.content)
        }
    }

    @Test
    fun headlinesAndFeedItemsUseCategoryLists() {
        val feed = json.decodeFromString<PersonalFeedResponseDto>(
            """{"total":1,"headlines":[{"post_id":"headline","title":"Headline",
                "published_at":null,"has_content":true,"categories":["science","health"]}],
                "items":[{"post_id":"article","title":"Article","published_at":null,
                "has_content":true,"categories":[]}]}""",
        )

        assertEquals(listOf("science", "health"), feed.headlines!!.single().toDomain().categories)
        assertTrue(feed.items.single().toDomain().categories.isEmpty())
    }

    @Test
    fun filterRequestsKeepTheCurrentApiParameters() {
        val home = json.parseToJsonElement(json.encodeToString(FeedRequestDto(category = "health"))).jsonObject
        val explore = json.parseToJsonElement(
            json.encodeToString(ExploreRequestDto(categories = listOf("science", "health"))),
        ).jsonObject

        assertEquals("health", home.getValue("category").jsonPrimitive.content)
        assertEquals(
            listOf("science", "health"),
            explore.getValue("categories").jsonArray.map { it.jsonPrimitive.content },
        )
    }

    @Test
    fun muteRequestsPreserveEverySelectedCategory() {
        val preferences = ProfilePreferences(
            mutedKeywords = emptyList(),
            mutedCategories = listOf("science", "health"),
            blockedSourceIds = emptySet(),
            languages = emptySet(),
        )
        val payload = json.parseToJsonElement(json.encodeToString(preferences.toPatchDto())).jsonObject

        assertEquals(
            listOf("science", "health"),
            payload.getValue("muted_categories").jsonArray.map { it.jsonPrimitive.content },
        )
    }
}
