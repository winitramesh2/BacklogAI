package com.backlogai.ui

import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.WindowPosition
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import java.awt.Dimension

fun main() = application {
    val windowState = rememberWindowState(
        position = WindowPosition.Aligned(Alignment.Center),
        size = DpSize(1200.dp, 840.dp)
    )

    Window(
        onCloseRequest = ::exitApplication,
        title = "BacklogAI",
        state = windowState
    ) {
        LaunchedEffect(Unit) {
            window.minimumSize = Dimension(980, 700)
        }

        BacklogAiApp()
    }
}
