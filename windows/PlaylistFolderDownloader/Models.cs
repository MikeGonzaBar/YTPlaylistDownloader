using System.Collections.ObjectModel;
using System.Text.Json.Serialization;

namespace PlaylistFolderDownloader;

public sealed class MediaFormat
{
    [JsonPropertyName("format_id")]
    public string FormatId { get; set; } = "";

    [JsonPropertyName("ext")]
    public string? Ext { get; set; }

    [JsonPropertyName("resolution")]
    public string? Resolution { get; set; }

    [JsonPropertyName("height")]
    public int? Height { get; set; }

    [JsonPropertyName("width")]
    public int? Width { get; set; }

    [JsonPropertyName("fps")]
    public double? Fps { get; set; }

    [JsonPropertyName("vcodec")]
    public string? Vcodec { get; set; }

    [JsonPropertyName("acodec")]
    public string? Acodec { get; set; }

    [JsonPropertyName("abr")]
    public double? Abr { get; set; }

    [JsonPropertyName("tbr")]
    public double? Tbr { get; set; }

    [JsonPropertyName("filesize")]
    public int? Filesize { get; set; }

    [JsonPropertyName("language")]
    public string? Language { get; set; }

    [JsonPropertyName("format_note")]
    public string? FormatNote { get; set; }

    [JsonPropertyName("is_video")]
    public bool IsVideo { get; set; }

    [JsonPropertyName("is_audio")]
    public bool IsAudio { get; set; }
}

public sealed class SubtitleTrack
{
    [JsonPropertyName("language")]
    public string Language { get; set; } = "";

    [JsonPropertyName("ext")]
    public string Ext { get; set; } = "";

    [JsonPropertyName("url")]
    public string? Url { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("source")]
    public string Source { get; set; } = "";
}

public sealed class VideoInfo : ObservableObject
{
    private bool _isSelected;
    private string _status = "Ready";
    private string _qualitySummary = "Loading";
    private string _audioSummary = "Loading";

    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("title")]
    public string Title { get; set; } = "";

    [JsonPropertyName("webpage_url")]
    public string WebpageUrl { get; set; } = "";

    [JsonPropertyName("playlist_index")]
    public int? PlaylistIndex { get; set; }

    [JsonPropertyName("duration")]
    public int? Duration { get; set; }

    [JsonPropertyName("channel")]
    public string? Channel { get; set; }

    [JsonPropertyName("thumbnail_url")]
    public string? ThumbnailUrl { get; set; }

    [JsonPropertyName("availability_status")]
    public string AvailabilityStatus { get; set; } = "unknown";

    [JsonPropertyName("probed")]
    public bool Probed { get; set; }

    [JsonPropertyName("formats")]
    public List<MediaFormat> Formats { get; set; } = [];

    [JsonPropertyName("subtitles")]
    public Dictionary<string, List<SubtitleTrack>> Subtitles { get; set; } = [];

    [JsonPropertyName("automatic_captions")]
    public Dictionary<string, List<SubtitleTrack>> AutomaticCaptions { get; set; } = [];

    [JsonIgnore]
    public bool IsSelected
    {
        get => _isSelected;
        set => SetProperty(ref _isSelected, value);
    }

    [JsonIgnore]
    public string Status
    {
        get => _status;
        set => SetProperty(ref _status, value);
    }

    [JsonIgnore]
    public string QualitySummary
    {
        get => _qualitySummary;
        set => SetProperty(ref _qualitySummary, value);
    }

    [JsonIgnore]
    public string AudioSummary
    {
        get => _audioSummary;
        set => SetProperty(ref _audioSummary, value);
    }

    [JsonIgnore]
    public string IndexText => (PlaylistIndex ?? 0).ToString("00");

    [JsonIgnore]
    public string DurationText => Formatting.FormatDuration(Duration);

    public void CopyDisplayStateFrom(VideoInfo other)
    {
        IsSelected = other.IsSelected;
        Status = other.Status;
        QualitySummary = other.QualitySummary;
        AudioSummary = other.AudioSummary;
    }
}

public sealed class PlaylistInfo
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("title")]
    public string Title { get; set; } = "";

    [JsonPropertyName("webpage_url")]
    public string WebpageUrl { get; set; } = "";

    [JsonPropertyName("warning_count")]
    public int WarningCount { get; set; }

    [JsonPropertyName("videos")]
    public List<VideoInfo> Videos { get; set; } = [];
}

public sealed class VideoDownloadOptions
{
    [JsonPropertyName("include_video")]
    public bool IncludeVideo { get; set; } = true;

    [JsonPropertyName("include_audio")]
    public bool IncludeAudio { get; set; } = true;

    [JsonPropertyName("max_height")]
    public int? MaxHeight { get; set; } = 1080;

    [JsonPropertyName("selected_video_format_id")]
    public string? SelectedVideoFormatId { get; set; }

