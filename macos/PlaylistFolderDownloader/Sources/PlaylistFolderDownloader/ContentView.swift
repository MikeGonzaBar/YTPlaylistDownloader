import AppKit
import SwiftUI

struct ContentView: View {
    @StateObject private var model = AppModel()

    var body: some View {
        ZStack {
            VisualEffectView(material: .underWindowBackground, blendingMode: .behindWindow)
                .ignoresSafeArea()

            if #available(macOS 26.0, *) {
                GlassEffectContainer(spacing: 12) {
                    mainContent
                }
            } else {
                mainContent
            }
        }
        .background(WindowAccessor())
        .preferredColorScheme(.dark)
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.willTerminateNotification)) { _ in
            model.shutdown()
        }
        .onDisappear {
            model.shutdown()
        }
        .sheet(isPresented: $model.showingSettings) {
            SettingsSheet(downloadRoot: $model.downloadRoot)
        }
        .sheet(isPresented: $model.showingAbout) {
            AboutSheet()
        }
        .alert(
            "Error",
            isPresented: Binding(
                get: { model.errorMessage != nil },
                set: { if !$0 { model.errorMessage = nil } }
            )
        ) {
            Button("OK") { model.errorMessage = nil }
        } message: {
            Text(model.errorMessage ?? "")
        }
    }

    private var mainContent: some View {
        VStack(spacing: 10) {
            topBar
            statusBar
            VSplitView {
                HStack(alignment: .top, spacing: 14) {
                    playlistPanel
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    optionsPanel
                        .frame(width: 330)
                        .frame(maxHeight: .infinity)
                }
                .frame(maxWidth: .infinity, minHeight: 260, maxHeight: .infinity, alignment: .top)

                queuePanel
                    .frame(maxWidth: .infinity, minHeight: 78, idealHeight: 118, maxHeight: .infinity)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .layoutPriority(1)
            actionBar
        }
        .padding(.top, 34)
        .padding(.horizontal, 16)
        .padding(.bottom, 14)
        .frame(minWidth: 1180, minHeight: 760)
    }

    private var topBar: some View {
        HStack(spacing: 12) {
            Text("Playlist or video URL")
                .font(.callout.weight(.medium))
                .lineLimit(1)
            TextField("https://www.youtube.com/playlist?list=...", text: $model.url)
                .textFieldStyle(.plain)
                .padding(.horizontal, 12)
                .frame(height: 34)
                .nativeGlassPanel(cornerRadius: 10)
                .layoutPriority(1)
            topToolbarButton(title: "Load", systemImage: "arrow.clockwise", isDisabled: model.isLoading) {
                model.load()
            }
            topToolbarButton(title: "Settings", systemImage: "gearshape") {
                model.showingSettings = true
            }
            topToolbarButton(title: "About", systemImage: "info.circle") {
                model.showingAbout = true
            }
        }
        .padding(.leading, 72)
    }

    private var statusBar: some View {
        HStack {
            Text(model.isLoading ? "Loading metadata..." : model.message)
            Spacer()
            if model.isAutoProbing {
                Text("Loading per-video options")
            }
            Text("\(model.videos.count) \(model.videos.count == 1 ? "video" : "videos")")
            Text("Native macOS frontend")
        }
        .font(.callout)
        .foregroundStyle(.white.opacity(0.9))
    }

    private var playlistPanel: some View {
        VStack(spacing: 0) {
            tableHeader
            if model.videos.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "list.bullet.rectangle")
                        .font(.system(size: 34))
                        .foregroundStyle(.white.opacity(0.38))
                    Text("Load a playlist or single video to begin.")
                        .font(.callout)
                        .foregroundStyle(.white.opacity(0.68))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(model.videos) { video in
                            videoRow(video)
                        }
                    }
                }
            }
        }
        .nativeGlassPanel(cornerRadius: 14)
    }

    private var tableHeader: some View {
        HStack(spacing: 0) {
            tableCell("Selected", width: 82, alignment: .center)
            tableCell("Index", width: 72, alignment: .center)
            tableCell("Title", width: nil, alignment: .leading)
            tableCell("Duration", width: 90, alignment: .center)
            tableCell("Channel", width: 130, alignment: .leading)
            tableCell("Status", width: 110, alignment: .center)
            tableCell("Quality", width: 90, alignment: .center)
            tableCell("Audio", width: 90, alignment: .center)
        }
        .font(.caption.weight(.semibold))
        .lineLimit(1)
        .padding(.vertical, 7)
        .background(.white.opacity(0.08))
    }

    private func videoRow(_ video: VideoInfo) -> some View {
        let isFocused = model.focusedID == video.id
        let options = model.optionsByID[video.id] ?? VideoDownloadOptions()
        return HStack(spacing: 0) {
            Toggle(
                "",
                isOn: Binding(
                    get: { model.selectedIDs.contains(video.id) },
                    set: { model.toggleSelected(video.id, isSelected: $0) }
                )
            )
            .labelsHidden()
            .frame(width: 82)

            tableText(String(format: "%02d", video.playlistIndex ?? 0), width: 72, alignment: .center)
            tableText(video.title, width: nil, alignment: .leading)
            tableText(formatDuration(video.duration), width: 90, alignment: .center)
            tableText(video.channel ?? "", width: 130, alignment: .leading)
            tableText(model.statusByID[video.id] ?? "Ready", width: 110, alignment: .center)
            tableText(qualitySummary(for: video, options: options), width: 90, alignment: .center)
            tableText(audioSummary(for: video, options: options), width: 90, alignment: .center)
        }
        .frame(height: 34)
        .background(isFocused ? Color.accentColor.opacity(0.45) : Color.white.opacity(0.045))
        .contentShape(Rectangle())
        .onTapGesture {
            model.focusedID = video.id
        }
    }

    private var optionsPanel: some View {
        let qualityLabels = model.availableQualityLabels(for: model.focusedVideo)
        return ScrollView {
            VStack(alignment: .leading, spacing: 11) {
                Text("Video Options")
                    .font(.headline)
                Text(model.focusedVideo?.title ?? "Select a video to edit options.")
                    .font(.callout)
                    .lineLimit(2)

                HStack {
                    Toggle("Include video", isOn: optionBinding(\.includeVideo))
                    Toggle("Include audio", isOn: optionBinding(\.includeAudio))
                }

                Picker("Quality", selection: qualityBinding) {
                    if qualityLabels.isEmpty {
                        Text(model.focusedVideo?.probed == true ? "No video quality" : "Loading options...")
                            .tag("Loading")
                    } else {
                        ForEach(qualityLabels, id: \.self) { label in
                            Text(label).tag(label)
                        }
                    }
                }
                .pickerStyle(.menu)
                .disabled(qualityLabels.isEmpty)

                formatBox(title: "Video formats", formats: model.focusedVideo?.formats.filter(\.isVideo) ?? [])
                audioTrackBox(formats: model.audioFormats(for: model.focusedVideo))

                Button(model.focusedVideo?.probed == true ? "Refresh options" : "Probe formats") {
                    model.probeFocused()
                }
                .nativeGlassButton()
                .disabled(model.focusedVideo == nil)

                Toggle("Subtitles", isOn: optionBinding(\.subtitlesEnabled))
                Toggle("Manual subtitles", isOn: optionBinding(\.includeManualSubtitles))
                Toggle("Auto subtitles", isOn: optionBinding(\.includeAutoSubtitles))

                subtitleLanguageBox(languages: model.subtitleLanguages(for: model.focusedVideo))

                Toggle("Embed subtitles", isOn: optionBinding(\.embedSubtitles))
                Toggle("Keep subtitle files", isOn: optionBinding(\.keepSubtitleFiles))

                Picker("Container", selection: optionBinding(\.preferContainer)) {
                    Text("mkv").tag("mkv")
                    Text("mp4").tag("mp4")
                    Text("webm").tag("webm")
                }
                .pickerStyle(.menu)
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .nativeGlassPanel(cornerRadius: 14)
    }

    private func formatBox(title: String, formats: [MediaFormat]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.callout.weight(.medium))
            ScrollView {
                VStack(alignment: .leading, spacing: 4) {
                    if formats.isEmpty {
                        Text("Probe this video to show formats.")
                            .foregroundStyle(.white.opacity(0.55))
                    } else {
                        ForEach(formats, id: \.formatID) { format in
                            Text(formatLabel(format))
                                .font(.caption)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(8)
            }
            .frame(height: 68)
            .nativeGlassPanel(cornerRadius: 10)
        }
    }

    private func audioTrackBox(formats: [MediaFormat]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Audio tracks")
                .font(.callout.weight(.medium))
            ScrollView {
                VStack(alignment: .leading, spacing: 4) {
                    if formats.isEmpty {
                        Text(model.focusedVideo?.probed == true ? "No separate audio tracks found." : "Loading audio tracks...")
                            .foregroundStyle(.white.opacity(0.55))
                    } else {
                        ForEach(formats, id: \.formatID) { format in
                            Toggle(
                                audioTrackLabel(format),
                                isOn: Binding(
                                    get: { model.currentOptions.selectedAudioFormatIDs.contains(format.formatID) },
                                    set: { model.toggleAudioFormat(format.formatID, isSelected: $0) }
                                )
                            )
                            .font(.caption)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(8)
            }
            .frame(height: 84)
            .nativeGlassPanel(cornerRadius: 10)
        }
    }

    private func subtitleLanguageBox(languages: [String]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Subtitle languages")
                .font(.callout.weight(.medium))
            ScrollView {
                VStack(alignment: .leading, spacing: 4) {
                    if languages.isEmpty {
                        Text(model.focusedVideo?.probed == true ? "No subtitles found." : "Loading subtitles...")
                            .foregroundStyle(.white.opacity(0.55))
                    } else {
                        ForEach(languages, id: \.self) { language in
                            Toggle(
                                language,
                                isOn: Binding(
                                    get: { model.currentOptions.subtitleLanguages.contains(language) },
                                    set: { model.toggleSubtitleLanguage(language, isSelected: $0) }
                                )
                            )
                            .font(.caption)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(8)
            }
            .frame(height: 72)
            .nativeGlassPanel(cornerRadius: 10)
        }
    }

    private var queuePanel: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Download Queue")
                .font(.headline)
            if model.queue.isEmpty {
                Text("No downloads queued")
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(10)
                    .nativeGlassPanel(cornerRadius: 12)
            } else {
                ScrollView {
                    VStack(spacing: 5) {
                        ForEach(model.queue) { item in
                            HStack(spacing: 10) {
                                Text("\(item.title) - \(item.detail)")
                                    .lineLimit(1)
                                    .frame(width: 360, alignment: .leading)
                                ProgressView(value: item.percent, total: 100)
                                    .progressViewStyle(.linear)
                                queueStatusControl(for: item)
                            }
                            .padding(.horizontal, 8)
                        }
                    }
                }
                .padding(8)
                .nativeGlassPanel(cornerRadius: 12)
            }
        }
    }

    private func topToolbarButton(
        title: String,
        systemImage: String,
        isDisabled: Bool = false,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: 7) {
                Image(systemName: systemImage)
                    .font(.system(size: 13, weight: .semibold))
                    .frame(width: 16, alignment: .center)
                Text(title)
                    .font(.callout.weight(.semibold))
            }
                .frame(minWidth: 82, minHeight: 28, alignment: .center)
                .contentShape(Rectangle())
        }
        .help(title)
        .disabled(isDisabled)
        .nativeGlassButton()
    }

    @ViewBuilder
    private func queueStatusControl(for item: QueueItem) -> some View {
        if item.isFailed {
            Button {
                model.removeQueueItem(id: item.id)
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.red)
                    .frame(width: 20, height: 20)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .help("Remove from queue")
        } else {
            Image(systemName: item.isDone ? "checkmark.circle.fill" : "circle")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(item.isDone ? .green : .white.opacity(0.6))
                .frame(width: 20, height: 20)
        }
    }

    private var actionBar: some View {
        HStack {
            Button("Select all") { model.selectAll() }
                .nativeGlassButton()
            Button("Deselect all") { model.deselectAll() }
                .nativeGlassButton()
            Spacer()
            Button("Apply to selected") { model.applyOptionsToSelected() }
                .nativeGlassButton()
            Button("Apply to all") { model.applyOptionsToAll() }
                .nativeGlassButton()
            Button("Download selected") { model.downloadSelected() }
                .disabled(model.isDownloading)
                .nativeGlassButton(prominent: true)
            Button("Cancel") { model.cancelDownload() }
                .disabled(!model.isDownloading)
                .nativeGlassButton()
        }
    }

    private func tableCell(_ text: String, width: CGFloat?, alignment: Alignment) -> some View {
        Text(text)
            .lineLimit(1)
            .padding(.horizontal, 8)
            .frame(width: width, alignment: alignment)
            .frame(maxWidth: width == nil ? .infinity : nil, alignment: alignment)
            .layoutPriority(width == nil ? 1 : 0)
    }

    private func tableText(_ text: String, width: CGFloat?, alignment: Alignment) -> some View {
        Text(text)
            .font(.callout)
            .lineLimit(1)
            .truncationMode(.tail)
            .padding(.horizontal, 8)
            .frame(width: width, alignment: alignment)
            .frame(maxWidth: width == nil ? .infinity : nil, alignment: alignment)
            .layoutPriority(width == nil ? 1 : 0)
    }

    private func optionBinding<T>(_ keyPath: WritableKeyPath<VideoDownloadOptions, T>) -> Binding<T> {
        Binding {
            model.currentOptions[keyPath: keyPath]
        } set: { value in
            var options = model.currentOptions
            options[keyPath: keyPath] = value
            model.currentOptions = options
        }
    }

    private var qualityBinding: Binding<String> {
        Binding {
            let options = model.currentOptions
            if !options.includeVideo && options.includeAudio {
                return "Audio only"
            }
            let labels = model.availableQualityLabels(for: model.focusedVideo)
            if let label = options.maxHeight.map({ "\($0)p" }), labels.contains(label) {
                return label
            }
            return labels.first ?? "Loading"
        } set: { value in
            var options = model.currentOptions
            if value == "Audio only" {
                options.maxHeight = nil
                options.includeVideo = false
                options.includeAudio = true
            } else if value != "Loading" {
                options.maxHeight = Int(value.replacingOccurrences(of: "p", with: ""))
                options.includeVideo = true
            }
            model.currentOptions = options
        }
    }

    private var subtitleLanguagesBinding: Binding<String> {
        Binding {
            model.currentOptions.subtitleLanguages.joined(separator: ",")
        } set: { value in
            var options = model.currentOptions
            options.subtitleLanguages = value
                .split(separator: ",")
                .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                .filter { !$0.isEmpty }
            model.currentOptions = options
        }
    }

    private func formatDuration(_ seconds: Int?) -> String {
        guard let seconds else { return "" }
        let hours = seconds / 3600
        let minutes = (seconds % 3600) / 60
        let secs = seconds % 60
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, secs)
        }
        return String(format: "%d:%02d", minutes, secs)
    }

    private func formatLabel(_ format: MediaFormat) -> String {
        [
            format.resolution,
            format.language,
            format.vcodec != "none" ? format.vcodec : nil,
            format.acodec != "none" ? format.acodec : nil,
            format.abr.map { "\(Int($0))kbps" },
            format.formatID
        ]
        .compactMap { $0 }
        .filter { !$0.isEmpty }
        .joined(separator: " | ")
    }

    private func audioTrackLabel(_ format: MediaFormat) -> String {
        [
            format.language ?? "unknown",
            format.acodec,
            format.abr.map { "\(Int($0))kbps" },
            format.ext,
            format.formatID
        ]
        .compactMap { $0 }
        .filter { !$0.isEmpty && $0 != "none" }
        .joined(separator: " | ")
    }

    private func audioSummary(for video: VideoInfo, options: VideoDownloadOptions) -> String {
        guard options.includeAudio else { return "" }
        let count = model.audioFormats(for: video).count
        if !options.selectedAudioFormatIDs.isEmpty {
            return "\(options.selectedAudioFormatIDs.count) selected"
        }
        if count > 0 {
            return "\(count) tracks"
        }
        return video.probed ? "Audio" : "Loading"
    }

    private func qualitySummary(for video: VideoInfo, options: VideoDownloadOptions) -> String {
        if !video.probed {
            return model.statusByID[video.id] == "Options failed" ? "Failed" : "Loading"
        }
        if !options.includeVideo && options.includeAudio {
            return "Audio"
        }
        let available = model.availableQualityLabels(for: video)
        if let label = options.maxHeight.map({ "\($0)p" }), available.contains(label) {
            return label
        }
        return available.first ?? "Audio"
    }
}

