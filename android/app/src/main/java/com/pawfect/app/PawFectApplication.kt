package com.pawfect.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * PawFect Application entry point with Hilt dependency injection.
 * [FROM MARKDOWN: Section 2 & Step 4.1]
 */
@HiltAndroidApp
class PawFectApplication : Application()

