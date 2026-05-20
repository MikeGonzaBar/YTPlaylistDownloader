using Microsoft.UI;
using Microsoft.UI.Composition.SystemBackdrops;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.Graphics;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace PlaylistFolderDownloader;

public sealed partial class MainWindow : Window
{
    private readonly AppModel _model = new();
    private bool _syncingOptions;

    public MainWindow()
    {
        InitializeComponent();
        Root.DataContext = _model;
        ApplyFluentBackdrop();
        ApplyTitleBarTheme();
        ApplyWindowIcon();
        ResizeWindow(1220, 780);
        _model.PropertyChanged += (_, args) =>
            DispatcherQueue.TryEnqueue(() =>
            {
                RefreshShellState();
                if (args.PropertyName is nameof(AppModel.FocusedVideo) or nameof(AppModel.CurrentOptions))
                {
                    RefreshOptionsPanel();
                }
            });
        Closed += (_, _) => _model.Shutdown();
        RefreshShellState();
        RefreshOptionsPanel();
    }

    private async void LoadClicked(object sender, RoutedEventArgs e)
    {
        _model.Url = UrlBox.Text;
        await _model.LoadAsync();
        if (_model.FocusedVideo is not null)
        {
            VideosList.SelectedItem = _model.FocusedVideo;
        }

        RefreshShellState();
        RefreshOptionsPanel();
        await ShowErrorIfNeededAsync();
    }

