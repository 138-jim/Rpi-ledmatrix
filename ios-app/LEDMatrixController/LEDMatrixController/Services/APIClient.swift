//
//  APIClient.swift
//  LEDMatrixController
//
//  HTTP API client for fetching data from Raspberry Pi web server
//

import Foundation

/// HTTP API client for communicating with the LED Matrix backend
class APIClient {
    static let shared = APIClient()

    // Base URL for the Raspberry Pi web server
    private let baseURL = "http://raspberrypi.local:8080"

    // URLSession with timeout configuration
    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 5.0  // 5 second timeout
        config.timeoutIntervalForResource = 10.0
        self.session = URLSession(configuration: config)
    }

    /// Fetch system statistics from the backend
    /// - Parameter completion: Completion handler with Result containing SystemStats or Error
    func fetchSystemStats(completion: @escaping (Result<SystemStats, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/api/system-stats") else {
            completion(.failure(APIError.invalidURL))
            return
        }

        let task = session.dataTask(with: url) { data, response, error in
            // Handle network error
            if let error = error {
                let userError = self.userFriendlyError(from: error)
                DispatchQueue.main.async {
                    completion(.failure(userError))
                }
                return
            }

            // Check HTTP response
            guard let httpResponse = response as? HTTPURLResponse else {
                DispatchQueue.main.async {
                    completion(.failure(APIError.invalidResponse))
                }
                return
            }

            guard httpResponse.statusCode == 200 else {
                DispatchQueue.main.async {
                    completion(.failure(APIError.httpError(statusCode: httpResponse.statusCode)))
                }
                return
            }

            // Parse JSON
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(APIError.noData))
                }
                return
            }

            do {
                let decoder = JSONDecoder()
                // Decode on background thread, then pass to main actor
                let stats = try decoder.decode(SystemStats.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(stats))
                }
            } catch {
                print("❌ JSON decode error: \(error)")
                if let jsonString = String(data: data, encoding: .utf8) {
                    print("📄 Response JSON: \(jsonString)")
                }
                DispatchQueue.main.async {
                    completion(.failure(APIError.decodingError(error)))
                }
            }
        }

        task.resume()
    }

    /// Stop any running pattern/game on the display
    func stopPattern(completion: ((Result<Void, Error>) -> Void)? = nil) {
        guard let url = URL(string: "\(baseURL)/api/stop-pattern") else {
            completion?(.failure(APIError.invalidURL))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let task = session.dataTask(with: request) { _, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion?(.failure(self.userFriendlyError(from: error)))
                }
                return
            }
            DispatchQueue.main.async {
                completion?(.success(()))
            }
        }
        task.resume()
    }

    /// Convert NSError to user-friendly error message
    private func userFriendlyError(from error: Error) -> Error {
        let nsError = error as NSError

        switch nsError.code {
        case NSURLErrorCannotConnectToHost, NSURLErrorNotConnectedToInternet:
            return APIError.cannotConnect
        case NSURLErrorTimedOut:
            return APIError.timeout
        case NSURLErrorCannotFindHost:
            return APIError.hostNotFound
        default:
            return error
        }
    }
}

// MARK: - API Errors

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case noData
    case httpError(statusCode: Int)
    case decodingError(Error)
    case cannotConnect
    case timeout
    case hostNotFound

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .invalidResponse:
            return "Invalid response from display"
        case .noData:
            return "No data received from display"
        case .httpError(let code):
            return "Server error (HTTP \(code))"
        case .decodingError:
            return "Failed to parse response from display"
        case .cannotConnect:
            return "Cannot connect to display - check WiFi connection"
        case .timeout:
            return "Display not responding - request timed out"
        case .hostNotFound:
            return "Cannot find display at raspberrypi.local"
        }
    }
}
