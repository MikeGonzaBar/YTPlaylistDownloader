using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;

namespace PlaylistFolderDownloader;

public sealed class BackendClient
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true,
    };

    private readonly ConcurrentDictionary<Guid, Process> _processes = [];

    public async Task<PlaylistInfo> LoadAsync(string url, CancellationToken cancellationToken)
    {
        FrontendLog.Write($"Load requested: {url}");
        var output = await RunBackendAsync(["load", url], null, cancellationToken);
        var line = LastJsonLine(output) ?? throw new BackendException("The Python backend returned no output.");
        ThrowIfFailure(line, "Could not load metadata.");
        var envelope = JsonSerializer.Deserialize<PlaylistEnvelope>(line, JsonOptions)
            ?? throw new BackendException("The Python backend returned invalid load data.");
        return envelope.Playlist;
    }

    public async Task<VideoInfo> ProbeAsync(VideoInfo video, CancellationToken cancellationToken)
    {
        var videoJson = JsonSerializer.Serialize(new Dictionary<string, object?>
        {
            ["id"] = video.Id,
            ["title"] = video.Title,
            ["webpage_url"] = video.WebpageUrl,
            ["playlist_index"] = video.PlaylistIndex,
        }, JsonOptions);
        var output = await RunBackendAsync(["probe"], videoJson, cancellationToken);
        var line = LastJsonLine(output) ?? throw new BackendException("The Python backend returned no output.");
        ThrowIfFailure(line, "Could not probe video formats.");
        var envelope = JsonSerializer.Deserialize<ProbeEnvelope>(line, JsonOptions)
            ?? throw new BackendException("The Python backend returned invalid probe data.");
        return envelope.Video;
    }

    public async Task DownloadAsync(
        DownloadRequest request,
        Func<DownloadEvent, Task> onEvent,
        CancellationToken cancellationToken)
    {
        var requestJson = JsonSerializer.Serialize(request, JsonOptions);
        using var process = MakeBackendProcess(["download"]);
        var processId = Track(process);
        Task<string>? errorTask = null;
        try
        {
            StartBackendProcess(process);
            await process.StandardInput.WriteAsync(requestJson.AsMemory(), cancellationToken);
            process.StandardInput.Close();

            errorTask = process.StandardError.ReadToEndAsync();

            while (!process.StandardOutput.EndOfStream)
            {
                cancellationToken.ThrowIfCancellationRequested();
                var line = await process.StandardOutput.ReadLineAsync(cancellationToken);
                if (string.IsNullOrWhiteSpace(line))
                {
                    continue;
                }

                var downloadEvent = JsonSerializer.Deserialize<DownloadEvent>(line, JsonOptions);
                if (downloadEvent is not null)
                {
                    await onEvent(downloadEvent);
                }
            }

            await process.WaitForExitAsync(cancellationToken);
            var error = await errorTask;
            if (!string.IsNullOrWhiteSpace(error))
            {
                FrontendLog.Write($"Backend stderr: {error.Trim()}");
                Console.Error.WriteLine(error);
            }

            if (process.ExitCode != 0)
            {
                throw new BackendException(
                    string.IsNullOrWhiteSpace(error)
                        ? $"The Python backend exited with status {process.ExitCode}."
                        : error.Trim());
            }
        }
        catch (OperationCanceledException)
        {
            Terminate(process);
            throw;
        }
        finally
        {
            _processes.TryRemove(processId, out _);
        }
    }

    public void CancelAllOperations()
    {
        foreach (var process in _processes.Values)
        {
            Terminate(process);
        }
    }

    private async Task<string> RunBackendAsync(
        IReadOnlyList<string> arguments,
        string? standardInput,
        CancellationToken cancellationToken)
    {
        using var process = MakeBackendProcess(arguments);
        var processId = Track(process);
        try
        {
            StartBackendProcess(process);
            if (standardInput is not null)
            {
                await process.StandardInput.WriteAsync(standardInput.AsMemory(), cancellationToken);
            }

            process.StandardInput.Close();
            var outputTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
            var errorTask = process.StandardError.ReadToEndAsync(cancellationToken);
            await process.WaitForExitAsync(cancellationToken);
            var output = await outputTask;
            var error = await errorTask;
            if (!string.IsNullOrWhiteSpace(error))
            {
                FrontendLog.Write($"Backend stderr: {error.Trim()}");
                Console.Error.WriteLine(error);
            }

            if (process.ExitCode != 0)
            {
                FrontendLog.Write($"Backend exited with status {process.ExitCode}. Stdout: {output.Trim()}");
                if (LastJsonLine(output) is { } line)
                {
                    ThrowIfFailure(line, "The Python backend failed.");
                }

                throw new BackendException(
                    string.IsNullOrWhiteSpace(error) ? $"The Python backend exited with status {process.ExitCode}." : error.Trim());
            }

            FrontendLog.Write($"Backend completed successfully. Stdout length: {output.Length}");
            return output;
        }
        catch (OperationCanceledException)
        {
            Terminate(process);
            throw;
        }
        finally
        {
            _processes.TryRemove(processId, out _);
        }
    }

    private Process MakeBackendProcess(IReadOnlyList<string> backendArguments)
    {
        var root = FindRepoRoot();
        var python = FindRepoPython(root);
        ProcessStartInfo startInfo;

        if (python is not null)
        {
            startInfo = NewBackendStartInfo(python, root);
        }
        else
        {
            startInfo = NewBackendStartInfo(FindUvExecutable(), root);
            startInfo.ArgumentList.Add("run");
            startInfo.ArgumentList.Add("python");
        }

        startInfo.Environment["PYTHONUNBUFFERED"] = "1";
        startInfo.ArgumentList.Add("-m");
        startInfo.ArgumentList.Add("playlist_folder_downloader.cli");
        foreach (var argument in backendArguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        return new Process { StartInfo = startInfo, EnableRaisingEvents = true };
    }

    private static ProcessStartInfo NewBackendStartInfo(string executable, DirectoryInfo root)
    {
        return new ProcessStartInfo
        {
            FileName = executable,
            WorkingDirectory = root.FullName,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
    }

    private static void StartBackendProcess(Process process)
    {
        try
        {
            FrontendLog.Write(
                "Starting backend: "
                + $"{process.StartInfo.FileName} {RedactedArguments(process.StartInfo.ArgumentList)} "
                + $"(cwd={process.StartInfo.WorkingDirectory})");
            process.Start();
        }
        catch (Exception ex)
        {
            var fileName = process.StartInfo.FileName;
            var workingDirectory = process.StartInfo.WorkingDirectory;
            throw new BackendException(
                $"Could not start the Python backend. Tried '{fileName}' in '{workingDirectory}'. "
                + $"Make sure uv is installed and run 'uv sync --extra dev'. Details: {ex.Message}");
        }
    }

    private static string RedactedArguments(IEnumerable<string> arguments)
    {
        return string.Join(
            " ",
            arguments.Select(argument => argument.TrimStart().StartsWith('{') ? "<json>" : argument));
    }

    private static DirectoryInfo FindRepoRoot()
    {
        var overrideRoot = Environment.GetEnvironmentVariable("PFD_BACKEND_ROOT");
        if (!string.IsNullOrWhiteSpace(overrideRoot))
        {
            return new DirectoryInfo(overrideRoot);
        }

        var candidates = new[]
        {
            new DirectoryInfo(Environment.CurrentDirectory),
            new DirectoryInfo(AppContext.BaseDirectory),
        };

        foreach (var start in candidates)
        {
            for (var current = start; current is not null; current = current.Parent)
            {
                if (File.Exists(Path.Combine(current.FullName, "pyproject.toml")))
                {
                    return current;
                }
            }
        }

        throw new BackendException("Could not find the project root containing pyproject.toml.");
    }

    private static string? FindRepoPython(DirectoryInfo root)
    {
        var venvPython = Path.Combine(root.FullName, ".venv", "Scripts", "python.exe");
        if (File.Exists(venvPython))
        {
            return venvPython;
        }

        return null;
    }

    private static string FindUvExecutable()
    {
        var explicitUv = Environment.GetEnvironmentVariable("UV");
        if (!string.IsNullOrWhiteSpace(explicitUv))
        {
            return explicitUv;
        }

        foreach (var path in (Environment.GetEnvironmentVariable("PATH") ?? "")
            .Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            var candidate = Path.Combine(path.Trim(), "uv.exe");
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var windowsAppsUv = Path.Combine(localAppData, "Microsoft", "WindowsApps", "uv.exe");
        if (File.Exists(windowsAppsUv))
        {
            return windowsAppsUv;
        }

        var wingetPackages = Path.Combine(localAppData, "Microsoft", "WinGet", "Packages");
        if (Directory.Exists(wingetPackages))
        {
            var packageUv = Directory
                .EnumerateFiles(wingetPackages, "uv.exe", SearchOption.AllDirectories)
                .FirstOrDefault(path => path.Contains("astral-sh.uv", StringComparison.OrdinalIgnoreCase));
            if (packageUv is not null)
            {
                return packageUv;
            }
        }

        return "uv";
    }

    private Guid Track(Process process)
    {
        var id = Guid.NewGuid();
        _processes[id] = process;
        return id;
    }

    private static void Terminate(Process process)
    {
        try
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
            }
        }
        catch (InvalidOperationException)
        {
        }
    }

    private static string? LastJsonLine(string output)
    {
        return output
            .Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries)
            .LastOrDefault(line => line.TrimStart().StartsWith('{'));
    }

    private static void ThrowIfFailure(string json, string fallback)
    {
        var failure = JsonSerializer.Deserialize<FailureEnvelope>(json, JsonOptions);
        if (failure?.Event == "failed")
        {
            throw new BackendException(failure.Error ?? fallback);
        }
    }
}