    private void VideosListSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (VideosList.SelectedItem is VideoInfo video)
        {
            _model.FocusedVideo = video;
            RefreshOptionsPanel();
        }
    }

    private async void ProbeClicked(object sender, RoutedEventArgs e)
    {
        await _model.ProbeFocusedAsync();
        RefreshOptionsPanel();
        await ShowErrorIfNeededAsync();
    }

    private void SelectAllClicked(object sender, RoutedEventArgs e)
    {
        _model.SelectAll();
    }

    private void DeselectAllClicked(object sender, RoutedEventArgs e)
    {
        _model.DeselectAll();
    }

    private void ApplySelectedClicked(object sender, RoutedEventArgs e)
    {
        SyncOptionsFromControls();
        _model.ApplyOptionsToSelected();
    }

    private void ApplyAllClicked(object sender, RoutedEventArgs e)
    {
        SyncOptionsFromControls();
        _model.ApplyOptionsToAll();
    }

    private async void DownloadSelectedClicked(object sender, RoutedEventArgs e)
    {
        SyncOptionsFromControls();
        await _model.DownloadSelectedAsync();
        RefreshShellState();
        await ShowErrorIfNeededAsync();
    }

    private void CancelClicked(object sender, RoutedEventArgs e)
    {
        _model.CancelDownload();
        RefreshShellState();
    }

    private void RemoveQueueItemClicked(object sender, RoutedEventArgs e)
    {
        if (sender is FrameworkElement { Tag: string id })
        {
            _model.RemoveQueueItem(id);
        }
    }

    private async void SettingsClicked(object sender, RoutedEventArgs e)
    {
        var rootBox = new TextBox
        {
            Text = _model.DownloadRoot,
            MinWidth = 460,
            PlaceholderText = "Download folder",
        };
        var browseButton = new Button { Content = "Choose..." };
        var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        row.Children.Add(rootBox);
        row.Children.Add(browseButton);

        browseButton.Click += async (_, _) =>
        {
            var picker = new FolderPicker();
            picker.FileTypeFilter.Add("*");
            InitializeWithWindow.Initialize(picker, WindowNative.GetWindowHandle(this));
            var folder = await picker.PickSingleFolderAsync();
            if (folder is not null)
            {
                rootBox.Text = folder.Path;
            }
        };

        var dialog = NewDialog("Settings", row);
        dialog.PrimaryButtonText = "Save";
        dialog.CloseButtonText = "Cancel";
        var result = await dialog.ShowAsync();
        if (result == ContentDialogResult.Primary && !string.IsNullOrWhiteSpace(rootBox.Text))
        {
            _model.DownloadRoot = rootBox.Text.Trim();
        }
    }

    private async void AboutClicked(object sender, RoutedEventArgs e)
    {
        var text = new TextBlock
        {
            Text = "Native WinUI 3 frontend with a Python yt-dlp backend.\n\n"
                + "Use this app only for videos you own, have permission to download, "
                + "or that are explicitly licensed for download. This MVP does not support "
                + "cookies, private playlists, login, DRM bypass, CAPTCHA bypass, or access-control bypass.",
            TextWrapping = TextWrapping.Wrap,
            MaxWidth = 520,
        };
        var dialog = NewDialog("Playlist Folder Downloader", text);
        dialog.CloseButtonText = "Done";
        await dialog.ShowAsync();
    }

    private void OptionControlChanged(object sender, RoutedEventArgs e)
    {
        if (!_syncingOptions)
        {
            SyncOptionsFromControls();
            RefreshOptionListsOnly();
        }
    }

    private void OptionSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!_syncingOptions)
        {
            SyncOptionsFromControls();
        }
    }

    private void QualitySelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_syncingOptions)
        {
            return;
        }

        var options = _model.CurrentOptions.Clone();
        if (QualityCombo.SelectedItem is string label)
        {
            if (label == "Audio only")
            {
                options.MaxHeight = null;
                options.IncludeVideo = false;
                options.IncludeAudio = true;
            }
            else if (label.EndsWith('p') && int.TryParse(label[..^1], out var height))
            {
                options.MaxHeight = height;
                options.IncludeVideo = true;
            }
        }

        _model.CurrentOptions = options;
        RefreshOptionsPanel();
    }

    private void VideoFormatsSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_syncingOptions)
        {
            return;
        }

        var options = _model.CurrentOptions.Clone();
        options.SelectedVideoFormatId = (VideoFormatsList.SelectedItem as ListViewItem)?.Tag as string;
        _model.CurrentOptions = options;
    }

    private void RefreshShellState()
    {
        ProbeStatusText.Visibility = _model.IsAutoProbing ? Visibility.Visible : Visibility.Collapsed;
        VideoCountText.Text = $"{_model.Videos.Count} {(_model.Videos.Count == 1 ? "video" : "videos")}";
        DownloadButton.IsEnabled = !_model.IsDownloading;
        CancelButton.IsEnabled = _model.IsDownloading;
    }

    private void RefreshOptionsPanel()
    {
        _syncingOptions = true;
        try
        {
            var video = _model.FocusedVideo;
            var options = _model.CurrentOptions;
            FocusedTitleText.Text = video?.Title ?? "Select a video to edit options.";
            IncludeVideoBox.IsEnabled = video is not null;
            IncludeAudioBox.IsEnabled = video is not null;
            IncludeVideoBox.IsChecked = options.IncludeVideo;
            IncludeAudioBox.IsChecked = options.IncludeAudio;
            SubtitlesEnabledBox.IsChecked = options.SubtitlesEnabled;
            ManualSubtitlesBox.IsChecked = options.IncludeManualSubtitles;
            AutoSubtitlesBox.IsChecked = options.IncludeAutoSubtitles;
            EmbedSubtitlesBox.IsChecked = options.EmbedSubtitles;
            KeepSubtitleFilesBox.IsChecked = options.KeepSubtitleFiles;
            SelectContainer(options.PreferContainer);

            QualityCombo.Items.Clear();
            var qualities = _model.AvailableQualityLabels(video);
            foreach (var quality in qualities)
            {
                QualityCombo.Items.Add(quality);
            }

            if (qualities.Count == 0)
            {
                QualityCombo.Items.Add(video?.Probed == true ? "No video quality" : "Loading options...");
                QualityCombo.SelectedIndex = 0;
                QualityCombo.IsEnabled = false;
            }
            else
            {
                var selected = !options.IncludeVideo && options.IncludeAudio
                    ? "Audio only"
                    : options.MaxHeight is int height ? $"{height}p" : qualities[0];
                QualityCombo.SelectedItem = qualities.Contains(selected) ? selected : qualities[0];
                QualityCombo.IsEnabled = true;
            }

            RefreshOptionListsOnly();
        }
        finally
        {
            _syncingOptions = false;
        }
    }

    private void RefreshOptionListsOnly()
    {
        var video = _model.FocusedVideo;
        var options = _model.CurrentOptions;

        VideoFormatsList.Items.Clear();
        if (video is null || video.Formats.All(format => !format.IsVideo))
        {
            VideoFormatsList.Items.Add(new ListViewItem
            {
                Content = video?.Probed == true ? "No video formats found." : "Probe this video to show formats.",
                IsEnabled = false,
            });
        }
        else
        {
            foreach (var format in video.Formats.Where(format => format.IsVideo))
            {
                var item = new ListViewItem
                {
                    Content = Formatting.FormatMediaLabel(format),
                    Tag = format.FormatId,
                };
                VideoFormatsList.Items.Add(item);
                if (format.FormatId == options.SelectedVideoFormatId)
                {
                    VideoFormatsList.SelectedItem = item;
                }
            }
        }

        AudioTracksPanel.Children.Clear();
        var audioFormats = _model.AudioFormats(video);
        if (audioFormats.Count == 0)
        {
            AudioTracksPanel.Children.Add(new TextBlock
            {
                Text = video?.Probed == true ? "No separate audio tracks found." : "Loading audio tracks...",
                Foreground = new SolidColorBrush(Colors.Gray),
            });
        }
        else
        {
            foreach (var format in audioFormats)
            {
                var box = new CheckBox
                {
                    Content = Formatting.FormatMediaLabel(format),
                    IsChecked = options.SelectedAudioFormatIds.Contains(format.FormatId),
                    Tag = format.FormatId,
                };
                box.Checked += AudioTrackToggled;
                box.Unchecked += AudioTrackToggled;
                AudioTracksPanel.Children.Add(box);
            }
        }

        SubtitleLanguagesPanel.Children.Clear();
        var languages = _model.SubtitleLanguages(video);
        if (languages.Count == 0)
        {
            SubtitleLanguagesPanel.Children.Add(new TextBlock
            {
                Text = video?.Probed == true ? "No subtitles found." : "Loading subtitles...",
                Foreground = new SolidColorBrush(Colors.Gray),
            });
        }
        else
        {
            foreach (var language in languages)
            {
                var box = new CheckBox
                {
                    Content = language,
                    IsChecked = options.SubtitleLanguages.Contains(language),
                    Tag = language,
                };
                box.Checked += SubtitleLanguageToggled;
                box.Unchecked += SubtitleLanguageToggled;
                SubtitleLanguagesPanel.Children.Add(box);
            }
        }
    }

    private void AudioTrackToggled(object sender, RoutedEventArgs e)
    {
        if (_syncingOptions || sender is not CheckBox { Tag: string formatId } box)
        {
            return;
        }

        _model.ToggleAudioFormat(formatId, box.IsChecked == true);
        RefreshOptionsPanel();
    }

    private void SubtitleLanguageToggled(object sender, RoutedEventArgs e)
    {
        if (_syncingOptions || sender is not CheckBox { Tag: string language } box)
        {
            return;
        }

        _model.ToggleSubtitleLanguage(language, box.IsChecked == true);
    }

    private void SyncOptionsFromControls()
    {
        if (_model.FocusedVideo is null)
        {
            return;
        }

        var options = _model.CurrentOptions.Clone();
        options.IncludeVideo = IncludeVideoBox.IsChecked == true;
        options.IncludeAudio = IncludeAudioBox.IsChecked == true;
        options.SubtitlesEnabled = SubtitlesEnabledBox.IsChecked == true;
        options.IncludeManualSubtitles = ManualSubtitlesBox.IsChecked == true;
        options.IncludeAutoSubtitles = AutoSubtitlesBox.IsChecked == true;
        options.EmbedSubtitles = EmbedSubtitlesBox.IsChecked == true;
        options.KeepSubtitleFiles = KeepSubtitleFilesBox.IsChecked == true;
        options.PreferContainer = SelectedContainer();
        if (options.SelectedAudioFormatIds.Count > 1 || (options.SubtitlesEnabled && options.EmbedSubtitles))
        {
            options.PreferContainer = "mkv";
        }

        _model.CurrentOptions = options;
        SelectContainer(options.PreferContainer);
    }

    private string SelectedContainer()
    {
        return (ContainerCombo.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "mkv";
    }

    private void SelectContainer(string container)
    {
        foreach (var item in ContainerCombo.Items.OfType<ComboBoxItem>())
        {
            if (string.Equals(item.Content?.ToString(), container, StringComparison.OrdinalIgnoreCase))
            {
                ContainerCombo.SelectedItem = item;
                return;
            }
        }

        ContainerCombo.SelectedIndex = 0;
    }

    private ContentDialog NewDialog(string title, object content)
    {
        return new ContentDialog
        {
            XamlRoot = Content.XamlRoot,
            Title = title,
            Content = content,
            DefaultButton = ContentDialogButton.Primary,
        };
    }

    private async Task ShowErrorIfNeededAsync()
    {
        if (string.IsNullOrWhiteSpace(_model.ErrorMessage))
        {
            return;
        }

        var dialog = NewDialog("Error", new TextBlock
        {
            Text = $"{_model.ErrorMessage}\n\nLog: {FrontendLog.LogPath}",
            TextWrapping = TextWrapping.Wrap,
            MaxWidth = 520,
        });
        dialog.CloseButtonText = "OK";
        await dialog.ShowAsync();
        _model.ErrorMessage = null;
    }

    private void ApplyFluentBackdrop()
    {
        if (DesktopAcrylicController.IsSupported())
        {
            SystemBackdrop = new DesktopAcrylicBackdrop();
        }
        else if (MicaController.IsSupported())
        {
            SystemBackdrop = new MicaBackdrop { Kind = MicaKind.BaseAlt };
        }
    }

    private void ApplyTitleBarTheme()
    {
        var titleBar = GetAppWindow().TitleBar;
        titleBar.BackgroundColor = Colors.Transparent;
        titleBar.InactiveBackgroundColor = Colors.Transparent;
        titleBar.ForegroundColor = Colors.White;
        titleBar.InactiveForegroundColor = Colors.Gray;
        titleBar.ButtonBackgroundColor = Colors.Transparent;
        titleBar.ButtonInactiveBackgroundColor = Colors.Transparent;
        titleBar.ButtonHoverBackgroundColor = Windows.UI.Color.FromArgb(38, 255, 255, 255);
        titleBar.ButtonPressedBackgroundColor = Windows.UI.Color.FromArgb(60, 255, 255, 255);
        titleBar.ButtonForegroundColor = Colors.White;
        titleBar.ButtonInactiveForegroundColor = Colors.Gray;
    }

    private void ResizeWindow(int width, int height)
    {
        GetAppWindow().Resize(new SizeInt32(width, height));
    }

    private void ApplyWindowIcon()
    {
        var iconPath = System.IO.Path.Combine(AppContext.BaseDirectory, "Assets", "AppIcon.ico");
        if (File.Exists(iconPath))
        {
            GetAppWindow().SetIcon(iconPath);
        }
    }

    private AppWindow GetAppWindow()
    {
        var hwnd = WindowNative.GetWindowHandle(this);
        var id = Win32Interop.GetWindowIdFromWindow(hwnd);
        return AppWindow.GetFromWindowId(id);
    }
}
