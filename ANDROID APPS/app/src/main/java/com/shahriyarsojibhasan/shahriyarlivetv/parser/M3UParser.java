package com.shahriyarsojibhasan.shahriyarlivetv.parser;

import com.shahriyarsojibhasan.shahriyarlivetv.model.Channel;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import android.net.Uri;

public class M3UParser {
    private static final String DEFAULT_LOGO = "https://blogger.googleusercontent.com/img/a/AVvXsEjz0o_rUO-ESkNHIPrS97j51IBvyY35Z8GmEmmDOLQtRmErsvwvDka4XGmqpDlcDy6iNkfo3mc-ApousuAR4mrZoFlGYeBSO6HKxnlM62ODaMOAhOIAzXp34Q5pO39RV6UIKS-WjKFLh6tLB3KLHxqTivKYmRTdnZEmm9xUZw5tFeZ5YakHpd0jF3DU";

    public static List<Channel> parse(String content) {
        List<Channel> channels = new ArrayList<>();
        if (content == null || content.isEmpty()) return channels;

        content = content.trim();
        if (content.startsWith("\uFEFF")) {
            content = content.substring(1);
        }

        String[] lines = content.split("\\r?\\n");
        String currentName = "";
        String currentLogo = DEFAULT_LOGO;
        String currentGroup = "Uncategorized";
        Map<String, String> currentHeaders = new HashMap<>();
        String currentDrmScheme = null;
        String currentLicenseUrl = null;
        String currentManifestType = null;
        int channelCounter = 1;

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.isEmpty()) continue;

            if (line.startsWith("#EXTINF:")) {
                int lastComma = line.lastIndexOf(",");
                if (lastComma != -1 && lastComma < line.length() - 1) {
                    currentName = line.substring(lastComma + 1).trim()
                            .replace(" | SHAHRIYAR LIVE TV", "");
                } else {
                    currentName = "Channel " + channelCounter;
                }

                currentLogo = parseAttribute(line, "tvg-logo", DEFAULT_LOGO);
                currentGroup = parseAttribute(line, "group-title", "Uncategorized");

            } else if (line.startsWith("#KODIPROP:")) {
                String prop = line.substring(10).trim();
                if (prop.contains("=")) {
                    String[] kv = prop.split("=", 2);
                    String key = kv[0].trim();
                    String val = kv[1].trim();
                    if (key.contains("license_type")) currentDrmScheme = val;
                    else if (key.contains("license_key")) currentLicenseUrl = val;
                    else if (key.contains("manifest_type")) currentManifestType = val;
                }
            } else if (line.startsWith("#EXTVLCOPT:")) {
                String opt = line.substring(11).trim();
                parseAndAddHeader(currentHeaders, opt);
            } else if (line.startsWith("#EXTHTTP:")) {
                String jsonStr = line.substring(9).trim();
                try {
                    JSONObject json = new JSONObject(jsonStr);
                    Iterator<String> keys = json.keys();
                    while (keys.hasNext()) {
                        String key = keys.next();
                        currentHeaders.put(key, json.getString(key));
                    }
                } catch (Exception e) {
                    // Fallback to key-value if not perfect JSON
                    parseAndAddHeader(currentHeaders, jsonStr);
                }
            } else if (line.startsWith("#EXT-X-SESSION-KEY:") || line.startsWith("#EXT-X-KEY:")) {
                // Common HLS DRM keys
                if (line.contains("URI=\"")) {
                    String uri = parseAttribute(line, "URI", null);
                    if (uri != null) currentLicenseUrl = uri;
                }
                if (line.contains("KEYFORMAT=\"clearkey\"")) {
                    currentDrmScheme = "clearkey";
                } else if (line.contains("KEYFORMAT=\"com.widevine.alpha\"")) {
                    currentDrmScheme = "widevine";
                }
            } else if (!line.startsWith("#")) {
                String url = line;
                Map<String, String> headers = new HashMap<>(currentHeaders);
                
                if (url.contains("|")) {
                    String[] parts = url.split("\\|");
                    url = parts[0].trim();
                    for (int j = 1; j < parts.length; j++) {
                        parseAndAddHeader(headers, parts[j].trim());
                    }
                }
                
                String id = "SHAHRIYAR_CH" + channelCounter;
                Channel channel = new Channel(id, currentName.isEmpty() ? "Channel " + channelCounter : currentName, url, currentLogo, currentGroup);
                if (!headers.isEmpty()) {
                    channel.setHeaders(headers);
                }
                channel.setDrmScheme(currentDrmScheme);
                channel.setLicenseUrl(currentLicenseUrl);
                channel.setManifestType(currentManifestType);

                channels.add(channel);
                channelCounter++;
                
                currentName = "";
                currentLogo = DEFAULT_LOGO;
                currentGroup = "Uncategorized";
                currentHeaders.clear();
                currentDrmScheme = null;
                currentLicenseUrl = null;
                currentManifestType = null;
            }
        }
        return channels;
    }

    private static void parseAndAddHeader(Map<String, String> headers, String part) {
        // Handle http-user-agent, User-Agent, cookie, etc.
        String[] pairs = part.split("[&,]");
        for (String pair : pairs) {
            if (pair.contains("=")) {
                String[] kv = pair.split("=", 2);
                String key = kv[0].trim();
                String val = kv[1].trim();
                
                // Remove http- prefix if present for standardization
                if (key.startsWith("http-")) key = key.substring(5);
                
                // Standardize case
                if (key.equalsIgnoreCase("user-agent")) headers.put("User-Agent", val);
                else if (key.equalsIgnoreCase("referer")) {
                    headers.put("Referer", val);
                    // Automatically add Origin if Referer is present
                    if (!headers.containsKey("Origin")) {
                        String origin = getOriginFromUrl(val);
                        if (origin != null) headers.put("Origin", origin);
                    }
                }
                else if (key.equalsIgnoreCase("origin")) headers.put("Origin", val);
                else if (key.equalsIgnoreCase("cookie")) headers.put("Cookie", val);
                else headers.put(key, val);
            }
        }
    }

    private static String getOriginFromUrl(String url) {
        if (url == null || !url.contains("://")) return null;
        try {
            int schemeEnd = url.indexOf("://") + 3;
            int hostEnd = url.indexOf("/", schemeEnd);
            if (hostEnd == -1) return url;
            return url.substring(0, hostEnd);
        } catch (Exception e) {
            return null;
        }
    }

    private static String parseAttribute(String line, String attribute, String defaultValue) {
        Pattern pattern = Pattern.compile(attribute + "=\"(.*?)\"");
        Matcher matcher = pattern.matcher(line);
        if (matcher.find()) {
            String val = matcher.group(1);
            return (val != null && !val.isEmpty()) ? val : defaultValue;
        }
        return defaultValue;
    }
}
