package com.pawfect.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.pawfect.app.ui.navigation.PawFectMainScaffold
import com.pawfect.app.ui.theme.PawFectTheme
import dagger.hilt.android.AndroidEntryPoint

/**
 * Single activity entry point hosting the Jetpack Compose navigation graph.
 * [FROM MARKDOWN: Section 2 & Step 4.2]
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PawFectTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    PawFectMainScaffold()
                }
            }
        }
    }
}

