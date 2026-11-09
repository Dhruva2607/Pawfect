package com.pawfect.app.ui.screens.welcome

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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Pets
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.pawfect.app.ui.theme.BackgroundWarm

private const val WelcomePetImage =
    "https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=1200&q=85"

@Composable
fun WelcomeScreen(
    onGetStarted: () -> Unit,
    onSignUp: () -> Unit,
    onLogin: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize().background(BackgroundWarm),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Spacer(Modifier.height(24.dp))
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.primaryContainer) {
            Icon(
                Icons.Default.Pets,
                contentDescription = "PawFect",
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(14.dp)
            )
        }
        Spacer(Modifier.height(12.dp))
        Text("AI Pet Matchmaker", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text(
            "Find your perfect companion with a little help from AI",
            modifier = Modifier.padding(horizontal = 38.dp, vertical = 8.dp),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center
        )

        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 18.dp, vertical = 12.dp)
                .clip(RoundedCornerShape(34.dp))
        ) {
            AsyncImage(
                model = WelcomePetImage,
                contentDescription = "A happy dog ready to meet its new family",
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
            Box(
                modifier = Modifier.fillMaxSize().background(
                    Brush.verticalGradient(
                        colors = listOf(Color.Transparent, Color(0xAA13281B)),
                        startY = 250f
                    )
                )
            )
            Column(
                modifier = Modifier.align(Alignment.BottomStart).padding(24.dp)
            ) {
                Text(
                    "A best friend,\nmade for your life.",
                    style = MaterialTheme.typography.headlineLarge,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 38.sp
                )
                Text(
                    "Thoughtful matches. Happier homes.",
                    color = Color.White.copy(alpha = 0.9f),
                    modifier = Modifier.padding(top = 8.dp)
                )
            }
        }

        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Button(
                onClick = onGetStarted,
                modifier = Modifier.fillMaxWidth().height(54.dp),
                shape = RoundedCornerShape(28.dp),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
            ) {
                Text("Get started", fontWeight = FontWeight.SemiBold)
            }
            Spacer(Modifier.height(10.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedButton(
                    onClick = onSignUp,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(28.dp)
                ) { Text("Sign up") }
                OutlinedButton(
                    onClick = onLogin,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(28.dp)
                ) { Text("Log in") }
            }
        }
    }
}
