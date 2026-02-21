package com.backlogai.shared

private const val defaultDesktopBaseUrl = "http://localhost:8001"

private fun resolveDesktopBaseUrl(): String {
    val envUrl = System.getenv("BACKLOGAI_BASE_URL")?.trim().orEmpty()
    if (envUrl.isNotEmpty()) {
        return envUrl
    }

    val propertyUrl = System.getProperty("backlogai.baseUrl")?.trim().orEmpty()
    if (propertyUrl.isNotEmpty()) {
        return propertyUrl
    }

    return defaultDesktopBaseUrl
}

actual val platformBaseUrl: String = resolveDesktopBaseUrl()
