package com.pawfect.app.ui.screens.shelter

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pawfect.app.data.model.PetDimensionOptionDto
import com.pawfect.app.data.model.ShelterPetCreateRequestDto
import com.pawfect.app.ui.components.PetImage
import com.pawfect.app.ui.viewmodel.ShelterPetFormViewModel
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun ShelterPetFormScreen(
    petId: String?,
    onBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: ShelterPetFormViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current

    LaunchedEffect(petId) { viewModel.initForm(petId) }
    LaunchedEffect(uiState.savedPetId) {
        if (uiState.savedPetId != null) onSaved()
    }

    var name by remember { mutableStateOf("") }
    var breed by remember { mutableStateOf("") }
    var ageMonthsText by remember { mutableStateOf("12") }
    var gender by remember { mutableStateOf("Female") }
    var bioText by remember { mutableStateOf("") }
    var exerciseNeeds by remember { mutableStateOf("") }
    var adoptionFeeText by remember { mutableStateOf("") }
    var idealAdopterNotes by remember { mutableStateOf("") }

    var species by remember { mutableStateOf("dog") }
    var size by remember { mutableStateOf("medium") }
    var energyLevel by remember { mutableFloatStateOf(3f) }
    var groomingNeeds by remember { mutableStateOf("low") }
    var sheddingLevel by remember { mutableStateOf("moderate") }
    var noiseLevel by remember { mutableStateOf("moderate") }
    var aloneTimeTolerance by remember { mutableStateOf("moderate") }
    var experienceRequired by remember { mutableStateOf("first_time_friendly") }
    var housingRequirement by remember { mutableStateOf("apartment_or_house") }
    var goodWithKids by remember { mutableStateOf(true) }
    var goodWithOtherPets by remember { mutableStateOf(true) }
    var hypoallergenic by remember { mutableStateOf(false) }
    var vaccinated by remember { mutableStateOf(true) }
    var neutered by remember { mutableStateOf(true) }

    var selectedPhotoUri by remember { mutableStateOf<Uri?>(null) }
    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        selectedPhotoUri = uri
    }

    // Populate when editing an existing pet
    LaunchedEffect(uiState.existingPet) {
        uiState.existingPet?.let { pet ->
            name = pet.name
            breed = pet.breed
            ageMonthsText = pet.ageMonths.toString()
            gender = pet.gender
            bioText = pet.bioText
            exerciseNeeds = pet.exerciseNeeds.orEmpty()
            adoptionFeeText = pet.adoptionFee?.toString().orEmpty()
            idealAdopterNotes = pet.idealAdopterNotes.orEmpty()
            species = pet.species
            size = pet.size
            energyLevel = pet.energyLevel.toFloat()
            groomingNeeds = pet.groomingNeeds ?: groomingNeeds
            sheddingLevel = pet.sheddingLevel ?: sheddingLevel
            noiseLevel = pet.noiseLevel ?: noiseLevel
            aloneTimeTolerance = pet.aloneTimeTolerance ?: aloneTimeTolerance
            experienceRequired = pet.experienceLevelRequired ?: experienceRequired
            housingRequirement = pet.housingRequirement
            goodWithKids = pet.goodWithKids
            goodWithOtherPets = pet.goodWithOtherPets
            hypoallergenic = pet.hypoallergenic
            vaccinated = pet.vaccinated ?: true
            neutered = pet.neutered ?: true
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (petId == null) "List a Pet" else "Edit Pet", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        if (uiState.isLoading) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = androidx.compose.ui.Alignment.Center) {
                CircularProgressIndicator()
            }
            return@Scaffold
        }

        val dims = uiState.options?.dimensions.orEmpty()

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Pet Name *") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            OutlinedTextField(
                value = breed,
                onValueChange = { breed = it },
                label = { Text("Breed *") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = ageMonthsText,
                    onValueChange = { ageMonthsText = it.filter(Char::isDigit) },
                    label = { Text("Age (months) *") },
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )
                Column(Modifier.weight(1f)) {
                    Text("Gender", style = MaterialTheme.typography.labelMedium)
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        listOf("Female", "Male").forEach { g ->
                            FilterChip(selected = gender == g, onClick = { gender = g }, label = { Text(g) })
                        }
                    }
                }
            }

            // Dynamic option selectors built from GET /meta/pet-options
            OptionChipSection("Species *", dims["species"], species) { species = it }
            OptionChipSection("Size *", dims["size"], size) { size = it }

            Column {
                Text("Energy Level: ${energyLevel.roundToInt()} / 5", style = MaterialTheme.typography.labelLarge)
                Slider(value = energyLevel, onValueChange = { energyLevel = it }, valueRange = 1f..5f, steps = 3)
            }

            OptionChipSection("Grooming Needs *", dims["grooming"], groomingNeeds) { groomingNeeds = it }
            OptionChipSection("Shedding Level *", dims["allergies"], sheddingLevel) { sheddingLevel = it }
            OptionChipSection("Noise Level *", dims["noise"], noiseLevel) { noiseLevel = it }
            OptionChipSection("Alone Time Tolerance *", dims["alone_time"], aloneTimeTolerance) { aloneTimeTolerance = it }
            OptionChipSection("Experience Required *", dims["experience"], experienceRequired) { experienceRequired = it }
            OptionChipSection("Housing Requirement *", dims["housing"], housingRequirement) { housingRequirement = it }

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Good with Children")
                Switch(checked = goodWithKids, onCheckedChange = { goodWithKids = it })
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Good with Other Pets")
                Switch(checked = goodWithOtherPets, onCheckedChange = { goodWithOtherPets = it })
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Hypoallergenic")
                Switch(checked = hypoallergenic, onCheckedChange = { hypoallergenic = it })
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Vaccinated")
                Switch(checked = vaccinated, onCheckedChange = { vaccinated = it })
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Spayed / Neutered")
                Switch(checked = neutered, onCheckedChange = { neutered = it })
            }

            OutlinedTextField(
                value = bioText,
                onValueChange = { bioText = it },
                label = { Text("Bio (min 20 chars for publishing) *") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3
            )
            OutlinedTextField(
                value = exerciseNeeds,
                onValueChange = { exerciseNeeds = it },
                label = { Text("Exercise Needs (optional)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            OutlinedTextField(
                value = adoptionFeeText,
                onValueChange = { adoptionFeeText = it },
                label = { Text("Adoption Fee (optional)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            OutlinedTextField(
                value = idealAdopterNotes,
                onValueChange = { idealAdopterNotes = it },
                label = { Text("Ideal Adopter Notes (optional)") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2
            )

            if (!uiState.existingPet?.photoUrl.isNullOrBlank() && selectedPhotoUri == null) {
                PetImage(
                    url = uiState.existingPet?.photoUrl,
                    contentDescription = name,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(180.dp)
                        .clip(RoundedCornerShape(14.dp))
                )
            }
            OutlinedButton(
                onClick = { photoPicker.launch("image/*") },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(if (selectedPhotoUri != null) "Photo selected ✓ (Tap to change)" else "Upload Pet Photo (optional)")
            }

            if (!uiState.error.isNullOrBlank()) {
                Text(uiState.error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }

            fun submit(targetStatus: String) {
                val bytes = selectedPhotoUri?.let { uri ->
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                }
                val mime = selectedPhotoUri?.let { context.contentResolver.getType(it) } ?: "image/jpeg"
                viewModel.savePet(
                    petId = petId,
                    request = ShelterPetCreateRequestDto(
                        name = name.trim(),
                        species = species,
                        breed = breed.trim(),
                        ageMonths = ageMonthsText.toIntOrNull() ?: 12,
                        gender = gender,
                        size = size,
                        energyLevel = energyLevel.roundToInt(),
                        groomingNeeds = groomingNeeds,
                        sheddingLevel = sheddingLevel,
                        noiseLevel = noiseLevel,
                        aloneTimeTolerance = aloneTimeTolerance,
                        experienceLevelRequired = experienceRequired,
                        goodWithKids = goodWithKids,
                        goodWithOtherPets = goodWithOtherPets,
                        housingRequirement = housingRequirement,
                        hypoallergenic = hypoallergenic,
                        bioText = bioText.trim(),
                        exerciseNeeds = exerciseNeeds.takeIf { it.isNotBlank() },
                        vaccinated = vaccinated,
                        neutered = neutered,
                        adoptionFee = adoptionFeeText.toDoubleOrNull(),
                        idealAdopterNotes = idealAdopterNotes.takeIf { it.isNotBlank() },
                        status = targetStatus
                    ),
                    photoBytes = bytes,
                    photoMimeType = mime
                )
            }

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = { submit("draft") },
                    enabled = !uiState.isSaving && name.isNotBlank() && breed.isNotBlank(),
                    modifier = Modifier.weight(1f).height(50.dp)
                ) {
                    Text("Save Draft")
                }
                Button(
                    onClick = { submit("available") },
                    enabled = !uiState.isSaving && name.isNotBlank() && breed.isNotBlank() && bioText.trim().length >= 20,
                    modifier = Modifier.weight(1f).height(50.dp)
                ) {
                    if (uiState.isSaving) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
                    else Text("Publish Pet")
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun OptionChipSection(
    title: String,
    option: PetDimensionOptionDto?,
    selected: String,
    onSelect: (String) -> Unit
) {
    val values = option?.allowedValues ?: return
    val labels = option.displayLabels
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, style = MaterialTheme.typography.labelLarge)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            values.forEach { value ->
                FilterChip(
                    selected = selected == value,
                    onClick = { onSelect(value) },
                    label = { Text(labels[value] ?: value) }
                )
            }
        }
    }
}
