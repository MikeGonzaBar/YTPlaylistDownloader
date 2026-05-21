using Microsoft.UI.Xaml;

namespace PlaylistFolderDownloader;

public partial class App : Application
{
    private Window? _window;

    public App()
    {
        InitializeComponent();
        UnhandledException += OnUnhandledException;
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _window = new MainWindow();
        _window.Activate();
    }

    private static void OnUnhandledException(object sender, Microsoft.UI.Xaml.UnhandledExceptionEventArgs args)
    {
        FrontendLog.Write($"Unhandled UI exception: {args.Message}\n{args.Exception}");
        System.Diagnostics.Debug.WriteLine(args.Exception);
    }
}
