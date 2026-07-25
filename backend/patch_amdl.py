#!/usr/bin/env python3
import os
import sys

def patch_file(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found for patching")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
        else:
            print(f"Notice: pattern not found in {filepath}: {old[:40]}...")

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully patched {filepath}")

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."

    # 1. Patch runv2.go and runv3.go for fast downloads (okhttp User-Agent)
    for sub in ["utils/runv2/runv2.go", "utils/runv3/runv3.go"]:
        p = os.path.join(root, sub)
        patch_file(p, [
            ('req.Header = header', 'req.Header = header\n\treq.Header.Set("User-Agent", "okhttp/4.12.0")')
        ])

    # 2. Patch lyrics.go for User-Agent, fallback from syllable-lyrics -> lyrics, & nil checks
    lyrics_p = os.path.join(root, "utils/lyrics/lyrics.go")
    patch_file(lyrics_p, [
        (
            'req.Header.Set("Origin", "https://music.apple.com")',
            'req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")\n\treq.Header.Set("Origin", "https://music.apple.com")'
        ),
        (
            'if obj.Data != nil {',
            'if obj.Data != nil && len(obj.Data) > 0 {'
        ),
        (
            'ttml, err := getSongLyrics(songId, storefront, token, mediaUserToken, lrcType, language)\n\tif err != nil {\n\t\treturn "", err\n\t}',
            'ttml, err := getSongLyrics(songId, storefront, token, mediaUserToken, lrcType, language)\n\tif err != nil && lrcType != "lyrics" {\n\t\tttml, err = getSongLyrics(songId, storefront, token, mediaUserToken, "lyrics", language)\n\t}\n\tif err != nil {\n\t\treturn "", err\n\t}'
        ),
        (
            'for _, item := range parsedTTML.FindElement("tt").FindElement("body").ChildElements() {',
            'ttElem := parsedTTML.FindElement("tt")\n\tif ttElem == nil {\n\t\treturn "", errors.New("missing tt element")\n\t}\n\tbodyElem := ttElem.FindElement("body")\n\tif bodyElem == nil {\n\t\treturn "", errors.New("missing body element")\n\t}\n\tfor _, item := range bodyElem.ChildElements() {'
        )
    ])

    # 3. Patch token.go for User-Agent when fetching developer token
    token_p = os.path.join(root, "utils/ampapi/token.go")
    patch_file(token_p, [
        (
            'req, err := http.NewRequest("GET", "https://music.apple.com", nil)',
            'req, err := http.NewRequest("GET", "https://music.apple.com", nil)\n\tif err == nil { req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") }'
        ),
        (
            'req, err = http.NewRequest("GET", "https://music.apple.com"+indexJsUri, nil)',
            'req, err = http.NewRequest("GET", "https://music.apple.com"+indexJsUri, nil)\n\tif err == nil { req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") }'
        )
    ])

if __name__ == "__main__":
    main()
