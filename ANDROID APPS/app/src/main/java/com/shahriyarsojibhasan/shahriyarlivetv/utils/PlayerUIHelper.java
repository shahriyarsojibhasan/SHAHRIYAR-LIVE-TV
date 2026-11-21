package com.shahriyarsojibhasan.shahriyarlivetv.utils;

import android.view.View;
import android.widget.ImageButton;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.media3.common.Player;
import androidx.media3.common.util.UnstableApi;
import com.shahriyarsojibhasan.shahriyarlivetv.R;
import com.shahriyarsojibhasan.shahriyarlivetv.ui.SpringProgressDrawable;
import java.util.Locale;

@UnstableApi
public class PlayerUIHelper {
    private final View controller;
    private final Player player;
    private final ImageButton btnPlayPause;
    private final SeekBar seekBar;
    private final TextView txtPosition;
    private final TextView txtDuration;
    private final ImageButton btnFullscreen;
    private final ImageButton btnSettings;
    private final ImageButton btnVolume;
    private boolean isMuted = false;
    private float lastVolume = 1f;

    public interface PlayerUIListener {
        void onFullscreenClick();
        void onSettingsClick();
        void onUserInteraction();
    }

    public PlayerUIHelper(View controller, Player player, PlayerUIListener listener) {
        this.controller = controller;
        this.player = player;

        btnPlayPause = controller.findViewById(R.id.exo_play_pause);
        seekBar = controller.findViewById(R.id.exo_progress);
        txtPosition = controller.findViewById(R.id.exo_position);
        txtDuration = controller.findViewById(R.id.exo_duration);
        btnFullscreen = controller.findViewById(R.id.exo_fullscreen);
        btnSettings = controller.findViewById(R.id.btnSettings);
        btnVolume = controller.findViewById(R.id.btnVolume);

        setupSpringProgress();
        setupListeners(listener);
    }

    private void setupSpringProgress() {
        int stripeColor = controller.getContext().getColor(R.color.primary_color);
        int bgColor = 0x1AFFFFFF; // Modern subtle track color
        
        SpringProgressDrawable springProgress = new SpringProgressDrawable(bgColor, stripeColor);
        seekBar.setProgressDrawable(springProgress);
    }

    private void setupListeners(PlayerUIListener listener) {
        View.OnClickListener playPauseClick = v -> {
            listener.onUserInteraction();
            if (player.isPlaying()) {
                player.pause();
            } else {
                player.play();
            }
        };

        if (btnPlayPause != null) btnPlayPause.setOnClickListener(playPauseClick);

        if (btnFullscreen != null) btnFullscreen.setOnClickListener(v -> {
            listener.onUserInteraction();
            listener.onFullscreenClick();
        });
        if (btnSettings != null) btnSettings.setOnClickListener(v -> {
            listener.onUserInteraction();
            listener.onSettingsClick();
        });
        
        if (btnVolume != null) {
            btnVolume.setOnClickListener(v -> {
                listener.onUserInteraction();
                isMuted = !isMuted;
                if (isMuted) {
                    lastVolume = player.getVolume();
                    player.setVolume(0f);
                    btnVolume.setImageResource(R.drawable.ic_volume_off);
                } else {
                    player.setVolume(lastVolume > 0 ? lastVolume : 1f);
                    btnVolume.setImageResource(R.drawable.ic_volume_up);
                }
            });
        }

        player.addListener(new Player.Listener() {
            @Override
            public void onIsPlayingChanged(boolean isPlaying) {
                int icon = isPlaying ? R.drawable.ic_pause : R.drawable.ic_play;
                if (btnPlayPause != null) btnPlayPause.setImageResource(icon);
            }
            
            @Override
            public void onVolumeChanged(float volume) {
                if (btnVolume == null) return;
                if (volume > 0) {
                    btnVolume.setImageResource(R.drawable.ic_volume_up);
                    isMuted = false;
                } else {
                    btnVolume.setImageResource(R.drawable.ic_volume_off);
                    isMuted = true;
                }
            }
        });

        if (seekBar != null) {
            seekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                @Override
                public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                    if (fromUser) {
                        listener.onUserInteraction();
                        player.seekTo(progress);
                    }
                }
                @Override
                public void onStartTrackingTouch(SeekBar seekBar) {}
                @Override
                public void onStopTrackingTouch(SeekBar seekBar) {}
            });
        }
    }

    public void updateProgress() {
        if (player == null || seekBar == null) return;
        
        long position = player.getCurrentPosition();
        long duration = player.getDuration();
        
        if (duration > 0) {
            seekBar.setMax((int) duration);
            seekBar.setProgress((int) position);
            if (txtDuration != null) txtDuration.setText(formatTime(duration));
        } else {
            seekBar.setMax(0);
            seekBar.setProgress(0);
            if (txtDuration != null) txtDuration.setText("LIVE");
        }
        if (txtPosition != null) txtPosition.setText(formatTime(position));
    }

    private String formatTime(long ms) {
        if (ms < 0) return "00:00";
        int totalSeconds = (int) (ms / 1000);
        int seconds = totalSeconds % 60;
        int minutes = (totalSeconds / 60) % 60;
        int hours = totalSeconds / 3600;
        if (hours > 0) {
            return String.format(Locale.getDefault(), "%02d:%02d:%02d", hours, minutes, seconds);
        } else {
            return String.format(Locale.getDefault(), "%02d:%02d", minutes, seconds);
        }
    }
}
