package com.pawfect.app.ui.components

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Pets
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.pawfect.app.BuildConfig

/**
 * PawFect's brand mark: a soft paw printed in the current accent.
 * Drawn in canvas so it scales crisply everywhere without an asset.
 */
@Composable
fun PawLogo(
    modifier: Modifier = Modifier,
    tint: Color = MaterialTheme.colorScheme.primary
) {
    Canvas(modifier = modifier) {
        val w = size.width
        val h = size.height
        drawOval(
            color = tint,
            topLeft = Offset(w * 0.20f, h * 0.46f),
            size = Size(w * 0.60f, h * 0.44f)
        )
        val radius = w * 0.105f
        drawCircle(tint, radius, Offset(w * 0.24f, h * 0.33f))
        drawCircle(tint, radius, Offset(w * 0.41f, h * 0.20f))
        drawCircle(tint, radius, Offset(w * 0.59f, h * 0.20f))
        drawCircle(tint, radius, Offset(w * 0.76f, h * 0.33f))
    }
}

/** A pet photo that always renders something warm, even if the URL is missing or fails. */
@Composable
fun PetImage(
    url: String?,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    contentScale: ContentScale = ContentScale.Crop
) {
    val context = LocalContext.current
    val fullUrl = remember(url) {
        val sanitized = when {
            url.isNullOrBlank() -> null
            url.contains("photo-1513360309081-38a60b9d997c") -> "https://images.unsplash.com/photo-1533743983669-94fa5c4338ec"
            url.contains("photo-1529429617124-95b104e86bcd") -> "https://images.unsplash.com/photo-1587300003388-59208cc962cb"
            else -> url
        }

        if (sanitized == null) null
        else if (sanitized.startsWith("http://") || sanitized.startsWith("https://")) {
            if (sanitized.contains("unsplash.com") && !sanitized.contains("w=")) {
                val sep = if (sanitized.contains("?")) "&" else "?"
                "$sanitized${sep}auto=format&fit=crop&w=800&q=80"
            } else {
                sanitized
            }
        } else {
            val base = BuildConfig.API_BASE_URL.removeSuffix("api/v1/").removeSuffix("/")
            val path = if (sanitized.startsWith("/")) sanitized else "/$sanitized"
            "$base$path"
        }
    }

    Box(
        modifier = modifier.background(
            Brush.linearGradient(
                listOf(
                    MaterialTheme.colorScheme.primaryContainer,
                    MaterialTheme.colorScheme.secondaryContainer
                )
            )
        )
    ) {
        PawLogo(
            modifier = Modifier
                .align(Alignment.Center)
                .size(36.dp),
            tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.32f)
        )
        if (!fullUrl.isNullOrBlank()) {
            AsyncImage(
                model = ImageRequest.Builder(context)
                    .data(fullUrl)
                    .crossfade(true)
                    .build(),
                contentDescription = contentDescription,
                contentScale = contentScale,
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}

@Composable
fun PawSectionHeader(
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.headlineSmall)
            if (subtitle != null) {
                Spacer(Modifier.height(2.dp))
                Text(
                    subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        if (actionLabel != null && onAction != null) {
            TextButton(onClick = onAction) { Text(actionLabel) }
        }
    }
}

@Composable
fun PawTag(
    text: String,
    modifier: Modifier = Modifier,
    container: Color = MaterialTheme.colorScheme.surfaceVariant
) {
    Surface(modifier = modifier, shape = MaterialTheme.shapes.small, color = container) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
        )
    }
}

@Composable
fun PawEmptyState(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
    icon: ImageVector = Icons.Filled.Pets,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 32.dp, vertical = 40.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier
                    .padding(18.dp)
                    .size(28.dp)
            )
        }
        Spacer(Modifier.height(16.dp))
        Text(title, style = MaterialTheme.typography.titleLarge, textAlign = TextAlign.Center)
        Spacer(Modifier.height(6.dp))
        Text(
            message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        if (actionLabel != null && onAction != null) {
            Spacer(Modifier.height(18.dp))
            Button(onClick = onAction, shape = MaterialTheme.shapes.medium) {
                Text(actionLabel)
            }
        }
    }
}

@Composable
fun PawErrorState(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    PawEmptyState(
        title = "Something went wrong",
        message = message,
        modifier = modifier,
        icon = Icons.Filled.Warning,
        actionLabel = "Try again",
        onAction = onRetry
    )
}

/** Pulsing placeholder used while content loads, instead of a bare spinner. */
@Composable
fun PawSkeleton(
    modifier: Modifier = Modifier,
    shape: Shape = RoundedCornerShape(16.dp)
) {
    val transition = rememberInfiniteTransition(label = "skeleton")
    val alpha by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 0.75f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "skeletonAlpha"
    )
    Box(
        modifier = modifier.background(
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = alpha),
            shape = shape
        )
    )
}
