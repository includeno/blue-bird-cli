import AppKit
import ApplicationServices
import Foundation

struct Failure: Error { let message: String }
func fail(_ s: String) throws -> Never { throw Failure(message: s) }
func attribute(_ e: AXUIElement, _ name: String) -> CFTypeRef? {
    var value: CFTypeRef?
    return AXUIElementCopyAttributeValue(e, name as CFString, &value) == .success ? value : nil
}
func string(_ e: AXUIElement, _ name: String) -> String { attribute(e, name) as? String ?? "" }
func children(_ e: AXUIElement) -> [AXUIElement] { attribute(e, kAXChildrenAttribute) as? [AXUIElement] ?? [] }
func actions(_ e: AXUIElement) -> [[String: String]] {
    var names: CFArray?
    AXUIElementCopyActionNames(e, &names)
    return (names as? [String] ?? []).map { name in
        var desc: CFString?
        AXUIElementCopyActionDescription(e, name as CFString, &desc)
        return ["name": name, "description": desc as String? ?? ""]
    }
}
func walk(_ element: AXUIElement, _ path: [Int] = []) -> [(AXUIElement, [Int])] {
    if path.count > 30 { return [] }
    return [(element, path)] + children(element).enumerated().flatMap { index, child in
        walk(child, path + [index])
    }
}
func record(_ e: AXUIElement) -> [String: Any] {
    var result: [String: Any] = ["role": string(e, kAXRoleAttribute),
        "title": string(e, kAXTitleAttribute), "description": string(e, kAXDescriptionAttribute),
        "value_description": string(e, kAXValueDescriptionAttribute), "identifier": string(e, kAXIdentifierAttribute), "placeholder": string(e, "AXPlaceholderValue"), "actions": actions(e)]
    if let v = attribute(e, kAXValueAttribute), CFGetTypeID(v) == CFStringGetTypeID() || CFGetTypeID(v) == CFNumberGetTypeID() { if let number = v as? NSNumber, !number.doubleValue.isFinite { result["value"] = NSNull() } else { result["value"] = v } }
    if let v = attribute(e, kAXFocusedAttribute) as? Bool { result["focused"] = v }
    if let v = attribute(e, kAXSelectedAttribute) as? Bool { result["selected"] = v }
    return result
}
func emit(_ obj: [String: Any]) { let d = try! JSONSerialization.data(withJSONObject: obj, options: [.sortedKeys]); print(String(data: d, encoding: .utf8)!) }

