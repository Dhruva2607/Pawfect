package com.pawfect.app.ui.screens.profile

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForwardIos
import androidx.compose.material.icons.filled.BookmarkBorder
import androidx.compose.material.icons.filled.ChatBubbleOutline
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.Pets
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.local.UserSession
import com.pawfect.app.data.model.UserProfileDto
import com.pawfect.app.ui.viewmodel.ProfileViewModel

@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    onNavigateToMatches: () -> Unit,
    onNavigateToSavedPets: () -> Unit,
    onNavigateToChatHistory: () -> Unit,
    onLogout: () -> Unit,
    viewModel: ProfileViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var showSettings by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    val snackbarHost = remember { SnackbarHostState() }

    LaunchedEffect(uiState.message) {
        uiState.message?.let {
            snackbarHost.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My profile", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        snackbarHost = { SnackbarHost(snackbarHost) },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(20.dp)
        ) {
            ProfileHeader(uiState.profile, uiState.session, uiState.savedPets.size)
            Spacer(Modifier.height(24.dp))

            if (uiState.isLoading) {
                CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally))
                Spacer(Modifier.height(16.dp))
            }
            if (uiState.error != null) {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                    Column(Modifier.fillMaxWidth().padding(16.dp)) {
                        Text(uiState.error ?: "", color = MaterialTheme.colorScheme.onErrorContainer)
                        TextButton(onClick = viewModel::loadProfile) { Text("Try again") }
                    }
                }
                Spacer(Modifier.height(16.dp))
            }

            Text("Your adoption journey", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(10.dp))
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Column {
                    ProfileMenuItem(Icons.Default.FavoriteBorder, "My matches", "Your AI recommendations", onNavigateToMatches)
                    HorizontalDivider(Modifier.padding(horizontal = 16.dp))
                    ProfileMenuItem(Icons.Default.BookmarkBorder, "Saved pets", "${uiState.savedPets.size} companions saved", onNavigateToSavedPets)
                    HorizontalDivider(Modifier.padding(horizontal = 16.dp))
                    ProfileMenuItem(Icons.Default.ChatBubbleOutline, "Chat history", "Continue your matchmaker conversation", onNavigateToChatHistory)
                }
            }

            Spacer(Modifier.height(24.dp))
            Text("Account", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(10.dp))
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Column {
                    ProfileMenuItem(Icons.Default.Settings, "Lifestyle preferences", "Help us make thoughtful matches", { showSettings = true })
                    HorizontalDivider(Modifier.padding(horizontal = 16.dp))
                    ProfileMenuItem(Icons.Default.Info, "About PawFect", "AI-powered adoption, centered on you", { showAbout = true })
                }
            }
            Spacer(Modifier.height(20.dp))
            OutlinedButton(
                onClick = onLogout,
                modifier = Modifier.fillMaxWidth().height(52.dp),
                shape = RoundedCornerShape(28.dp)
            ) {
                Icon(Icons.AutoMirrored.Filled.Logout, contentDescription = null)
                Spacer(Modifier.size(8.dp))
                Text("Log out")
            }
            Spacer(Modifier.height(12.dp))
        }
    }

    if (showSettings) {
        PreferencesDialog(
            profile = uiState.profile,
            session = uiState.session,
            saving = uiState.isSaving,
            onDismiss = { showSettings = false },
            onSave = { name, email, housing, children, pets, energy ->
                viewModel.savePreferences(name, email, housing, children, pets, energy)
                showSettings = false
            }
        )
    }
    if (showAbout) {
        AlertDialog(
            onDismissRequest = { showAbout = false },
            icon = { Icon(Icons.Default.Pets, contentDescription = null) },
            title = { Text("PawFect") },
            text = { Text("A thoughtful AI pet matchmaker that helps adopters discover companions suited to their home, routine, and family.") },
            confirmButton = { TextButton(onClick = { showAbout = false }) { Text("Done") } }
        )
    }
}

@Composable
private fun ProfileHeader(profile: UserProfileDto?, session: UserSession?, savedCount: Int) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Row(
            Modifier.fillMaxWidth().padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(shape = CircleShape, color = MaterialTheme.colorScheme.surface) {
                Icon(
                    Icons.Default.Pets,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(16.dp).size(28.dp)
                )
            }
            Spacer(Modifier.size(16.dp))
            Column {
                Text(profile?.name ?: session?.name ?: "Adopter", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text(profile?.email ?: session?.email ?: "", style = MaterialTheme.typography.bodyMedium)
                Text("$savedCount saved pets", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

@Composable
private fun ProfileMenuItem(icon: ImageVector, title: String, subtitle: String, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(shape = RoundedCornerShape(12.dp), color = MaterialTheme.colorScheme.primaryContainer) {
            Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(10.dp).size(20.dp))
        }
        Spacer(Modifier.size(14.dp))
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Icon(Icons.AutoMirrored.Filled.ArrowForwardIos, contentDescription = null, tint = Color.LightGray, modifier = Modifier.size(14.dp))
    }
}

@Composable
private fun PreferencesDialog(
    profile: UserProfileDto?,
    session: UserSession?,
    saving: Boolean,
    onDismiss: () -> Unit,
    onSave: (String, String, String, Boolean, Boolean, Int) -> Unit
) {
    var name by remember(profile, session) { mutableStateOf(profile?.name ?: session?.name.orEmpty()) }
    var email by remember(profile, session) { mutableStateOf(profile?.email ?: session?.email.orEmpty()) }
    var housing by remember(profile, session) { mutableStateOf(profile?.housingType ?: session?.housingType ?: "apartment") }
    var children by remember(profile, session) { mutableStateOf(profile?.hasChildren ?: session?.hasChildren ?: false) }
    var otherPets by remember(profile, session) { mutableStateOf(profile?.hasOtherPets ?: session?.hasOtherPets ?: false) }
    var energy by remember(profile, session) { mutableFloatStateOf((profile?.energyBudget ?: session?.energyBudget ?: 3).toFloat()) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Lifestyle preferences") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                OutlinedTextField(name, { name = it }, label = { Text("Name") }, singleLine = true)
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(email, { email = it }, label = { Text("Email") }, singleLine = true)
                Spacer(Modifier.height(12.dp))
                Text("Home type", style = MaterialTheme.typography.labelLarge)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("apartment" to "Apartment", "house_with_yard" to "House with yard").forEach { (value, label) ->
                        if (housing == value) {
                            Button(onClick = { housing = value }) { Text(label) }
                        } else {
                            OutlinedButton(onClick = { housing = value }) { Text(label) }
                        }
                    }
                }
                PreferenceSwitch("Children at home", children) { children = it }
                PreferenceSwitch("Other pets at home", otherPets) { otherPets = it }
                Text("Activity level: ${energy.toInt()}/5")
                Slider(energy, onValueChange = { energy = it }, valueRange = 1f..5f, steps = 3)
            }
        },
        confirmButton = {
            Button(
                enabled = !saving,
                onClick = { onSave(name, email, housing, children, otherPets, energy.toInt()) }
            ) { Text(if (saving) "Saving…" else "Save") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}

@Composable
private fun PreferenceSwitch(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Switch(checked = checked, onCheckedChange = onChange)
    }
}
