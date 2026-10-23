package com.srnyndrs.android.briefly.domain.model.content.source

data class SourceDiscoveryResult(
    val id: String,
    val url: String,
    val title: String,
    val faviconUrl: String? = null,
    val description: String? = null,
    val isSubscribed: Boolean = false,
)
