import AppKit
import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let swiftResourceDir = root.appendingPathComponent(
    "macos/PlaylistFolderDownloader/Sources/PlaylistFolderDownloader/Resources",
    isDirectory: true
)
let iconsetDir = swiftResourceDir.appendingPathComponent("AppIcon.iconset", isDirectory: true)
let pythonAssetDir = root.appendingPathComponent(
    "src/playlist_folder_downloader/assets",
    isDirectory: true
)

try FileManager.default.createDirectory(at: swiftResourceDir, withIntermediateDirectories: true)
try FileManager.default.createDirectory(at: iconsetDir, withIntermediateDirectories: true)
try FileManager.default.createDirectory(at: pythonAssetDir, withIntermediateDirectories: true)

func removeIfPresent(_ url: URL) throws {
    if FileManager.default.fileExists(atPath: url.path) {
        try FileManager.default.removeItem(at: url)
    }
}

func roundedRect(_ rect: CGRect, radius: CGFloat) -> NSBezierPath {
    NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
}

func drawTriangle(points: [CGPoint], color: NSColor) {
    let path = NSBezierPath()
    path.move(to: points[0])
    path.line(to: points[1])
    path.line(to: points[2])
    path.close()
    color.setFill()
    path.fill()
}

func drawLine(from start: CGPoint, to end: CGPoint, width: CGFloat, color: NSColor) {
    let path = NSBezierPath()
    path.lineCapStyle = .round
    path.lineJoinStyle = .round
    path.lineWidth = width
    path.move(to: start)
    path.line(to: end)
    color.setStroke()
    path.stroke()
}

func drawIconArtwork() {
    let baseRect = CGRect(x: 132, y: 132, width: 760, height: 760)
    let basePath = roundedRect(baseRect, radius: 160)

    NSGraphicsContext.saveGraphicsState()
    let outerShadow = NSShadow()
    outerShadow.shadowBlurRadius = 34
    outerShadow.shadowOffset = NSSize(width: 0, height: -18)
    outerShadow.shadowColor = NSColor.black.withAlphaComponent(0.18)
    outerShadow.set()
    NSColor.white.withAlphaComponent(0.94).setFill()
    basePath.fill()
    NSGraphicsContext.restoreGraphicsState()

    NSGradient(colors: [
        NSColor(calibratedRed: 1.0, green: 1.0, blue: 1.0, alpha: 0.96),
        NSColor(calibratedRed: 0.91, green: 0.95, blue: 1.0, alpha: 0.94),
        NSColor(calibratedRed: 0.84, green: 0.90, blue: 1.0, alpha: 0.92),
    ])?.draw(in: basePath, angle: -42)

    NSColor.white.withAlphaComponent(0.66).setStroke()
    basePath.lineWidth = 4
    basePath.stroke()

    let videoRect = CGRect(x: 248, y: 530, width: 360, height: 230)
    let videoPath = roundedRect(videoRect, radius: 58)

    NSGraphicsContext.saveGraphicsState()
    let redShadow = NSShadow()
    redShadow.shadowBlurRadius = 22
    redShadow.shadowOffset = NSSize(width: 0, height: -10)
    redShadow.shadowColor = NSColor(calibratedRed: 1.0, green: 0.10, blue: 0.10, alpha: 0.28)
    redShadow.set()
    NSColor(calibratedRed: 1.0, green: 0.16, blue: 0.14, alpha: 1.0).setFill()
    videoPath.fill()
    NSGraphicsContext.restoreGraphicsState()

    NSGradient(colors: [
        NSColor(calibratedRed: 1.0, green: 0.28, blue: 0.28, alpha: 1.0),
        NSColor(calibratedRed: 0.96, green: 0.10, blue: 0.10, alpha: 1.0),
    ])?.draw(in: videoPath, angle: -55)

    drawTriangle(
        points: [
            CGPoint(x: 394, y: 634),
            CGPoint(x: 394, y: 728),
            CGPoint(x: 492, y: 681),
        ],
        color: NSColor.white.withAlphaComponent(0.94)
    )

    let lineColor = NSColor(calibratedRed: 0.58, green: 0.64, blue: 0.75, alpha: 0.52)
    for y in [700.0, 626.0, 552.0] {
        let line = roundedRect(CGRect(x: 628, y: y, width: 220, height: 34), radius: 17)
        NSGradient(colors: [
            lineColor.withAlphaComponent(0.36),
            lineColor.withAlphaComponent(0.62),
        ])?.draw(in: line, angle: 0)
    }

    let folderBack = NSBezierPath()
    folderBack.move(to: CGPoint(x: 304, y: 290))
    folderBack.line(to: CGPoint(x: 304, y: 566))
    folderBack.curve(to: CGPoint(x: 362, y: 624), controlPoint1: CGPoint(x: 304, y: 598), controlPoint2: CGPoint(x: 330, y: 624))
    folderBack.line(to: CGPoint(x: 484, y: 624))
    folderBack.curve(to: CGPoint(x: 540, y: 590), controlPoint1: CGPoint(x: 510, y: 624), controlPoint2: CGPoint(x: 516, y: 590))
    folderBack.line(to: CGPoint(x: 760, y: 590))
    folderBack.curve(to: CGPoint(x: 824, y: 526), controlPoint1: CGPoint(x: 796, y: 590), controlPoint2: CGPoint(x: 824, y: 562))
    folderBack.line(to: CGPoint(x: 824, y: 290))
    folderBack.close()

    NSGraphicsContext.saveGraphicsState()
    let blueShadow = NSShadow()
    blueShadow.shadowBlurRadius = 26
    blueShadow.shadowOffset = NSSize(width: 0, height: -12)
    blueShadow.shadowColor = NSColor(calibratedRed: 0.30, green: 0.53, blue: 1.0, alpha: 0.34)
    blueShadow.set()
    NSColor(calibratedRed: 0.48, green: 0.66, blue: 1.0, alpha: 1.0).setFill()
    folderBack.fill()
    NSGraphicsContext.restoreGraphicsState()

    NSGradient(colors: [
        NSColor(calibratedRed: 0.70, green: 0.80, blue: 1.0, alpha: 1.0),
        NSColor(calibratedRed: 0.35, green: 0.60, blue: 1.0, alpha: 1.0),
    ])?.draw(in: folderBack, angle: -45)

    let folderFront = roundedRect(CGRect(x: 326, y: 238, width: 524, height: 286), radius: 62)
    NSGradient(colors: [
        NSColor(calibratedRed: 0.76, green: 0.84, blue: 1.0, alpha: 0.98),
        NSColor(calibratedRed: 0.42, green: 0.66, blue: 1.0, alpha: 0.98),
    ])?.draw(in: folderFront, angle: -40)
    NSColor.white.withAlphaComponent(0.48).setStroke()
    folderFront.lineWidth = 4
    folderFront.stroke()

    let white = NSColor.white.withAlphaComponent(0.96)
    drawLine(from: CGPoint(x: 588, y: 450), to: CGPoint(x: 588, y: 330), width: 28, color: white)
    drawLine(from: CGPoint(x: 588, y: 330), to: CGPoint(x: 532, y: 386), width: 28, color: white)
    drawLine(from: CGPoint(x: 588, y: 330), to: CGPoint(x: 644, y: 386), width: 28, color: white)
    drawLine(from: CGPoint(x: 516, y: 280), to: CGPoint(x: 660, y: 280), width: 26, color: white)
    drawLine(from: CGPoint(x: 516, y: 280), to: CGPoint(x: 516, y: 302), width: 26, color: white)
    drawLine(from: CGPoint(x: 660, y: 280), to: CGPoint(x: 660, y: 302), width: 26, color: white)
}

