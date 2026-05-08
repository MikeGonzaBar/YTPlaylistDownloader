// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "PlaylistFolderDownloader",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "PlaylistFolderDownloader", targets: ["PlaylistFolderDownloader"])
    ],
    targets: [
        .executableTarget(
            name: "PlaylistFolderDownloader",
            resources: [
                .process("Resources")
            ]
        )
    ]
)
