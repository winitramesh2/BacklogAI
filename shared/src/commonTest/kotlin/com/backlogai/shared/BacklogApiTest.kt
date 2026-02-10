package com.backlogai.shared

import com.backlogai.shared.models.BacklogItemCreate
import com.backlogai.shared.models.PillarScores
import com.backlogai.shared.network.BacklogApi
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import io.ktor.utils.io.ByteReadChannel
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals

class BacklogApiTest {

    @Test
    fun testGenerateBacklogItemSuccess() = runTest {
        val mockEngine = MockEngine { request ->
            respond(
                content = ByteReadChannel("""
                    {
                      "id": "1d87cb97-d0f2-436b-8576-b2b03cd33b6e",
                      "title": "Test Feature",
                      "description": "As a user...",
                      "acceptance_criteria": ["Given x"],
                      "priority_score": 65.0,
                      "moscow_priority": "Should Have",
                      "pillar_scores": {
                        "user_value": 8.0,
                        "commercial_impact": 8.0,
                        "strategic_horizon": 5.0,
                        "competitive_positioning": 5.0,
                        "technical_reality": 5.0
                      },
                      "status": "draft",
                      "validation_warnings": []
                    }
                """.trimIndent()),
                status = HttpStatusCode.OK,
                headers = headersOf(HttpHeaders.ContentType, "application/json")
            )
        }

        val api = BacklogApi(baseUrl = "http://localhost", engine = mockEngine)
        val request = BacklogItemCreate(
            projectId = "123", 
            title = "Test Feature",
            description = "Desc",
            pillarScores = PillarScores()
        )

        val response = api.generateBacklogItem(request)
        
        assertEquals("Test Feature", response.title)
    }
}
