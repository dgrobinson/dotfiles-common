import AppKit

private let largeDisplayMinWidth: CGFloat = 2_500
private let validPlacements = Set([
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "left-side",
    "middle-third",
    "right-side",
])

private func usage() -> Never {
    fputs("Usage: contextual-corner <top-left|top-right|bottom-left|bottom-right|left-side|middle-third|right-side> [--dry-run]\n", stderr)
    exit(2)
}

private func usesLargeDisplayLayout() -> Bool {
    NSScreen.screens.contains { $0.frame.width >= largeDisplayMinWidth }
}

private func rectangleAction(for placement: String) -> String {
    switch placement {
    case "left-side":
        return usesLargeDisplayLayout() ? "first-third" : "left-half"
    case "middle-third":
        return "center-third"
    case "right-side":
        return usesLargeDisplayLayout() ? "last-third" : "right-half"
    default:
        return usesLargeDisplayLayout() ? "\(placement)-sixth" : placement
    }
}

let arguments = CommandLine.arguments.dropFirst()

guard let placement = arguments.first, validPlacements.contains(placement) else {
    usage()
}

let action = rectangleAction(for: placement)

if arguments.contains("--dry-run") {
    let screenSizes = NSScreen.screens
        .map { "\(Int($0.frame.width))x\(Int($0.frame.height))" }
        .sorted()
        .joined(separator: ",")
    print("\(screenSizes) \(action)")
    exit(0)
}

guard let url = URL(string: "rectangle://execute-action?name=\(action)") else {
    fputs("Could not construct Rectangle URL.\n", stderr)
    exit(1)
}

NSWorkspace.shared.open(url)
