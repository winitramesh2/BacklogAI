package com.backlogai.shared.network

import com.backlogai.shared.models.BacklogItemCreate
import com.backlogai.shared.models.BacklogItemResponse
import com.backlogai.shared.models.BacklogItemSyncResponse
import com.backlogai.shared.models.JiraSyncRequest
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

import com.backlogai.shared.platformBaseUrl

class BacklogApi(
    private val baseUrl: String = platformBaseUrl
) {
    private val client = HttpClient {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                ignoreUnknownKeys = true
            })
        }
    }

    suspend fun healthCheck(): Boolean {
        return try {
            val response = client.get("$baseUrl/health")
            response.status.value == 200
        } catch (e: Exception) {
            println("Health Check Failed: $e")
            false
        }
    }

    suspend fun generateBacklogItem(request: BacklogItemCreate): BacklogItemResponse {
        return client.post("$baseUrl/backlog/generate") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }

    suspend fun syncToJira(request: JiraSyncRequest): BacklogItemSyncResponse {
        return client.post("$baseUrl/backlog/sync") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }
}
