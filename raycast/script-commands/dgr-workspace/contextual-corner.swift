import AppKit
import CoreGraphics

private let largeDisplayMinWidth: CGFloat = 2_500
private let minimumNormalWindowDimension: CGFloat = 100
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

// Rectangle repeats first-third/last-third across the display. Choose the half
// explicitly when this window is already in that side's third instead.
func sideAction(for placement: String, windowFrame: CGRect, screenFrame: CGRect,
                gapSize: CGFloat = 0, skipTopGap: Bool = false) -> String {
    let isLeft = placement == "left-side"
    let thirdAction = isLeft ? "first-third" : "last-third"
    // Rectangle rotates first/last thirds to top/bottom on portrait displays.
    // Preserve that native behavior instead of switching axes to a side half.
    guard screenFrame.width > screenFrame.height else { return thirdAction }

    var third = screenFrame
    third.size.width = floor(screenFrame.width / 3)
    if !isLeft { third.origin.x = screenFrame.maxX - third.width }

    third = third.insetBy(dx: gapSize, dy: gapSize)
    third.size.width += gapSize / 2
    if !isLeft { third.origin.x -= gapSize / 2 }
    if skipTopGap { third.size.height += gapSize }

    // Terminal windows snap to character cells, so their edges can differ by
    // more than a pixel even after Rectangle successfully places them.
    let tolerance: CGFloat = 24
    let matchesThird = abs(windowFrame.minX - third.minX) <= tolerance
        && abs(windowFrame.minY - third.minY) <= tolerance
        && abs(windowFrame.maxX - third.maxX) <= tolerance
        && abs(windowFrame.maxY - third.maxY) <= tolerance
    if matchesThird { return isLeft ? "left-half" : "right-half" }
    return thirdAction
}

private func frontWindowGeometry() -> (window: CGRect, screen: NSScreen) {
    let screens = NSScreen.screens
    guard let primaryScreen = screens.first,
          let pid = NSWorkspace.shared.frontmostApplication?.processIdentifier,
          let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID)
            as? [[String: Any]] else {
        fputs("Could not read the front window for side tiling.\n", stderr)
        exit(1)
    }

    // The list is front to back. Bounds and owner PIDs do not require Screen
    // Recording permission; do not read window titles or capture window contents.
    // Some apps expose transient layer-zero surfaces with a tiny dimension
    // ahead of their normal document window; those are not tiling targets.
    for info in windows where (info[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid
        && (info[kCGWindowLayer as String] as? Int) == 0 {
        guard let bounds = info[kCGWindowBounds as String] as? [String: Any],
              var frame = CGRect(dictionaryRepresentation: bounds as CFDictionary),
              frame.width >= minimumNormalWindowDimension,
              frame.height >= minimumNormalWindowDimension else { continue }
        // Window Server coordinates start at the primary display's top left;
        // NSScreen coordinates start at its bottom left, including other displays.
        frame.origin.y = primaryScreen.frame.maxY - frame.maxY
        guard let screen = screens.max(by: {
            let first = frame.intersection($0.frame)
            let second = frame.intersection($1.frame)
            return first.width * first.height < second.width * second.height
        }), !frame.intersection(screen.frame).isNull else { continue }
        return (frame, screen)
    }

    fputs("No visible front window was found for side tiling.\n", stderr)
    exit(1)
}

private func sideAction(for placement: String) -> String {
    let geometry = frontWindowGeometry()
    guard let preferences = UserDefaults(suiteName: "com.knollsoft.Rectangle") else {
        fputs("Could not read Rectangle's window gap settings.\n", stderr)
        exit(1)
    }
    var screenFrame = geometry.screen.visibleFrame
    if !preferences.bool(forKey: "screenEdgeGapsOnMainScreenOnly") || geometry.screen == NSScreen.screens.first {
        let left = CGFloat(preferences.double(forKey: "screenEdgeGapLeft"))
        let right = CGFloat(preferences.double(forKey: "screenEdgeGapRight"))
        let bottom = CGFloat(preferences.double(forKey: "screenEdgeGapBottom"))
        var top = CGFloat(preferences.double(forKey: "screenEdgeGapTop"))
        if #available(macOS 12.0, *), geometry.screen.safeAreaInsets.top != 0,
           preferences.double(forKey: "screenEdgeGapTopNotch") != 0 {
            top = CGFloat(preferences.double(forKey: "screenEdgeGapTopNotch"))
        }
        screenFrame.origin.x += left
        screenFrame.origin.y += bottom
        screenFrame.size.width -= left + right
        screenFrame.size.height -= top + bottom
    }
    return sideAction(for: placement, windowFrame: geometry.window, screenFrame: screenFrame,
                      gapSize: CGFloat(preferences.double(forKey: "gapSize")),
                      skipTopGap: preferences.bool(forKey: "skipGapTopEdge"))
}

private func rectangleAction(for placement: String) -> String {
    switch placement {
    case "left-side":
        return usesLargeDisplayLayout() ? sideAction(for: placement) : "left-half"
    case "middle-third":
        return "center-third"
    case "right-side":
        return usesLargeDisplayLayout() ? sideAction(for: placement) : "right-half"
    default:
        return usesLargeDisplayLayout() ? "\(placement)-sixth" : placement
    }
}

#if !WINDOW_TILING_TESTS
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
#endif
