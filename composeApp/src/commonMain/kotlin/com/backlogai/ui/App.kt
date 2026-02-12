package com.backlogai.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import cafe.adriel.voyager.navigator.Navigator
import cafe.adriel.voyager.transitions.SlideTransition
import com.backlogai.ui.screens.InputScreen

@Composable
fun BacklogAiApp() {
    val colorScheme = lightColorScheme(
        primary = Color(0xFF0E4A5A),
        onPrimary = Color(0xFFF7FBFC),
        secondary = Color(0xFFB26E2B),
        onSecondary = Color(0xFFFCF6F0),
        tertiary = Color(0xFF2E6F59),
        onTertiary = Color(0xFFF2FBF6),
        background = Color(0xFFF7F4EE),
        onBackground = Color(0xFF1E1C19),
        surface = Color(0xFFFDFBF7),
        onSurface = Color(0xFF24211E),
        surfaceVariant = Color(0xFFECE3D6),
        onSurfaceVariant = Color(0xFF3B342B),
        outline = Color(0xFFC9B79F)
    )

    val typography = Typography(
        displayLarge = TextStyle(
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.Bold,
            fontSize = 32.sp,
            letterSpacing = 0.4.sp
        ),
        headlineMedium = TextStyle(
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.SemiBold,
            fontSize = 22.sp
        ),
        titleLarge = TextStyle(
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.SemiBold,
            fontSize = 18.sp
        ),
        titleMedium = TextStyle(
            fontFamily = FontFamily.SansSerif,
            fontWeight = FontWeight.SemiBold,
            fontSize = 16.sp
        ),
        bodyLarge = TextStyle(
            fontFamily = FontFamily.SansSerif,
            fontWeight = FontWeight.Normal,
            fontSize = 15.sp,
            lineHeight = 22.sp
        ),
        bodyMedium = TextStyle(
            fontFamily = FontFamily.SansSerif,
            fontWeight = FontWeight.Normal,
            fontSize = 13.sp,
            lineHeight = 20.sp
        ),
        labelLarge = TextStyle(
            fontFamily = FontFamily.SansSerif,
            fontWeight = FontWeight.Medium,
            fontSize = 12.sp,
            letterSpacing = 0.3.sp
        )
    )

    MaterialTheme(
        colorScheme = colorScheme,
        typography = typography
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
