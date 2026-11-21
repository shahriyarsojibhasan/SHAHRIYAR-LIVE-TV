package com.shahriyarsojibhasan.shahriyarlivetv.model;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

public class Channel implements Serializable {
    private String id;
    private String name;
    private String url;
    private String logo;
    private String group;
    private Map<String, String> headers;
    private String drmScheme;
    private String licenseUrl;
    private String manifestType;

    public Channel(String id, String name, String url, String logo, String group) {
        this.id = id;
        this.name = name;
        this.url = url;
        this.logo = logo;
        this.group = group;
        this.headers = new HashMap<>();
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getUrl() { return url; }
    public String getLogo() { return logo; }
    public String getGroup() { return group; }
    public Map<String, String> getHeaders() { return headers; }
    public String getDrmScheme() { return drmScheme; }
    public String getLicenseUrl() { return licenseUrl; }
    public String getManifestType() { return manifestType; }

    public void setId(String id) { this.id = id; }
    public void setName(String name) { this.name = name; }
    public void setUrl(String url) { this.url = url; }
    public void setLogo(String logo) { this.logo = logo; }
    public void setGroup(String group) { this.group = group; }
    public void setHeaders(Map<String, String> headers) { this.headers = headers; }
    public void setDrmScheme(String drmScheme) { this.drmScheme = drmScheme; }
    public void setLicenseUrl(String licenseUrl) { this.licenseUrl = licenseUrl; }
    public void setManifestType(String manifestType) { this.manifestType = manifestType; }
    
    public void addHeader(String key, String value) {
        if (this.headers == null) this.headers = new HashMap<>();
        this.headers.put(key, value);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Channel channel = (Channel) o;
        return java.util.Objects.equals(id, channel.id) &&
                java.util.Objects.equals(name, channel.name) &&
                java.util.Objects.equals(url, channel.url) &&
                java.util.Objects.equals(logo, channel.logo) &&
                java.util.Objects.equals(group, channel.group);
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(id, name, url, logo, group);
    }
}
