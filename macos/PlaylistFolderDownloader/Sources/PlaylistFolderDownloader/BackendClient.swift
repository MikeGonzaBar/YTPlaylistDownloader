import Foundation

final class ProcessRegistry: @unchecked Sendable {
    private let lock = NSLock()
    private var processes: [UUID: Process] = [:]

    func insert(_ process: Process) -> UUID {
        let id = UUID()
        lock.lock()
        processes[id] = process
        lock.unlock()
        return id
    }

    func remove(_ id: UUID) {
        lock.lock()
        processes[id] = nil
        lock.unlock()
    }

    func terminateAll() {
        lock.lock()
        let runningProcesses = Array(processes.values)
        lock.unlock()

        for process in runningProcesses where process.isRunning {
            process.terminate()
        }
    }
}

enum BackendError: LocalizedError {
    case repoRootNotFound
    case invalidOutput
    case processFailed(String)

    var errorDescription: String? {
        switch self {
        case .repoRootNotFound:
            "Could not find the project root containing pyproject.toml."
        case .invalidOutput:
            "The Python backend returned invalid output."
        case let .processFailed(message):
            message
        }
    }
}

actor BackendClient {
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()
    private let processRegistry = ProcessRegistry()

    func load(url: String) async throws -> PlaylistInfo {
        let output = try await runBackend(arguments: ["load", url])
        guard let line = output.split(separator: "\n").last else {
            throw BackendError.invalidOutput
        }
        let data = Data(line.utf8)
        if let failure = try? decoder.decode(FailureEnvelope.self, from: data),
           failure.event == "failed" {
            throw BackendError.processFailed(failure.error ?? "Could not load metadata.")
        }
        return try decoder.decode(LoadEnvelope.self, from: data).playlist
    }

    func probe(video: VideoInfo) async throws -> VideoInfo {
        let videoData = try encoder.encode(video)
        let videoJSON = String(decoding: videoData, as: UTF8.self)
        let output = try await runBackend(arguments: ["probe", videoJSON])
        guard let line = output.split(separator: "\n").last else {
            throw BackendError.invalidOutput
        }
        let data = Data(line.utf8)
        if let failure = try? decoder.decode(FailureEnvelope.self, from: data),
           failure.event == "failed" {
            throw BackendError.processFailed(failure.error ?? "Could not probe video formats.")
        }
        return try decoder.decode(ProbeEnvelope.self, from: data).video
    }

    func download(
        request: DownloadRequest,
        onEvent: @escaping @MainActor (DownloadEvent) -> Void
    ) async throws {
        let requestData = try encoder.encode(request)
        let process = try makeProcess(arguments: ["download"])
        let processID = processRegistry.insert(process)
        defer { processRegistry.remove(processID) }

        let stdin = Pipe()
        let stdout = Pipe()
        let errPipe = Pipe()
        process.standardInput = stdin
        process.standardOutput = stdout
        process.standardError = errPipe

        try process.run()
        stdin.fileHandleForWriting.write(requestData)
        stdin.fileHandleForWriting.closeFile()

        Task.detached {
            let data = errPipe.fileHandleForReading.readDataToEndOfFile()
            if let text = String(data: data, encoding: .utf8), !text.isEmpty {
                fputs(text, Darwin.stderr)
            }
        }

        for try await line in stdout.fileHandleForReading.bytes.lines {
            if Task.isCancelled {
                processRegistry.terminateAll()
                throw CancellationError()
            }
            guard !line.isEmpty else { continue }
            if let data = line.data(using: .utf8),
               let event = try? decoder.decode(DownloadEvent.self, from: data) {
                await onEvent(event)
            }
        }

        process.waitUntilExit()
        if process.terminationStatus != 0 {
            if Task.isCancelled || process.terminationReason == .uncaughtSignal {
                throw CancellationError()
            }
            throw BackendError.processFailed("The Python backend exited with status \(process.terminationStatus).")
        }
    }

    nonisolated func cancelDownload() {
        processRegistry.terminateAll()
    }

    nonisolated func cancelAllOperations() {
        processRegistry.terminateAll()
    }

    private func runBackend(arguments: [String]) async throws -> String {
        let process = try makeProcess(arguments: arguments)
        let processID = processRegistry.insert(process)
        defer { processRegistry.remove(processID) }

        let stdout = Pipe()
        let errPipe = Pipe()
        process.standardOutput = stdout
        process.standardError = errPipe
        try process.run()

        let output = stdout.fileHandleForReading.readDataToEndOfFile()
        let errorOutput = errPipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()

        if let text = String(data: errorOutput, encoding: .utf8), !text.isEmpty {
            fputs(text, Darwin.stderr)
        }
        if process.terminationStatus != 0 {
            if let message = decodeFailureMessage(from: output) {
                throw BackendError.processFailed(message)
            }
            let message = String(data: errorOutput, encoding: .utf8) ?? "Backend failed."
            throw BackendError.processFailed(message)
        }
        return String(data: output, encoding: .utf8) ?? ""
    }

    private func decodeFailureMessage(from data: Data) -> String? {
        guard let output = String(data: data, encoding: .utf8),
              let line = output.split(separator: "\n").last else {
            return nil
        }

        guard let failure = try? decoder.decode(FailureEnvelope.self, from: Data(line.utf8)),
              failure.event == "failed" else {
            return nil
        }

        return failure.error
    }

    private func makeProcess(arguments: [String]) throws -> Process {
        let root = try findRepoRoot()
        let uv = ProcessInfo.processInfo.environment["UV"] ?? "uv"
        let quotedArgs = arguments.map(shellQuote).joined(separator: " ")
        let command = "cd \(shellQuote(root.path)) && \(uv) run python -m playlist_folder_downloader.cli \(quotedArgs)"

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", command]
        process.environment = ProcessInfo.processInfo.environment.merging(["PYTHONUNBUFFERED": "1"]) { _, new in new }
        return process
    }

    private func findRepoRoot() throws -> URL {
        if let override = ProcessInfo.processInfo.environment["PFD_BACKEND_ROOT"] {
            return URL(fileURLWithPath: override)
        }

        var url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        for _ in 0..<8 {
            if FileManager.default.fileExists(atPath: url.appendingPathComponent("pyproject.toml").path) {
                return url
            }
            url.deleteLastPathComponent()
        }
        throw BackendError.repoRootNotFound
    }

    private func shellQuote(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: "'\\''") + "'"
    }
}
