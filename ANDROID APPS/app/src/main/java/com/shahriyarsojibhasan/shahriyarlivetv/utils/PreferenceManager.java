package com.shahriyarsojibhasan.shahriyarlivetv.utils;

import android.content.Context;
import android.content.SharedPreferences;

public class PreferenceManager {
    private static final String PREF_NAME = "ShahriyarLiveTVPrefs";
    private static final String KEY_INSTALL_DISMISSED = "install_dismissed";
    
    private final SharedPreferences sharedPreferences;

    public PreferenceManager(Context context) {
        sharedPreferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    public void setInstallDismissed(boolean dismissed) {
        sharedPreferences.edit().putBoolean(KEY_INSTALL_DISMISSED, dismissed).apply();
    }

    public boolean isInstallDismissed() {
        return sharedPreferences.getBoolean(KEY_INSTALL_DISMISSED, false);
    }
}
