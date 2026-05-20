using System.Collections.ObjectModel;

namespace PlaylistFolderDownloader;

public sealed class AppModel : ObservableObject
{
    private readonly BackendClient _backend = new();
    private CancellationTokenSource? _loadCts;
    private CancellationTokenSource? _downloadCts;
    private CancellationTokenSource? _probeCts;
    private string _url = "";
    private PlaylistInfo? _playlist;
    private VideoInfo? _focusedVideo;
    private bool _isLoading;
    private bool _isDownloading;
    private bool _isAutoProbing;
    private string _message = "No playlist loaded";
    private string? _errorMessage;
    private string _downloadRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        "Downloads");

    public ObservableCollection<VideoInfo> Videos { get; } = [];

    public ObservableCollection<QueueItem> Queue { get; } = [];

    public Dictionary<string, VideoDownloadOptions> OptionsById { get; } = [];

    public string Url
    {
        get => _url;
        set => SetProperty(ref _url, value);
    }

    public PlaylistInfo? Playlist
    {
        get => _playlist;
        private set => SetProperty(ref _playlist, value);
    }

    public VideoInfo? FocusedVideo
    {
        get => _focusedVideo;
        set
        {
            if (SetProperty(ref _focusedVideo, value))
            {
                OnPropertyChanged(nameof(CurrentOptions));
            }
        }
    }

    public VideoDownloadOptions CurrentOptions
    {
        get
        {
            if (FocusedVideo is null)
            {
                return new VideoDownloadOptions();
            }

            return OptionsById.TryGetValue(FocusedVideo.Id, out var options) ? options : new VideoDownloadOptions();
        }
        set
        {
            if (FocusedVideo is null)
            {
                return;
            }

            OptionsById[FocusedVideo.Id] = value;
            RefreshSummaries(FocusedVideo);
            OnPropertyChanged();
        }
    }

    public bool IsLoading
    {
        get => _isLoading;
        private set => SetProperty(ref _isLoading, value);
    }

    public bool IsDownloading
    {
        get => _isDownloading;
        private set => SetProperty(ref _isDownloading, value);
    }

    public bool IsAutoProbing
    {
        get => _isAutoProbing;
        private set => SetProperty(ref _isAutoProbing, value);
    }

    public string Message
    {
        get => _message;
        private set => SetProperty(ref _message, value);
    }

    public string? ErrorMessage
    {
        get => _errorMessage;
        set => SetProperty(ref _errorMessage, value);
    }

    public string DownloadRoot
    {
        get => _downloadRoot;
        set => SetProperty(ref _downloadRoot, value);
    }

    public async Task LoadAsync()
    {
        if (string.IsNullOrWhiteSpace(Url))
        {
            ErrorMessage = "Enter a playlist or video URL.";
            return;
        }

        _probeCts?.Cancel();
        _loadCts?.Cancel();
        _downloadCts?.Cancel();
        _backend.CancelAllOperations();
        IsLoading = true;
        IsAutoProbing = false;
        Message = "Starting Python backend...";
        FrontendLog.Write($"UI load started. Log path: {FrontendLog.LogPath}");
        var loadCts = new CancellationTokenSource(TimeSpan.FromSeconds(90));
        _loadCts = loadCts;

        try
        {
            Message = "Loading metadata...";
            var playlist = await _backend.LoadAsync(Url.Trim(), loadCts.Token);
            Playlist = playlist;
            Videos.Clear();
            OptionsById.Clear();
            Queue.Clear();

            for (var index = 0; index < playlist.Videos.Count; index++)
            {
                var video = playlist.Videos[index];
                if (video.PlaylistIndex is null or 0)
                {
                    video.PlaylistIndex = index + 1;
                }

                video.IsSelected = true;
                video.Status = "Loading options";
                OptionsById[video.Id] = new VideoDownloadOptions();
                RefreshSummaries(video);
                Videos.Add(video);
            }

            FocusedVideo = Videos.FirstOrDefault();
            Message = playlist.Title;
            _ = StartAutoProbeAsync();
        }
        catch (OperationCanceledException)
        {
            if (ReferenceEquals(_loadCts, loadCts))
            {
                ErrorMessage = "Timed out while loading metadata. Check the backend log, then try the URL again.";
                Message = "Load timed out";
                FrontendLog.Write("UI load timed out.");
            }
            else
            {
                FrontendLog.Write("UI load canceled because a newer load started.");
            }
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
            Message = "Load failed";
            FrontendLog.Write($"UI load failed: {ex}");
        }
        finally
        {
            if (ReferenceEquals(_loadCts, loadCts))
            {
                IsLoading = false;
                _loadCts = null;
            }
            loadCts.Dispose();
        }
    }

    public async Task ProbeFocusedAsync()
    {
        if (FocusedVideo is null)
        {
            return;
        }

        await ProbeOneAsync(FocusedVideo, CancellationToken.None, showErrors: true);
    }

    public IReadOnlyList<string> AvailableQualityLabels(VideoInfo? video)
    {
        if (video is null)
        {
            return [];
        }

        var heights = video.Formats
            .Where(format => format.IsVideo && format.Height is > 0)
            .Select(format => format.Height!.Value)
            .Distinct()
            .OrderDescending()
            .Select(height => $"{height}p")
            .ToList();

        if (heights.Count > 0)
        {
            return heights;
        }

        if (video.Probed && video.Formats.Any(format => format.IsAudio))
        {
            return ["Audio only"];
        }

        return [];
    }

    public IReadOnlyList<MediaFormat> AudioFormats(VideoInfo? video)
    {
        if (video is null)
        {
            return [];
        }

        return video.Formats
            .Where(format => format.IsAudio && !format.IsVideo)
            .OrderBy(format => format.Language ?? "")
            .ThenByDescending(format => format.Abr ?? format.Tbr ?? 0)
            .ToList();
    }

    public IReadOnlyList<string> SubtitleLanguages(VideoInfo? video)
    {
        if (video is null)
        {
            return [];
        }

        var options = CurrentOptions;
        var languages = new HashSet<string>();
        if (options.IncludeManualSubtitles)
        {
            languages.UnionWith(video.Subtitles.Keys);
        }

        if (options.IncludeAutoSubtitles)
        {
            languages.UnionWith(video.AutomaticCaptions.Keys);
        }

        return languages.Order().ToList();
    }

    public void ToggleAudioFormat(string formatId, bool isSelected)
    {
        var options = CurrentOptions.Clone();
        if (isSelected && !options.SelectedAudioFormatIds.Contains(formatId))
        {
            options.SelectedAudioFormatIds.Add(formatId);
        }
        else if (!isSelected)
        {
            options.SelectedAudioFormatIds.RemoveAll(item => item == formatId);
        }

        options.AllowMultipleAudioTracks = options.SelectedAudioFormatIds.Count > 1;
        if (options.AllowMultipleAudioTracks)
        {
            options.PreferContainer = "mkv";
        }

        CurrentOptions = options;
    }

    public void ToggleSubtitleLanguage(string language, bool isSelected)
    {
        var options = CurrentOptions.Clone();
        if (isSelected && !options.SubtitleLanguages.Contains(language))
        {
            options.SubtitleLanguages.Add(language);
        }
        else if (!isSelected)
        {
            options.SubtitleLanguages.RemoveAll(item => item == language);
        }

        CurrentOptions = options;
    }

    public void SelectAll()
    {
        foreach (var video in Videos)
        {
            video.IsSelected = true;
        }
    }

    public void DeselectAll()
    {
        foreach (var video in Videos)
        {
            video.IsSelected = false;
        }
    }

    public void ApplyOptionsToAll()
    {
        var options = CurrentOptions.Clone();
        foreach (var video in Videos)
        {
            OptionsById[video.Id] = options.Clone();
            RefreshSummaries(video);
        }
    }

    public void ApplyOptionsToSelected()
    {
        var options = CurrentOptions.Clone();
        foreach (var video in Videos.Where(video => video.IsSelected))
        {
            OptionsById[video.Id] = options.Clone();
            RefreshSummaries(video);
        }
    }

    public async Task DownloadSelectedAsync()
    {
        if (Playlist is null)
        {
            ErrorMessage = "Load a playlist or video first.";
            return;
        }

        var selected = Videos.Where(video => video.IsSelected).ToList();
        if (selected.Count == 0)
        {
            ErrorMessage = "Select at least one video.";
            return;
        }

        if (!Directory.Exists(DownloadRoot))
        {
            ErrorMessage = "Choose an existing download folder.";
            return;
        }

        _probeCts?.Cancel();
        _downloadCts?.Cancel();
        _backend.CancelAllOperations();
        _downloadCts = new CancellationTokenSource();

        Queue.Clear();
        foreach (var video in selected)
        {
            Queue.Add(new QueueItem(video.Id, video.Title));
        }

        var request = new DownloadRequest
        {
            Playlist = new PlaylistSummary { Id = Playlist.Id, Title = Playlist.Title },
            DownloadRoot = DownloadRoot,
            Jobs = selected
                .Select(video => new DownloadJobPayload
                {
                    Video = video,
                    Options = OptionsById.TryGetValue(video.Id, out var options)
                        ? options.Clone()
                        : new VideoDownloadOptions(),
                })
                .ToList(),
        };

        IsDownloading = true;
        try
        {
            await _backend.DownloadAsync(request, HandleDownloadEventAsync, _downloadCts.Token);
        }
        catch (OperationCanceledException)
        {
            MarkPendingDownloadsCanceled();
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
        }
        finally
        {
            IsDownloading = false;
            _downloadCts.Dispose();
            _downloadCts = null;
        }
    }

    public void CancelDownload()
    {
        if (!IsDownloading)
        {
            return;
        }

        Message = "Canceling downloads...";
        foreach (var item in Queue.Where(item => !item.IsDone && !item.IsFailed))
        {
            item.Detail = "Canceling";
        }

        _downloadCts?.Cancel();
        _backend.CancelAllOperations();
    }

    public void RemoveQueueItem(string id)
    {
        var item = Queue.FirstOrDefault(queueItem => queueItem.Id == id);
        if (item is not null)
        {
            Queue.Remove(item);
        }
    }

    public void Shutdown()
    {
        _loadCts?.Cancel();
        _probeCts?.Cancel();
        _downloadCts?.Cancel();
        _backend.CancelAllOperations();
        IsAutoProbing = false;
        IsDownloading = false;
    }

    public void RefreshSummaries(VideoInfo video)
    {
        var options = OptionsById.TryGetValue(video.Id, out var selectedOptions)
            ? selectedOptions
            : new VideoDownloadOptions();

        video.QualitySummary = QualitySummary(video, options);
        video.AudioSummary = AudioSummary(video, options);
    }

    private async Task StartAutoProbeAsync()
    {
        _probeCts?.Cancel();
        var probeCts = new CancellationTokenSource();
        _probeCts = probeCts;
        var token = probeCts.Token;
        var videos = Videos.ToList();
        if (videos.Count == 0)
        {
            IsAutoProbing = false;
            if (ReferenceEquals(_probeCts, probeCts))
            {
                _probeCts = null;
            }
            probeCts.Dispose();
            return;
        }

        IsAutoProbing = true;
        var completed = 0;
        try
        {
            foreach (var video in videos)
            {
                token.ThrowIfCancellationRequested();
                if (video.Probed)
                {
                    completed += 1;
                    continue;
                }

                video.Status = "Loading options";
                Message = $"Loading options {completed + 1} of {videos.Count}...";
                await ProbeOneAsync(video, token, showErrors: false);
                completed += 1;
            }

            Message = Playlist?.Title ?? "Options loaded";
        }
        catch (OperationCanceledException)
        {
        }
        finally
        {
            if (ReferenceEquals(_probeCts, probeCts))
            {
                IsAutoProbing = false;
                _probeCts = null;
            }
            probeCts.Dispose();
        }
    }

    private async Task ProbeOneAsync(VideoInfo video, CancellationToken token, bool showErrors)
    {
        video.Status = "Probing";
        try
        {
            var probed = await _backend.ProbeAsync(video, token);
            ApplyProbedVideo(probed, video);
            probed.Status = "Ready";
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            video.Status = showErrors ? "Failed" : "Options failed";
            video.QualitySummary = "Failed";
            if (showErrors)
            {
                ErrorMessage = ex.Message;
            }
        }
    }

    private void ApplyProbedVideo(VideoInfo probed, VideoInfo fallback)
    {
        probed.CopyDisplayStateFrom(fallback);
        if (probed.PlaylistIndex is null)
        {
            probed.PlaylistIndex = fallback.PlaylistIndex;
        }

        if (!string.IsNullOrWhiteSpace(fallback.Title))
        {
            probed.Title = fallback.Title;
        }

        var index = Videos.IndexOf(fallback);
        if (index >= 0)
        {
            Videos[index] = probed;
        }

        FocusedVideo = FocusedVideo?.Id == fallback.Id ? probed : FocusedVideo;
        NormalizeOptions(probed);
        RefreshSummaries(probed);
    }

    private void NormalizeOptions(VideoInfo video)
    {
        if (!OptionsById.TryGetValue(video.Id, out var options))
        {
            options = new VideoDownloadOptions();
            OptionsById[video.Id] = options;
        }

        var heights = AvailableQualityLabels(video)
            .Select(label => int.TryParse(label.Replace("p", "", StringComparison.OrdinalIgnoreCase), out var height) ? height : (int?)null)
            .OfType<int>()
            .ToList();

        if (options.MaxHeight is int selectedHeight && !heights.Contains(selectedHeight))
        {
            options.MaxHeight = heights.FirstOrDefault();
        }
        else if (options.MaxHeight is null && heights.Count > 0)
        {
            options.MaxHeight = heights[0];
        }

        var audioIds = AudioFormats(video).Select(format => format.FormatId).ToHashSet();
        options.SelectedAudioFormatIds.RemoveAll(id => !audioIds.Contains(id));
        options.AllowMultipleAudioTracks = options.SelectedAudioFormatIds.Count > 1;

        var subtitleLanguages = video.Subtitles.Keys.Union(video.AutomaticCaptions.Keys).ToHashSet();
        options.SubtitleLanguages.RemoveAll(language => !subtitleLanguages.Contains(language));
        if (options.SubtitleLanguages.Count == 0 && subtitleLanguages.Order().FirstOrDefault() is { } language)
        {
            options.SubtitleLanguages.Add(language);
        }
    }

    private Task HandleDownloadEventAsync(DownloadEvent downloadEvent)
    {
        if (downloadEvent.Event == "all_finished")
        {
            if (!string.IsNullOrWhiteSpace(downloadEvent.OutputDir))
            {
                Message = $"Finished: {downloadEvent.OutputDir}";
            }

            return Task.CompletedTask;
        }

        if (string.IsNullOrWhiteSpace(downloadEvent.VideoId))
        {
            return Task.CompletedTask;
        }

        var id = downloadEvent.VideoId;
        var item = Queue.FirstOrDefault(queueItem => queueItem.Id == id);
        if (item is null)
        {
            item = new QueueItem(id, downloadEvent.Title ?? id);
            Queue.Add(item);
        }

        var video = Videos.FirstOrDefault(item => item.Id == id);
        switch (downloadEvent.Event)
        {
            case "started":
                item.Detail = downloadEvent.Filename ?? "Starting";
                item.Percent = 0;
                if (video is not null)
                {
                    video.Status = "Downloading";
                }
                break;
            case "progress":
                var percent = downloadEvent.Percent ?? 0;
                var suffix = string.Join(" ", new[] { downloadEvent.Speed, downloadEvent.Eta }
                    .Where(value => !string.IsNullOrWhiteSpace(value)));
                item.Detail = string.IsNullOrWhiteSpace(suffix) ? $"{percent:0}%" : $"{percent:0}% {suffix}";
                item.Percent = percent;
                break;
            case "finished":
                item.Detail = downloadEvent.Filename ?? "Done";
                item.Percent = 100;
                item.IsDone = true;
                if (video is not null)
                {
                    video.Status = "Done";
                }
                break;
            case "failed":
                item.Detail = downloadEvent.Error ?? "Failed";
                item.IsFailed = true;
                if (video is not null)
                {
                    video.Status = "Failed";
                }
                break;
            case "canceled":
                item.Detail = "Canceled";
                item.IsFailed = true;
                if (video is not null)
                {
                    video.Status = "Canceled";
                }
                break;
        }

        return Task.CompletedTask;
    }

    private void MarkPendingDownloadsCanceled()
    {
        foreach (var item in Queue.Where(item => !item.IsDone && !item.IsFailed))
        {
            item.Detail = "Canceled";
            item.IsFailed = true;
            var video = Videos.FirstOrDefault(video => video.Id == item.Id);
            if (video is not null)
            {
                video.Status = "Canceled";
            }
        }

        Message = "Download canceled";
    }

    private string AudioSummary(VideoInfo video, VideoDownloadOptions options)
    {
        if (!options.IncludeAudio)
        {
            return "";
        }

        var count = AudioFormats(video).Count;
        if (options.SelectedAudioFormatIds.Count > 0)
        {
            return $"{options.SelectedAudioFormatIds.Count} selected";
        }

        if (count > 0)
        {
            return $"{count} tracks";
        }

        return video.Probed ? "Audio" : "Loading";
    }

    private string QualitySummary(VideoInfo video, VideoDownloadOptions options)
    {
        if (!video.Probed)
        {
            return video.Status == "Options failed" ? "Failed" : "Loading";
        }

        if (!options.IncludeVideo && options.IncludeAudio)
        {
            return "Audio";
        }

        var available = AvailableQualityLabels(video);
        if (options.MaxHeight is int height && available.Contains($"{height}p"))
        {
            return $"{height}p";
        }

        return available.FirstOrDefault() ?? "Audio";
    }
}
