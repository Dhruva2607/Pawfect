package com.pawfect.app.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

private val LightColorScheme = lightColorScheme(
    primary = Pine700,
    onPrimary = Color(0xFFFFFBF4),
    primaryContainer = Pine100,
    onPrimaryContainer = Pine900,
    secondary = Clay600,
    onSecondary = Color(0xFFFFFBF6),
    secondaryContainer = Clay100,
    onSecondaryContainer = Color(0xFF4A1F14),
    tertiary = Honey700,
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Honey100,
    onTertiaryContainer = Color(0xFF3A2A0C),
    background = Sand050,
    onBackground = Ink900,
    surface = Paper,
    onSurface = Ink900,
    surfaceVariant = Sand100,
    onSurfaceVariant = Ink500,
    surfaceTint = Pine700,
    outline = Color(0xFFCBBFAE),
    outlineVariant = Color(0xFFE6DCCD),
    error = Color(0xFFB3261E),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFF9DEDC),
    onErrorContainer = Color(0xFF410E0B),
    inverseSurface = Color(0xFF303B33),
    inverseOnSurface = Color(0xFFF4F1EA),
    scrim = Color(0xFF000000)
)

// A clear radius hierarchy: fields are tight, cards are soft,
// hero surfaces are generous. Nothing defaults to "maximum round".
val PawFectShapes = Shapes(
    extraSmall = RoundedCornerShape(8.dp),
    small = RoundedCornerShape(12.dp),
    medium = RoundedCornerShape(16.dp),
    large = RoundedCornerShape(22.dp),
    extraLarge = RoundedCornerShape(30.dp)
)

@Composable
fun PawFectTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        shapes = PawFectShapes,
        content = content
    )
}
