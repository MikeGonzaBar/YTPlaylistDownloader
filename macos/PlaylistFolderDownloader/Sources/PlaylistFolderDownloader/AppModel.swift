import Foundation
import SwiftUI

@MainActor
final class AppModel: ObservableObject {
    @Published var url = ""
    @Published var playlist: PlaylistInfo?
    @Published var videos: [VideoInfo] = []
    @Published var selectedIDs: Set<String> = []
    @Published var focusedID: String?
    @Published var statusByID: [String: String] = [:]
    @Published var optionsByID: [String: VideoDownloadOptions] = [:]
    @Published var queue: [QueueItem] = []
    @Published var isLoading = false
    @Published var isDownloading = false
    @Published var isAutoProbing = false
    @Published var message = "No playlist loaded"
    @Published var errorMessage: String?
    @Published var downloadRoot: URL = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first
        ?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Downloads")
    @Published var showingSettings = false
    @Published var showingAbout = false

    private let backend = BackendClient()
    private var downloadTask: Task<Void, Never>?
    private var probeTask: Task<Void, Never>?

    var focusedVideo: VideoInfo? {
        guard let focusedID else { return nil }
        return videos.first { $0.id == focusedID }
    }

    var currentOptions: VideoDownloadOptions {
        get {
            guard let focusedID else { return VideoDownloadOptions() }
            return optionsByID[focusedID] ?? VideoDownloadOptions()
        }
        set {
            guard let focusedID else { return }
            optionsByID[focusedID] = newValue
        }
    }