    [JsonPropertyName("selected_audio_format_ids")]
    public List<string> SelectedAudioFormatIds { get; set; } = [];

    [JsonPropertyName("allow_multiple_audio_tracks")]
    public bool AllowMultipleAudioTracks { get; set; }

    [JsonPropertyName("prefer_container")]
    public string PreferContainer { get; set; } = "mkv";

    [JsonPropertyName("subtitles_enabled")]
    public bool SubtitlesEnabled { get; set; }

    [JsonPropertyName("include_manual_subtitles")]
    public bool IncludeManualSubtitles { get; set; } = true;

    [JsonPropertyName("include_auto_subtitles")]
    public bool IncludeAutoSubtitles { get; set; }

    [JsonPropertyName("subtitle_languages")]
    public List<string> SubtitleLanguages { get; set; } = ["en"];

    [JsonPropertyName("embed_subtitles")]
    public bool EmbedSubtitles { get; set; } = true;

    [JsonPropertyName("keep_subtitle_files")]
    public bool KeepSubtitleFiles { get; set; }

    public VideoDownloadOptions Clone()
    {
        return new VideoDownloadOptions
        {
            IncludeVideo = IncludeVideo,
            IncludeAudio = IncludeAudio,
            MaxHeight = MaxHeight,
            SelectedVideoFormatId = SelectedVideoFormatId,
            SelectedAudioFormatIds = [.. SelectedAudioFormatIds],
            AllowMultipleAudioTracks = AllowMultipleAudioTracks,
            PreferContainer = PreferContainer,
            SubtitlesEnabled = SubtitlesEnabled,
            IncludeManualSubtitles = IncludeManualSubtitles,
            IncludeAutoSubtitles = IncludeAutoSubtitles,
            SubtitleLanguages = [.. SubtitleLanguages],
            EmbedSubtitles = EmbedSubtitles,
            KeepSubtitleFiles = KeepSubtitleFiles,
        };
    }
}

public sealed class QueueItem : ObservableObject
{
    private string _detail = "Queued";
    private double _percent;
    private bool _isDone;
    private bool _isFailed;

    public QueueItem(string id, string title)
    {
        Id = id;
        Title = title;
    }

    public string Id { get; }

    public string Title { get; }

    public string Detail
    {
        get => _detail;
        set
        {
            if (SetProperty(ref _detail, value))
            {
                OnPropertyChanged(nameof(DisplayText));
            }
        }
    }

    public double Percent
    {
        get => _percent;
        set => SetProperty(ref _percent, value);
    }

    public bool IsDone
    {
        get => _isDone;
        set => SetProperty(ref _isDone, value);
    }

    public bool IsFailed
    {
        get => _isFailed;
        set => SetProperty(ref _isFailed, value);
    }

    public string DisplayText => $"{Title} - {Detail}";
}

public sealed class PlaylistEnvelope
{
    [JsonPropertyName("event")]
    public string Event { get; set; } = "";

    [JsonPropertyName("playlist")]
    public PlaylistInfo Playlist { get; set; } = new();
}

public sealed class ProbeEnvelope
{
    [JsonPropertyName("event")]
    public string Event { get; set; } = "";

    [JsonPropertyName("video")]
    public VideoInfo Video { get; set; } = new();
}

public sealed class FailureEnvelope
{
    [JsonPropertyName("event")]
    public string Event { get; set; } = "";

    [JsonPropertyName("command")]
    public string? Command { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }

    [JsonPropertyName("error_type")]
    public string? ErrorType { get; set; }
}

public sealed class PlaylistSummary
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("title")]
    public string Title { get; set; } = "";
}

public sealed class DownloadJobPayload
{
    [JsonPropertyName("video")]
    public VideoInfo Video { get; set; } = new();

    [JsonPropertyName("options")]
    public VideoDownloadOptions Options { get; set; } = new();
}

public sealed class DownloadRequest
{
    [JsonPropertyName("playlist")]
    public PlaylistSummary Playlist { get; set; } = new();

    [JsonPropertyName("download_root")]
    public string DownloadRoot { get; set; } = "";

    [JsonPropertyName("jobs")]
    public List<DownloadJobPayload> Jobs { get; set; } = [];
}

public sealed class DownloadEvent
{
    [JsonPropertyName("event")]
    public string Event { get; set; } = "";

    [JsonPropertyName("video_id")]
    public string? VideoId { get; set; }

    [JsonPropertyName("title")]
    public string? Title { get; set; }

    [JsonPropertyName("filename")]
    public string? Filename { get; set; }

    [JsonPropertyName("percent")]
    public double? Percent { get; set; }

    [JsonPropertyName("speed")]
    public string? Speed { get; set; }

    [JsonPropertyName("eta")]
    public string? Eta { get; set; }

    [JsonPropertyName("error")]
    public string? Error { get; set; }

    [JsonPropertyName("output_dir")]
    public string? OutputDir { get; set; }
}

public sealed class BackendException(string message) : Exception(message);
