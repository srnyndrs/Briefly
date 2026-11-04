package com.srnyndrs.android.briefly.domain.model.content.source

data class SourceDiscoveryResult(
    val url: String,
    val title: String,
    val faviconUrl: String? = null,
    val description: String? = null,
    val siteUrl: String? = null,
    val siteName: String? = null,
    val language: String? = null,
)
