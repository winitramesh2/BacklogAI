package com.backlogai.shared.network

import com.backlogai.shared.models.BacklogItemCreate
import com.backlogai.shared.models.BacklogItemResponse
import com.backlogai.shared.models.BacklogItemGenerateV2Request
import com.backlogai.shared.models.BacklogItemGenerateV2Response
import com.backlogai.shared.models.BacklogItemSyncResponse
import com.backlogai.shared.models.JiraSyncRequest
import com.backlogai.shared.models.JiraSyncRequestV2
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

import io.ktor.client.engine.HttpClientEngine
import io.ktor.client.statement.bodyAsText
import io.ktor.http.isSuccess

import com.backlogai.shared.platformBaseUrl

class BacklogApi(
    private val baseUrl: String = platformBaseUrl,
    engine: HttpClientEngine? = null
) {
    private val client = if (engine != null) {
        HttpClient(engine) {
            install(ContentNegotiation) {
                json(Json {
                    prettyPrint = true
                    ignoreUnknownKeys = true
                })
            }
        }
    } else {
        HttpClient {
            install(ContentNegotiation) {
                json(Json {
                    prettyPrint = true
                    ignoreUnknownKeys = true
                })
            }
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
        val response = client.post("$baseUrl/backlog/generate") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        
        if (!response.status.isSuccess()) {
            val errorBody = response.bodyAsText()
            throw Exception("API Error ${response.status.value}: $errorBody")
        }
        
        return response.body()
    }

    suspend fun syncToJira(request: JiraSyncRequest): BacklogItemSyncResponse {
        val response = client.post("$baseUrl/backlog/sync") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        
        if (!response.status.isSuccess()) {
            val errorBody = response.bodyAsText()
            throw Exception("API Error ${response.status.value}: $errorBody")
        }
        
        return response.body()
    }

    suspend fun generateBacklogItemV2(request: BacklogItemGenerateV2Request): BacklogItemGenerateV2Response {
        val response = client.post("$baseUrl/backlog/generate/v2") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }

        if (!response.status.isSuccess()) {
            val errorBody = response.bodyAsText()
            throw Exception("API Error ${response.status.value}: $errorBody")
        }

        return response.body()
    }

    suspend fun syncToJiraV2(request: JiraSyncRequestV2): BacklogItemSyncResponse {
        val response = client.post("$baseUrl/backlog/sync/v2") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }

        if (!response.status.isSuccess()) {
            val errorBody = response.bodyAsText()
            throw Exception("API Error ${response.status.value}: $errorBody")
        }

        return response.body()
    }
}