func renderIconRep(size: CGFloat) throws -> NSBitmapImageRep {
    guard let bitmap = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(size),
        pixelsHigh: Int(size),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bitmapFormat: [],
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else {
        throw NSError(domain: "IconGeneration", code: 1)
    }

    bitmap.size = NSSize(width: size, height: size)
    guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
        throw NSError(domain: "IconGeneration", code: 2)
    }

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    context.imageInterpolation = .high
    context.cgContext.clear(CGRect(x: 0, y: 0, width: size, height: size))
    context.cgContext.scaleBy(x: size / 1024.0, y: size / 1024.0)
    drawIconArtwork()
    NSGraphicsContext.restoreGraphicsState()
    return bitmap
}

func writePNG(size: CGFloat, to url: URL) throws {
    let bitmap = try renderIconRep(size: size)
    guard let png = bitmap.representation(using: .png, properties: [:]) else {
        throw NSError(domain: "IconGeneration", code: 3)
    }
    try png.write(to: url)
}

let iconFiles: [(String, CGFloat)] = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]

for (name, size) in iconFiles {
    try writePNG(size: size, to: iconsetDir.appendingPathComponent(name))
}

let fullSizePNG = swiftResourceDir.appendingPathComponent("AppIcon.png")
try writePNG(size: 1024, to: fullSizePNG)
try removeIfPresent(pythonAssetDir.appendingPathComponent("app_icon.png"))
try FileManager.default.copyItem(
    at: fullSizePNG,
    to: pythonAssetDir.appendingPathComponent("app_icon.png")
)

let icnsURL = swiftResourceDir.appendingPathComponent("AppIcon.icns")
try removeIfPresent(icnsURL)

let iconutil = Process()
iconutil.executableURL = URL(fileURLWithPath: "/usr/bin/iconutil")
iconutil.arguments = [
    "-c",
    "icns",
    iconsetDir.path,
    "-o",
    icnsURL.path,
]
try iconutil.run()
iconutil.waitUntilExit()
if iconutil.terminationStatus != 0 {
    throw NSError(domain: "IconGeneration", code: Int(iconutil.terminationStatus))
}

print("Generated app icon assets in \(swiftResourceDir.path)")
