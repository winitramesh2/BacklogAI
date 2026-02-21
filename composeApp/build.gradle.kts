import org.gradle.api.tasks.Copy
import org.gradle.api.tasks.bundling.Zip

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.jetbrainsCompose)
    alias(libs.plugins.composeCompiler)
}

kotlin {
    applyDefaultHierarchyTemplate()
    
    androidTarget {
        compilations.all {
            kotlinOptions {
                jvmTarget = "17"
            }
        }
    }
    
    jvm("desktop")
    
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "ComposeApp"
            isStatic = true
        }
    }
    
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(compose.runtime)
                implementation(compose.foundation)
                implementation(compose.material3)
                implementation(compose.ui)
                implementation(compose.components.resources)
                implementation(compose.components.uiToolingPreview)
                
                // Navigation
                implementation(libs.voyager.navigator)
                implementation(libs.voyager.screenmodel)
                implementation(libs.voyager.transitions)
                
                // Coroutines
                implementation(libs.kotlinx.coroutines.core)
                
                // Shared Logic
                implementation(project(":shared"))
            }
        }
        
        val androidMain by getting {
            dependencies {
                implementation(libs.androidx.activity.compose)
                implementation(libs.kotlinx.coroutines.android)
            }
        }
        
        val iosMain by getting
        val desktopMain by getting {
            dependencies {
                implementation(compose.desktop.currentOs)
                implementation(libs.kotlinx.coroutines.swing)
            }
        }
    }
}

android {
    namespace = "com.backlogai.ui"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.backlogai.ui"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        compose = true
    }
    dependencies {
        debugImplementation(libs.compose.ui.tooling)
    }
}

compose.desktop {
    application {
        mainClass = "com.backlogai.ui.MainKt"
        nativeDistributions {
            targetFormats(org.jetbrains.compose.desktop.application.dsl.TargetFormat.Dmg, org.jetbrains.compose.desktop.application.dsl.TargetFormat.Msi, org.jetbrains.compose.desktop.application.dsl.TargetFormat.Deb)
            packageName = "BackLogAI"
            packageVersion = "1.0.0"
        }
    }
}

val isWindowsHost = System.getProperty("os.name").contains("windows", ignoreCase = true)

tasks.register<Zip>("packageWindowsPortableZip") {
    group = "distribution"
    description = "Packages portable Windows ZIP from distributable app image"
    dependsOn("createDistributable")
    from(layout.buildDirectory.dir("compose/binaries/main/app/BackLogAI"))
    archiveFileName.set("BackLogAI-windows-portable.zip")
    destinationDirectory.set(layout.buildDirectory.dir("compose/binaries/main/windowsPortable"))
    onlyIf { isWindowsHost }
}

tasks.register<Copy>("publishWindowsBinariesToDemo") {
    group = "distribution"
    description = "Copies MSI and portable ZIP to demo binaries folder"
    dependsOn("packageMsi", "packageWindowsPortableZip")
    into(rootProject.layout.projectDirectory.dir("demo/binaries-v3/windows"))
    from(layout.buildDirectory.dir("compose/binaries/main/msi")) {
        include("*.msi")
    }
    from(layout.buildDirectory.dir("compose/binaries/main/windowsPortable")) {
        include("BackLogAI-windows-portable.zip")
    }
    onlyIf { isWindowsHost }
}
