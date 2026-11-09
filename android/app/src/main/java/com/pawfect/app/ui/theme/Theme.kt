package com.pawfect.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColorScheme = lightColorScheme(
    primary = PrimaryAmber,
    onPrimary = SurfaceWarm,
    secondary = SecondaryTeal,
    onSecondary = SurfaceWarm,
    tertiary = AccentCoral,
    primaryContainer = Color(0xFFE1EAD6),
    onPrimaryContainer = Color(0xFF1B3F2B),
    background = BackgroundWarm,
    surface = SurfaceWarm,
    surfaceVariant = SurfaceVariantWarm,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    onSurfaceVariant = TextSecondary
)

@Composable
fun PawFectTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        content = content
    )
}
