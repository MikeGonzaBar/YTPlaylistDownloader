import AppKit

enum AppIcon {
    @MainActor
    static func install() {
        guard let url = Bundle.module.url(forResource: "AppIcon", withExtension: "png"),
              let image = NSImage(contentsOf: url) else {
            return
        }

        image.size = NSSize(width: 512, height: 512)
        NSApplication.shared.applicationIconImage = image
    }
}
