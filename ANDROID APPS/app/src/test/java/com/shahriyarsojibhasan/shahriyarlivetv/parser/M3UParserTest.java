package com.shahriyarsojibhasan.shahriyarlivetv.parser;

import static org.junit.Assert.*;
import org.junit.Test;
import com.shahriyarsojibhasan.shahriyarlivetv.model.Channel;
import java.util.List;

public class M3UParserTest {
    @Test
    public void testParseKodiProps() {
        String m3u = "#EXTM3U\n" +
                "#EXTINF:-1 tvg-logo=\"logo.png\" group-title=\"DRM\",Test Channel\n" +
                "#KODIPROP:inputstream.adaptive.license_type=clearkey\n" +
                "#KODIPROP:inputstream.adaptive.license_key=kid:key\n" +
                "#KODIPROP:inputstream.adaptive.manifest_type=mpd\n" +
                "https://test.com/stream.mpd";
        
        List<Channel> channels = M3UParser.parse(m3u);
        assertEquals(1, channels.size());
        Channel channel = channels.get(0);
        assertEquals("Test Channel", channel.getName());
        assertEquals("clearkey", channel.getDrmScheme());
        assertEquals("kid:key", channel.getLicenseUrl());
        assertEquals("mpd", channel.getManifestType());
    }

    @Test
    public void testParseHeaders() {
        String m3u = "#EXTINF:-1,Header Channel\n" +
                "#EXTVLCOPT:http-user-agent=TestAgent\n" +
                "https://test.com/stream.m3u8|Referer=https://ref.com";
        
        List<Channel> channels = M3UParser.parse(m3u);
        assertEquals(1, channels.size());
        Channel channel = channels.get(0);
        assertEquals("TestAgent", channel.getHeaders().get("User-Agent"));
        assertEquals("https://ref.com", channel.getHeaders().get("Referer"));
        assertEquals("https://ref.com", channel.getHeaders().get("Origin"));
    }
}
