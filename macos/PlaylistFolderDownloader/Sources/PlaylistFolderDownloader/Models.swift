import Foundation

struct MediaFormat: Codable, Hashable {
    let formatID: String
    let ext: String?
    let resolution: String?
    let height: Int?
    let width: Int?
    let fps: Double?
    let vcodec: String?
    let acodec: String?
    let abr: Double?
    let tbr: Double?
    let filesize: Int?
    let language: String?
    let formatNote: String?
    let isVideo: Bool
    let isAudio: Bool

    enum CodingKeys: String, CodingKey {
        case formatID = "format_id"
        case ext, resolution, height, width, fps, vcodec, acodec, abr, tbr, filesize, language
        case formatNote = "format_note"
        case isVideo = "is_video"
        case isAudio = "is_audio"
    }
}

struct SubtitleTrack: Codable, Hashable {
    let language: String
    let ext: String
    let url: String?
    let name: String?
    let source: String
}

struct VideoInfo: Codable, Identifiable, Hashable {
    let id: String
    var title: String
    var webpageURL: String
    var playlistIndex: Int?
    var duration: Int?
    var channel: String?
    var thumbnailURL: String?
    var availabilityStatus: String
    var probed: Bool
    var formats: [MediaFormat]
    var subtitles: [String: [SubtitleTrack]]
    var automaticCaptions: [String: [SubtitleTrack]]

    enum CodingKeys: String, CodingKey {
        case id, title, duration, channel, probed, formats
        case webpageURL = "webpage_url"
        case playlistIndex = "playlist_index"
        case thumbnailURL = "thumbnail_url"
        case availabilityStatus = "availability_status"
        case subtitles
        case automaticCaptions = "automatic_captions"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        webpageURL = try container.decode(String.self, forKey: .webpageURL)
        playlistIndex = try container.decodeIfPresent(Int.self, forKey: .playlistIndex)
        duration = try container.decodeIfPresent(Int.self, forKey: .duration)
        channel = try container.decodeIfPresent(String.self, forKey: .channel)
        thumbnailURL = try container.decodeIfPresent(String.self, forKey: .thumbnailURL)
        availabilityStatus = try container.decodeIfPresent(String.self, forKey: .availabilityStatus) ?? "unknown"
        probed = try container.decodeIfPresent(Bool.self, forKey: .probed) ?? false
        formats = try container.decodeIfPresent([MediaFormat].self, forKey: .formats) ?? []
        subtitles = try container.decodeIfPresent([String: [SubtitleTrack]].self, forKey: .subtitles) ?? [:]
        automaticCaptions = try container.decodeIfPresent([String: [SubtitleTrack]].self, forKey: .automaticCaptions) ?? [:]
    }
}

struct PlaylistInfo: Codable {
    let id: String
    let title: String
    let webpageURL: String
    let warningCount: Int
    let videos: [VideoInfo]

    enum CodingKeys: String, CodingKey {
        case id, title, videos
        case webpageURL = "webpage_url"
        case warningCount = "warning_count"
    }
}

struct LoadEnvelope: Codable {
    let event: String
    let playlist: PlaylistInfo
}

struct ProbeEnvelope: Codable {
    let event: String
    let video: VideoInfo
}

struct FailureEnvelope: Codable {
    let event: String
    let command: String?
    let error: String?
    let errorType: String?

    enum CodingKeys: String, CodingKey {
        case event, command, error
        case errorType = "error_type"
    }
}

struct VideoDownloadOptions: Codable, Hashable {
    var includeVideo = true
    var includeAudio = true
    var maxHeight: Int? = 1080
    var selectedVideoFormatID: String?
    var selectedAudioFormatIDs: [String] = []
    var allowMultipleAudioTracks = false
    var preferContainer = "mkv"
    var subtitlesEnabled = false
    var includeManualSubtitles = true
    var includeAutoSubtitles = false
    var subtitleLanguages: [String] = ["en"]
    var embedSubtitles = true
    var keepSubtitleFiles = false

    enum CodingKeys: String, CodingKey {
        case includeVideo = "include_video"
        case includeAudio = "include_audio"
        case maxHeight = "max_height"
        case selectedVideoFormatID = "selected_video_format_id"
        case selectedAudioFormatIDs = "selected_audio_format_ids"
        case allowMultipleAudioTracks = "allow_multiple_audio_tracks"
        case preferContainer = "prefer_container"
        case subtitlesEnabled = "subtitles_enabled"
        case includeManualSubtitles = "include_manual_subtitles"
        case includeAutoSubtitles = "include_auto_subtitles"
        case subtitleLanguages = "subtitle_languages"
        case embedSubtitles = "embed_subtitles"
        case keepSubtitleFiles = "keep_subtitle_files"
    }
}

struct PlaylistSummary: Codable {
    let id: String
    let title: String
}

struct DownloadJobPayload: Codable {
    let video: VideoInfo
    let options: VideoDownloadOptions
}

struct DownloadRequest: Codable {
    let playlist: PlaylistSummary
    let downloadRoot: String
    let jobs: [DownloadJobPayload]

    enum CodingKeys: String, CodingKey {
        case playlist, jobs
        case downloadRoot = "download_root"
    }
}

struct DownloadEvent: Codable {
    let event: String
    let videoID: String?
    let title: String?
    let filename: String?
    let percent: Double?
    let speed: String?
    let eta: String?
    let error: String?
    let outputDir: String?

    enum CodingKeys: String, CodingKey {
        case event, title, filename, percent, speed, eta, error
        case videoID = "video_id"
        case outputDir = "output_dir"
    }
}

struct QueueItem: Identifiable, Hashable {
    let id: String
    var title: String
    var detail: String
    var percent: Double
    var isDone: Bool
    var isFailed: Bool
}
