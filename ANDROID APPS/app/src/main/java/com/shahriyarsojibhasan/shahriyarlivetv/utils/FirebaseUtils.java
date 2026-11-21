package com.shahriyarsojibhasan.shahriyarlivetv.utils;

import androidx.annotation.NonNull;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;

public class FirebaseUtils {
    private final String sessionId;
    private DatabaseReference currentChannelRef;
    private DatabaseReference currentUserRef;
    private ValueEventListener channelListener;

    public interface ViewerCountListener {
        void onCountChanged(long count);
    }

    public FirebaseUtils() {
        this.sessionId = UUID.randomUUID().toString();
    }

    private String getMd5(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] messageDigest = md.digest(input.getBytes());
            StringBuilder hexString = new StringBuilder();
            for (byte b : messageDigest) {
                String h = Integer.toHexString(0xFF & b);
                if (h.length() < 2) hexString.append("0");
                hexString.append(h);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            return String.valueOf(input.hashCode());
        }
    }

    public void trackChannel(String channelUrl, ViewerCountListener listener) {
        // Use MD5 hash to ensure key length is always short and safe
        String safeId = getMd5(channelUrl);

        if (currentUserRef != null) {
            currentUserRef.removeValue();
            currentUserRef.onDisconnect().cancel();
        }
        if (currentChannelRef != null && channelListener != null) {
            currentChannelRef.removeEventListener(channelListener);
        }

        currentChannelRef = FirebaseDatabase.getInstance().getReference("live_viewers").child(safeId);
        currentUserRef = currentChannelRef.child(sessionId);

        currentUserRef.setValue(true);
        currentUserRef.onDisconnect().removeValue();

        channelListener = new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                listener.onCountChanged(snapshot.getChildrenCount());
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {}
        };
        currentChannelRef.addValueEventListener(channelListener);
    }
    
    public void cleanup() {
        if (currentUserRef != null) {
            currentUserRef.removeValue();
        }
        if (currentChannelRef != null && channelListener != null) {
            currentChannelRef.removeEventListener(channelListener);
        }
    }

    public void checkUpdate(UpdateListener listener) {
        FirebaseDatabase.getInstance().getReference("app_config")
                .addListenerForSingleValueEvent(new ValueEventListener() {
                    @Override
                    public void onDataChange(@NonNull DataSnapshot snapshot) {
                        if (snapshot.exists()) {
                            long latestVersion = snapshot.child("version_code").getValue(Long.class);
                            String updateUrl = snapshot.child("update_url").getValue(String.class);
                            listener.onUpdateChecked(latestVersion, updateUrl);
                        }
                    }

                    @Override
                    public void onCancelled(@NonNull DatabaseError error) {}
                });
    }

    public interface UpdateListener {
        void onUpdateChecked(long latestVersionCode, String updateUrl);
    }
}
