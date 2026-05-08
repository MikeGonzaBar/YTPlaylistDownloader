import AppKit
import SwiftUI

@main
struct PlaylistFolderDownloaderApp: App {
    init() {
        NSApplication.shared.setActivationPolicy(.regular)
        AppIcon.install()
        DispatchQueue.main.async {
            NSApplication.shared.activate(ignoringOtherApps: true)
        }
    }

    var body: some Scene {
        WindowGroup("Playlist Folder Downloader") {
            ContentView()
        }
        .windowStyle(.hiddenTitleBar)
    }
}
