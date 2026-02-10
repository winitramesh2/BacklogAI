package com.backlogai.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import cafe.adriel.voyager.navigator.Navigator
import cafe.adriel.voyager.transitions.SlideTransition
import com.backlogai.ui.screens.InputScreen

@Composable
fun BacklogAiApp() {
    MaterialTheme(
        colorScheme = lightColorScheme()
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background
        ) {
            Navigator(InputScreen()) { navigator ->
                SlideTransition(navigator)
            }
        }
    }
}