    func load() {
        guard !url.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Enter a playlist or video URL."
            return
        }
        probeTask?.cancel()
        isLoading = true
        isAutoProbing = false
        message = "Loading metadata..."
        Task {
            do {
                let playlist = try await backend.load(url: url)
                self.playlist = playlist
                videos = playlist.videos.enumerated().map { offset, video in
                    var indexedVideo = video
                    if indexedVideo.playlistIndex == nil || indexedVideo.playlistIndex == 0 {
                        indexedVideo.playlistIndex = offset + 1
                    }
                    return indexedVideo
                }
                selectedIDs = Set(videos.map(\.id))
                focusedID = videos.first?.id
                statusByID = Dictionary(uniqueKeysWithValues: videos.map { ($0.id, "Loading options") })
                optionsByID = Dictionary(uniqueKeysWithValues: videos.map { ($0.id, VideoDownloadOptions()) })
                message = playlist.title
                startAutoProbe()
            } catch {
                errorMessage = error.localizedDescription
                message = "Load failed"
            }
            isLoading = false
        }
    }

    func probeFocused() {
        guard let video = focusedVideo else { return }
        statusByID[video.id] = "Probing"
        Task {
            do {
                let probed = try await backend.probe(video: video)
                applyProbedVideo(probed, fallback: video)
                statusByID[video.id] = "Ready"
            } catch {
                statusByID[video.id] = "Failed"
                errorMessage = error.localizedDescription
            }
        }
    }

    func availableQualityLabels(for video: VideoInfo?) -> [String] {
        guard let video else { return [] }
        let heights = Set(
            video.formats.compactMap { format -> Int? in
                guard format.isVideo, let height = format.height, height > 0 else { return nil }
                return height
            }
        )
        if !heights.isEmpty {
            return heights.sorted(by: >).map { "\($0)p" }
        }
        if video.probed, video.formats.contains(where: { $0.isAudio }) {
            return ["Audio only"]
        }
        return []
    }

    func audioFormats(for video: VideoInfo?) -> [MediaFormat] {
        guard let video else { return [] }
        return video.formats
            .filter { $0.isAudio && !$0.isVideo }
            .sorted { left, right in
                let leftLanguage = left.language ?? ""
                let rightLanguage = right.language ?? ""
                if leftLanguage != rightLanguage {
                    return leftLanguage < rightLanguage
                }
                return (left.abr ?? left.tbr ?? 0) > (right.abr ?? right.tbr ?? 0)
            }
    }

    func subtitleLanguages(for video: VideoInfo?) -> [String] {
        guard let video else { return [] }
        let options = currentOptions
        var languages = Set<String>()
        if options.includeManualSubtitles {
            languages.formUnion(video.subtitles.keys)
        }
        if options.includeAutoSubtitles {
            languages.formUnion(video.automaticCaptions.keys)
        }
        return languages.sorted()
    }

    func toggleAudioFormat(_ formatID: String, isSelected: Bool) {
        var options = currentOptions
        if isSelected {
            if !options.selectedAudioFormatIDs.contains(formatID) {
                options.selectedAudioFormatIDs.append(formatID)
            }
        } else {
            options.selectedAudioFormatIDs.removeAll { $0 == formatID }
        }
        options.allowMultipleAudioTracks = options.selectedAudioFormatIDs.count > 1
        if options.allowMultipleAudioTracks {
            options.preferContainer = "mkv"
        }
        currentOptions = options
    }

    func toggleSubtitleLanguage(_ language: String, isSelected: Bool) {
        var options = currentOptions
        if isSelected {
            if !options.subtitleLanguages.contains(language) {
                options.subtitleLanguages.append(language)
            }
        } else {
            options.subtitleLanguages.removeAll { $0 == language }
        }
        currentOptions = options
    }

    func selectAll() {
        selectedIDs = Set(videos.map(\.id))
    }

    func deselectAll() {
        selectedIDs.removeAll()
    }

    func toggleSelected(_ id: String, isSelected: Bool) {
        if isSelected {
            selectedIDs.insert(id)
        } else {
            selectedIDs.remove(id)
        }
    }

    func applyOptionsToAll() {
        let options = currentOptions
        for video in videos {
            optionsByID[video.id] = options
        }
    }

    func applyOptionsToSelected() {
        let options = currentOptions
        for id in selectedIDs {
            optionsByID[id] = options
        }
    }

    func downloadSelected() {
        guard let playlist else {
            errorMessage = "Load a playlist or video first."
            return
        }
        let selectedVideos = videos.filter { selectedIDs.contains($0.id) }
        guard !selectedVideos.isEmpty else {
            errorMessage = "Select at least one video."
            return
        }

        let jobs = selectedVideos.map {
            DownloadJobPayload(video: $0, options: optionsByID[$0.id] ?? VideoDownloadOptions())
        }
        let request = DownloadRequest(
            playlist: PlaylistSummary(id: playlist.id, title: playlist.title),
            downloadRoot: downloadRoot.path,
            jobs: jobs
        )

        queue = selectedVideos.map {
            QueueItem(id: $0.id, title: $0.title, detail: "Queued", percent: 0, isDone: false, isFailed: false)
        }
        isDownloading = true

        probeTask?.cancel()
        backend.cancelAllOperations()
        downloadTask?.cancel()
        downloadTask = Task {
            do {
                try await backend.download(request: request) { event in
                    self.handleDownloadEvent(event)
                }
            } catch is CancellationError {
                markPendingDownloadsCanceled()
            } catch {
                errorMessage = error.localizedDescription
            }
            isDownloading = false
            downloadTask = nil
        }
    }

    func cancelDownload() {
        guard isDownloading else { return }
        message = "Canceling downloads..."
        for index in queue.indices where !queue[index].isDone && !queue[index].isFailed {
            queue[index].detail = "Canceling"
        }
        downloadTask?.cancel()
        backend.cancelDownload()
    }

    func removeQueueItem(id: String) {
        queue.removeAll { $0.id == id }
    }

    func shutdown() {
        probeTask?.cancel()
        downloadTask?.cancel()
        backend.cancelAllOperations()
        isAutoProbing = false
        isDownloading = false
    }

    private func startAutoProbe() {
        probeTask?.cancel()
        let videosToProbe = videos
        guard !videosToProbe.isEmpty else {
            isAutoProbing = false
            return
        }

        isAutoProbing = true
        probeTask = Task {
            var completed = 0
            for video in videosToProbe {
                if Task.isCancelled { break }
                if let current = videos.first(where: { $0.id == video.id }), current.probed {
                    completed += 1
                    continue
                }
                statusByID[video.id] = "Loading options"
                message = "Loading options \(completed + 1) of \(videosToProbe.count)..."
                do {
                    let probed = try await backend.probe(video: video)
                    if Task.isCancelled { break }
                    applyProbedVideo(probed, fallback: video)
                    statusByID[video.id] = "Ready"
                } catch {
                    if Task.isCancelled { break }
                    statusByID[video.id] = "Options failed"
                }
                completed += 1
            }
            if !Task.isCancelled {
                message = playlist?.title ?? "Options loaded"
            }
            isAutoProbing = false
            probeTask = nil
        }
    }

    private func applyProbedVideo(_ probed: VideoInfo, fallback: VideoInfo) {
        var updated = probed
        if updated.playlistIndex == nil {
            updated.playlistIndex = fallback.playlistIndex
        }
        if fallback.title != updated.title {
            updated.title = fallback.title
        }
        if let index = videos.firstIndex(where: { $0.id == fallback.id }) {
            videos[index] = updated
        }
        normalizeOptions(for: updated)
    }

    private func normalizeOptions(for video: VideoInfo) {
        var options = optionsByID[video.id] ?? VideoDownloadOptions()
        let heights = availableQualityLabels(for: video)
            .compactMap { Int($0.replacingOccurrences(of: "p", with: "")) }
        if let selectedHeight = options.maxHeight, !heights.contains(selectedHeight) {
            options.maxHeight = heights.first
        } else if options.maxHeight == nil, let first = heights.first {
            options.maxHeight = first
        }

        let audioIDs = Set(audioFormats(for: video).map(\.formatID))
        options.selectedAudioFormatIDs.removeAll { !audioIDs.contains($0) }
        options.allowMultipleAudioTracks = options.selectedAudioFormatIDs.count > 1

        let subtitleLanguages = Set(video.subtitles.keys).union(video.automaticCaptions.keys)
        options.subtitleLanguages.removeAll { !subtitleLanguages.contains($0) }
        if options.subtitleLanguages.isEmpty, let firstLanguage = subtitleLanguages.sorted().first {
            options.subtitleLanguages = [firstLanguage]
        }

        optionsByID[video.id] = options
    }

    private func handleDownloadEvent(_ event: DownloadEvent) {
        guard let id = event.videoID else {
            if event.event == "all_finished", let outputDir = event.outputDir {
                message = "Finished: \(outputDir)"
            }
            return
        }
        let title = event.title ?? id
        if let index = queue.firstIndex(where: { $0.id == id }) {
            switch event.event {
            case "started":
                queue[index].detail = event.filename ?? "Starting"
                queue[index].percent = 0
                statusByID[id] = "Downloading"
            case "progress":
                let percent = event.percent ?? 0
                let suffix = [event.speed, event.eta].compactMap { value in
                    guard let value, !value.isEmpty else { return nil }
                    return value
                }.joined(separator: " ")
                queue[index].detail = suffix.isEmpty ? "\(Int(percent))%" : "\(Int(percent))% \(suffix)"
                queue[index].percent = percent
            case "finished":
                queue[index].detail = event.filename ?? "Done"
                queue[index].percent = 100
                queue[index].isDone = true
                statusByID[id] = "Done"
            case "failed":
                queue[index].detail = event.error ?? "Failed"
                queue[index].isFailed = true
                statusByID[id] = "Failed"
            case "canceled":
                queue[index].detail = "Canceled"
                queue[index].isFailed = true
                statusByID[id] = "Canceled"
            default:
                break
            }
        } else {
            queue.append(QueueItem(id: id, title: title, detail: event.event, percent: event.percent ?? 0, isDone: false, isFailed: false))
        }
    }

    private func markPendingDownloadsCanceled() {
        for index in queue.indices where !queue[index].isDone && !queue[index].isFailed {
            let id = queue[index].id
            queue[index].detail = "Canceled"
            queue[index].isFailed = true
            statusByID[id] = "Canceled"
        }
        message = "Download canceled"
    }
}