do {
    let request = try JSONSerialization.jsonObject(with: FileHandle.standardInput.readDataToEndOfFile()) as? [String: Any] ?? [:]
    let op = request["op"] as? String ?? "snapshot"
    if op == "resources" {
        let bundleID = "com.cub-and-pup.Bluebird"
        let supplied = request["app_path"] as? String
        let url = supplied.map { URL(fileURLWithPath: $0) }
            ?? NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleID)
            ?? ["/Applications/Bluebird.app", NSHomeDirectory() + "/Applications/Bluebird.app"]
                .map { URL(fileURLWithPath: $0) }.first { FileManager.default.fileExists(atPath: $0.path) }
        guard let url = url, let bundle = Bundle(url: url), bundle.bundleIdentifier == bundleID,
              let resources = bundle.resourceURL else { try fail("A valid Bluebird.app bundle could not be found") }
        let keys = request["keys"] as? [String] ?? []
        var tables: [String: [String: String]] = [:]
        for locale in bundle.localizations where locale != "Base" {
            let file = resources.appendingPathComponent(locale + ".lproj/Localizable.strings")
            guard let data = try? Data(contentsOf: file),
                  let values = try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any]
            else { try fail("Could not read localization: \(locale)") }
            tables[locale] = values.filter { keys.contains($0.key) }.compactMapValues { $0 as? String }
        }
        let appLanguages = CFPreferencesCopyAppValue("AppleLanguages" as CFString, bundleID as CFString) as? [String]
        let preferences = appLanguages ?? Locale.preferredLanguages
        emit(["path": url.path, "version": bundle.infoDictionary?["CFBundleShortVersionString"] as? String ?? "unknown",
              "localizations": tables,
              "preferred_localizations": Bundle.preferredLocalizations(from: Array(tables.keys), forPreferences: preferences)])
        exit(0)
    }
    if op == "doctor" { emit(["trusted": AXIsProcessTrusted()]); exit(0) }
    guard AXIsProcessTrusted() else { try fail("ACCESSIBILITY_REQUIRED: Enable Accessibility for your terminal/Codex and the bluebird-ax executable in System Settings > Privacy & Security > Accessibility.") }
    guard let app = NSRunningApplication.runningApplications(withBundleIdentifier: "com.cub-and-pup.Bluebird").first else { try fail("Bluebird is not running. Run bluebird --full-access open first.") }
    let root = AXUIElementCreateApplication(app.processIdentifier)
    AXUIElementSetMessagingTimeout(root, 3)
    if op == "activate" { app.activate(options: []); emit(["ok": true]); exit(0) }
    if op == "key" {
        guard let key = request["key"] as? Int, [36,48,53,51,0].contains(key) else { try fail("Unsupported key") }
        let flags: CGEventFlags = request["command"] as? Bool == true ? .maskCommand : []
        app.activate(options: [])
        Thread.sleep(forTimeInterval: 0.1)
        for down in [true, false] {
            let event = CGEvent(keyboardEventSource: nil, virtualKey: CGKeyCode(key), keyDown: down)!
            event.flags = flags
            // Catalyst needs the Return character to submit text fields.
            if key == 36 { event.keyboardSetUnicodeString(stringLength: 1, unicodeString: [13]) }
            event.postToPid(app.processIdentifier)
            Thread.sleep(forTimeInterval: 0.05)
        }
        emit(["ok": true]); exit(0)
    }
    let tree = walk(root)
    if op == "snapshot" {
        emit(["nodes": tree.map { element, path -> [String: Any] in
            var node = record(element)
            node["path"] = path
            return node
        }])
        exit(0)
    }
    guard let selector = request["selector"] as? [String: Any], !selector.isEmpty else { try fail("Missing selector") }
    let attrs = ["role": kAXRoleAttribute, "title": kAXTitleAttribute, "description": kAXDescriptionAttribute, "identifier": kAXIdentifierAttribute, "placeholder": "AXPlaceholderValue", "value": kAXValueAttribute]
    let matches = tree.filter { element, path in selector.allSatisfy { key, value in
        if key == "path" { return (value as? [Int]) == path }
        guard let attr = attrs[key], let expected = value as? String else { return false }
        return string(element, attr) == expected
    }}
    guard matches.count == 1 else { try fail("Expected one UI element, found \(matches.count); refresh the UI snapshot") }
    let element = matches[0].0
    if op == "set" {
        guard let value = request["value"] as? String else { try fail("Missing value") }
        let err = AXUIElementSetAttributeValue(element, kAXValueAttribute as CFString, value as CFString)
        guard err == .success else { try fail("AX set failed: \(err.rawValue)") }
    } else if op == "type" {
        app.activate(options: [])
        Thread.sleep(forTimeInterval: 0.1)
        guard let value = request["value"] as? String else { try fail("Missing value") }
        let err = AXUIElementPerformAction(element, kAXPressAction as CFString)
        guard err == .success else { try fail("Could not focus text input") }
        let focused = AXUIElementSetAttributeValue(element, kAXFocusedAttribute as CFString, kCFBooleanTrue)
        guard focused == .success else { try fail("Could not focus text input: \(focused.rawValue)") }
        Thread.sleep(forTimeInterval: 0.1)
        let original = string(element, kAXValueAttribute)
        var selection = CFRange(location: 0, length: original.utf16.count)
        if let value = AXValueCreate(.cfRange, &selection) {
            AXUIElementSetAttributeValue(element, kAXSelectedTextRangeAttribute as CFString, value)
        }
        for down in [true, false] {
            let event = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: down)!
            event.keyboardSetUnicodeString(stringLength: 1, unicodeString: [97])
            event.flags = .maskCommand; event.postToPid(app.processIdentifier)
        }
        Thread.sleep(forTimeInterval: 0.1)
        guard let selected = attribute(element, kAXSelectedTextRangeAttribute),
              CFGetTypeID(selected) == AXValueGetTypeID() else { try fail("Text selection cannot be verified; no replacement sent") }
        var actual = CFRange()
        guard AXValueGetValue(selected as! AXValue, .cfRange, &actual),
              actual.location == 0, actual.length == original.utf16.count else {
            try fail("Entire text is not selected; no replacement sent")
        }
        for down in [true, false] {
            let event = CGEvent(keyboardEventSource: nil, virtualKey: value.isEmpty ? 51 : 0, keyDown: down)!
            event.flags = []
            if !value.isEmpty {
                let chars = Array(value.utf16)
                event.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: chars)
            }
            event.postToPid(app.processIdentifier)
        }
    } else if op == "action" {
        let requested = request["action"] as? String ?? kAXPressAction
        let found = actions(element).filter { $0["name"] == requested || $0["description"] == requested }
        guard found.count == 1, let name = found[0]["name"] else { try fail("Action unavailable: \(requested)") }
        let err = AXUIElementPerformAction(element, name as CFString)
        guard err == .success else { try fail("AX action failed: \(err.rawValue)") }
    } else { try fail("Unknown operation: \(op)") }
    emit(["ok": true])
} catch {
    emit(["error": (error as? Failure)?.message ?? error.localizedDescription]); exit(1)
}
