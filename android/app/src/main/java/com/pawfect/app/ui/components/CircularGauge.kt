package com.pawfect.app.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pawfect.app.ui.theme.MatchAmber
import com.pawfect.app.ui.theme.MatchGreen
import com.pawfect.app.ui.theme.MatchRed

/**
 * Circular Match Score Gauge.
 * Animated 0–100% arc with a tonal track and colour-coded score.
 */
@Composable
fun CircularMatchGauge(
    score: Int,
    modifier: Modifier = Modifier,
    size: Dp = 100.dp,
    strokeWidth: Dp = 8.dp
) {
    val safeScore = score.coerceIn(0, 100)
    val animatedProgress = remember { Animatable(0f) }
    LaunchedEffect(safeScore) {
        animatedProgress.animateTo(
            targetValue = safeScore / 100f,
            animationSpec = tween(durationMillis = 900, easing = FastOutSlowInEasing)
        )
    }

    val scoreColor = when {
        safeScore >= 85 -> MatchGreen
        safeScore >= 70 -> MatchAmber
        else -> MatchRed
    }
    val trackColor = MaterialTheme.colorScheme.surfaceVariant

    Box(modifier = modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawArc(
                color = trackColor,
                startAngle = -90f,
                sweepAngle = 360f,
                useCenter = false,
                style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
            )
            drawArc(
                color = scoreColor,
                startAngle = -90f,
                sweepAngle = 360f * animatedProgress.value,
                useCenter = false,
                style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
            )
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "$safeScore%",
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontSize = (size.value * 0.26).sp,
                    fontWeight = FontWeight.Bold
                ),
                color = scoreColor
            )
            Text(
                text = "match",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontSize = (size.value * 0.105).sp
                ),
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