struct SettingsSheet: View {
    @Binding var downloadRoot: URL
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Settings")
                .font(.title2.weight(.semibold))

            VStack(alignment: .leading, spacing: 8) {
                Text("Download folder")
                    .font(.callout.weight(.medium))
                HStack(spacing: 10) {
                    Text(downloadRoot.path)
                        .lineLimit(1)
                        .truncationMode(.middle)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 10)
                        .frame(height: 32)
                        .nativeGlassPanel(cornerRadius: 9)
                    Button("Choose...") {
                        chooseDownloadFolder()
                    }
                    .nativeGlassButton()
                }
            }

            Text("The selected playlist or single video will be saved inside this folder. Playlist downloads create a folder using the playlist title.")
                .font(.callout)
                .foregroundStyle(.secondary)

            HStack {
                Spacer()
                Button("Done") { dismiss() }
                    .nativeGlassButton(prominent: true)
            }
        }
        .padding(22)
        .frame(width: 560)
        .background(VisualEffectView(material: .hudWindow, blendingMode: .behindWindow).ignoresSafeArea())
    }

    private func chooseDownloadFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.directoryURL = downloadRoot
        if panel.runModal() == .OK, let url = panel.url {
            downloadRoot = url
        }
    }
}

struct AboutSheet: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Playlist Folder Downloader")
                .font(.title2.weight(.semibold))
            Text("Native macOS frontend with a Python yt-dlp backend.")
                .foregroundStyle(.secondary)
            Text("Use this app only for videos you own, have permission to download, or that are explicitly licensed for download. This MVP does not support cookies, private playlists, login, DRM bypass, CAPTCHA bypass, or access-control bypass.")
                .fixedSize(horizontal: false, vertical: true)
            HStack {
                Spacer()
                Button("Done") { dismiss() }
                    .nativeGlassButton(prominent: true)
            }
        }
        .padding(22)
        .frame(width: 520)
        .background(VisualEffectView(material: .hudWindow, blendingMode: .behindWindow).ignoresSafeArea())
    }
}
