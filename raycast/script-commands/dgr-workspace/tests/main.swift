import AppKit

var checks = 0

func expect(_ name: String, _ placement: String, _ window: CGRect, _ screen: CGRect,
            _ expected: String, gap: CGFloat = 0, skipTopGap: Bool = false) {
    let actual = sideAction(for: placement, windowFrame: window, screenFrame: screen,
                            gapSize: gap, skipTopGap: skipTopGap)
    precondition(actual == expected, "\(name): expected \(expected), got \(actual)")
    checks += 1
}

let screen = CGRect(x: 0, y: 30, width: 3000, height: 1900)
expect("A repeats to a half", "left-side", CGRect(x: 0, y: 30, width: 1000, height: 1900), screen, "left-half")
expect("A returns from a half", "left-side", CGRect(x: 0, y: 30, width: 1500, height: 1900), screen, "first-third")
expect("F repeats to a half", "right-side", CGRect(x: 2000, y: 30, width: 1000, height: 1900), screen, "right-half")
expect("F returns from a half", "right-side", CGRect(x: 1500, y: 30, width: 1500, height: 1900), screen, "last-third")
expect("A from the center", "left-side", CGRect(x: 1000, y: 30, width: 1000, height: 1900), screen, "first-third")
expect("F from the center", "right-side", CGRect(x: 1000, y: 30, width: 1000, height: 1900), screen, "last-third")
expect("A from the opposite side", "left-side", CGRect(x: 2000, y: 30, width: 1000, height: 1900), screen, "first-third")
expect("F from the opposite side", "right-side", CGRect(x: 0, y: 30, width: 1000, height: 1900), screen, "last-third")
expect("A from a corner sixth", "left-side", CGRect(x: 0, y: 980, width: 1000, height: 950), screen, "first-third")
expect("A from an untiled window", "left-side", CGRect(x: 200, y: 180, width: 900, height: 1200), screen, "first-third")
expect("App rounding", "left-side", CGRect(x: 1, y: 31, width: 999, height: 1899), screen, "left-half")
expect("Terminal cell rounding on left", "left-side", CGRect(x: 0, y: 46, width: 984, height: 1884), screen, "left-half")
expect("Terminal cell rounding on right", "right-side", CGRect(x: 2016, y: 46, width: 984, height: 1884), screen, "right-half")
expect("Outside rounding tolerance", "left-side", CGRect(x: 25, y: 30, width: 1000, height: 1900), screen, "first-third")
expect("Left third with gaps", "left-side", CGRect(x: 10, y: 40, width: 985, height: 1880), screen, "left-half", gap: 10)
expect("Right third with gaps", "right-side", CGRect(x: 2005, y: 40, width: 985, height: 1880), screen, "right-half", gap: 10)
expect("Skip top gap", "left-side", CGRect(x: 10, y: 40, width: 985, height: 1890), screen, "left-half", gap: 10, skipTopGap: true)

let otherScreen = CGRect(x: -3001, y: 900, width: 3001, height: 1800)
expect("Display left and above primary", "right-side", CGRect(x: -1000, y: 900, width: 1000, height: 1800), otherScreen, "right-half")
let insetScreen = CGRect(x: 12, y: 50, width: 2970, height: 1834)
expect("Asymmetric screen insets", "left-side", CGRect(x: 24, y: 62, width: 972, height: 1810), insetScreen, "left-half", gap: 12)

let portrait = CGRect(x: 3000, y: -900, width: 1400, height: 2700)
expect("Portrait A preserves first third", "left-side", CGRect(x: 3000, y: 900, width: 1400, height: 900), portrait, "first-third")
expect("Portrait F preserves last third", "right-side", CGRect(x: 3000, y: -900, width: 1400, height: 900), portrait, "last-third")
expect("Portrait A preserves first third with gaps", "left-side", CGRect(x: 3010, y: 905, width: 1380, height: 885), portrait, "first-third", gap: 10)
expect("Portrait F preserves last third with gaps", "right-side", CGRect(x: 3010, y: -890, width: 1380, height: 885), portrait, "last-third", gap: 10)
expect("Portrait A ignores skip-top matching", "left-side", CGRect(x: 3010, y: 905, width: 1380, height: 895), portrait, "first-third", gap: 10, skipTopGap: true)

print("Passed \(checks) window tiling checks")
