package com.shahriyarsojibhasan.shahriyarlivetv;

import android.content.Intent;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.net.Uri;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.MenuItem;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.view.animation.RotateAnimation;
import android.widget.ImageButton;
import android.widget.PopupMenu;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.media3.common.MediaItem;
import androidx.media3.common.Player;
import androidx.media3.common.TrackSelectionOverride;
import androidx.media3.common.Tracks;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DefaultHttpDataSource;
import androidx.media3.datasource.HttpDataSource;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import androidx.media3.exoplayer.source.MediaSource;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.bumptech.glide.Glide;
import com.shahriyarsojibhasan.shahriyarlivetv.adapter.ChannelAdapter;
import com.shahriyarsojibhasan.shahriyarlivetv.databinding.ActivityMainBinding;
import com.shahriyarsojibhasan.shahriyarlivetv.model.Channel;
import com.shahriyarsojibhasan.shahriyarlivetv.parser.M3UParser;
import com.shahriyarsojibhasan.shahriyarlivetv.utils.FirebaseUtils;
import com.shahriyarsojibhasan.shahriyarlivetv.utils.PlayerUIHelper;
import com.shahriyarsojibhasan.shahriyarlivetv.utils.PreferenceManager;
import com.shahriyarsojibhasan.shahriyarlivetv.utils.ToastUtils;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

@UnstableApi
public class MainActivity extends AppCompatActivity implements PlayerUIHelper.PlayerUIListener {
    private ActivityMainBinding binding;
    private ExoPlayer player;
    private ChannelAdapter adapter;
    private List<Channel> allChannels = new ArrayList<>();
    private FirebaseUtils firebaseUtils;
    private PlayerUIHelper playerUIHelper;
    private PreferenceManager preferenceManager;
    private final OkHttpClient client = new OkHttpClient.Builder()
            .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .build();
    private final android.os.Handler scrollHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private Runnable scrollRunnable;
    private long lastBackPressedTime = 0;

    private static final String M3U_URL = "https://raw.githubusercontent.com/shahriyarsojibhasan/SHAHRIYAR-LIVE-TV/refs/heads/main/SHAHRIYAR-LIVE-TV-APP.m3u";
    private static final String LOGO_URL = "https://blogger.googleusercontent.com/img/a/AVvXsEjz0o_rUO-ESkNHIPrS97j51IBvyY35Z8GmEmmDOLQtRmErsvwvDka4XGmqpDlcDy6iNkfo3mc-ApousuAR4mrZoFlGYeBSO6HKxnlM62ODaMOAhOIAzXp34Q5pO39RV6UIKS-WjKFLh6tLB3KLHxqTivKYmRTdnZEmm9xUZw5tFeZ5YakHpd0jF3DU";

    private String currentChannelUrl;
    private boolean wasPlayingBeforePause = false;

    private boolean isFullscreen = false;
    private int originalOrientation = android.content.res.Configuration.ORIENTATION_UNDEFINED;
    private boolean isFirstLoad = true;
    private final Handler hideControlsHandler = new Handler(Looper.getMainLooper());
    private final Runnable hideControlsRunnable = () -> {
        if (binding.plyrController.getRoot().getVisibility() == View.VISIBLE) {
            binding.plyrController.getRoot().animate().alpha(0f).setDuration(300).withEndAction(() -> {
                binding.plyrController.getRoot().setVisibility(View.GONE);
                binding.playerLogo.setVisibility(View.GONE);
            }).start();
        }
    };
    private static final long CONTROLS_HIDE_TIMEOUT = 5000;

    private final Handler searchHideHandler = new Handler(Looper.getMainLooper());
    private final Runnable searchHideRunnable = () -> {
        // Only reset text and hide container on phone (where sidebar is null)
        if (binding.sidebar == null) {
            if (binding.searchBoxContainer.getVisibility() == View.VISIBLE) {
                binding.searchInput.setText("");
                binding.searchBoxContainer.setVisibility(View.GONE);
                ToastUtils.showToast(this, "Search reset", false);
            }
        } else {
            // On TV/Tab, just reset text if it's been idle but keep it stable/visible
            if (!binding.searchInput.getText().toString().isEmpty()) {
                binding.searchInput.setText("");
                ToastUtils.showToast(this, "Search reset", false);
            }
        }
    };
    private static final long SEARCH_HIDE_TIMEOUT = 40000;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Full immersive for cutout/notch
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
            getWindow().getAttributes().layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }

        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        if (savedInstanceState != null) {
            currentChannelUrl = savedInstanceState.getString("current_url");
            isFullscreen = savedInstanceState.getBoolean("is_fullscreen", false);
            originalOrientation = savedInstanceState.getInt("original_orientation", android.content.res.Configuration.ORIENTATION_UNDEFINED);
        }

        // Safe Inset Handling (Mainly for mobile)
        ViewCompat.setOnApplyWindowInsetsListener(binding.mainContainer, (v, insets) -> {
            try {
                int top = insets.getInsets(WindowInsetsCompat.Type.systemBars()).top;
                if (top > 0 && binding.header != null) {
                    binding.header.setPadding(binding.header.getPaddingLeft(), top, 
                            binding.header.getPaddingRight(), binding.header.getPaddingBottom());
                }
            } catch (Exception ignored) {}
            return insets;
        });

        preferenceManager = new PreferenceManager(this);
        firebaseUtils = new FirebaseUtils();

        setupUI();
        initPlayer();
        loadLogos();
        setupInstallBanner();
        setupCopyright();
        fetchChannels();
        
        binding.channelList.requestFocus();
        binding.searchInput.clearFocus();

        if (isFullscreen) {
            applyFullscreenUI();
        }
    }

    private void setupCopyright() {
        if (binding.copyrightContainer != null) {
            binding.copyrightContainer.setOnClickListener(v -> {
                android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_VIEW, 
                    android.net.Uri.parse("https://t.me/shahriyartvbot"));
                startActivity(intent);
            });
        }
        
        binding.retryButton.setOnClickListener(v -> {
            if (isNetworkAvailable()) {
                binding.noInternetOverlay.setVisibility(View.GONE);
                fetchChannels();
            } else {
                ToastUtils.showToast(this, "Still no internet", false);
            }
        });
    }

    private boolean isNetworkAvailable() {
        android.net.ConnectivityManager cm = (android.net.ConnectivityManager) getSystemService(android.content.Context.CONNECTIVITY_SERVICE);
        if (cm == null) return true;
        
        try {
            android.net.NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
            return activeNetwork != null && activeNetwork.isConnectedOrConnecting();
        } catch (Exception e) {
            return true; // Fallback to true to allow attempt
        }
    }

    private void loadLogos() {
        Glide.with(this).load(LOGO_URL).into(binding.headerLogo);
        Glide.with(this).load(LOGO_URL).into(binding.playerLogo);
    }

    private void setupUI() {
        binding.channelList.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ChannelAdapter(this::playChannel);
        binding.channelList.setAdapter(adapter);

        if (binding.sidebar != null) {
            // TV/Tab Mode: Search bar is always stable/visible
            binding.searchBoxContainer.setVisibility(View.VISIBLE);
        }

        if (binding.searchBtn != null) {
            binding.searchBtn.setOnClickListener(v -> {
                boolean isVisible = binding.searchBoxContainer.getVisibility() == View.VISIBLE;
                binding.searchBoxContainer.setVisibility(isVisible ? View.GONE : View.VISIBLE);
                if (!isVisible) {
                    binding.searchInput.requestFocus();
                    resetSearchHideTimer();
                } else {
                    searchHideHandler.removeCallbacks(searchHideRunnable);
                }
            });
        }

        binding.searchInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                filterChannels(s.toString());
                resetSearchHideTimer();
            }
            @Override
            public void afterTextChanged(Editable s) {}
        });

        binding.searchInput.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) resetSearchHideTimer();
        });

        binding.searchInput.setOnClickListener(v -> resetSearchHideTimer());

        binding.channelList.addOnScrollListener(new androidx.recyclerview.widget.RecyclerView.OnScrollListener() {
            @Override
            public void onScrolled(@NonNull androidx.recyclerview.widget.RecyclerView recyclerView, int dx, int dy) {
                super.onScrolled(recyclerView, dx, dy);
                if (!recyclerView.canScrollVertically(1) && dy > 0) {
                    // Reset search if scrolled to bottom of results
                    if (!binding.searchInput.getText().toString().isEmpty()) {
                        binding.searchInput.setText("");
                        ToastUtils.showToast(MainActivity.this, "Search reset", false);
                    }
                }
                resetSearchHideTimer();
            }
        });
    }

    private void resetSearchHideTimer() {
        searchHideHandler.removeCallbacks(searchHideRunnable);
        if (binding.searchBoxContainer.getVisibility() == View.VISIBLE) {
            searchHideHandler.postDelayed(searchHideRunnable, SEARCH_HIDE_TIMEOUT);
        }
    }

    private void initPlayer() {
        // High-compatibility Default User Agent
        DataSource.Factory httpDataSourceFactory = new DefaultHttpDataSource.Factory()
                .setUserAgent("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36")
                .setAllowCrossProtocolRedirects(true);
        
        DataSource.Factory dataSourceFactory = new androidx.media3.datasource.DefaultDataSource.Factory(this, httpDataSourceFactory);

        DefaultMediaSourceFactory mediaSourceFactory = new DefaultMediaSourceFactory(this)
                .setDataSourceFactory(dataSourceFactory);

        androidx.media3.exoplayer.DefaultLoadControl loadControl = new androidx.media3.exoplayer.DefaultLoadControl.Builder()
                .setBufferDurationsMs(
                        30000, // Min buffer
                        60000, // Max buffer
                        2500,  // Buffer for playback
                        5000   // Buffer for playback after rebuffer
                ).build();

        player = new ExoPlayer.Builder(this)
                .setMediaSourceFactory(mediaSourceFactory)
                .setLoadControl(loadControl)
                .build();
        binding.playerView.setPlayer(player);
        
        View.OnClickListener playerToggleListener = v -> {
            if (binding.plyrController.getRoot().getVisibility() == View.VISIBLE) {
                hideControls();
            } else {
                showControls();
                resetHideControlsTimer();
            }
        };
        
        binding.playerTouchAnchor.setOnClickListener(playerToggleListener);
        binding.playerContainer.setOnClickListener(playerToggleListener);

        playerUIHelper = new PlayerUIHelper(binding.plyrController.getRoot(), player, this);
        
        player.addListener(new Player.Listener() {
            @Override
            public void onPlaybackStateChanged(int playbackState) {
                View loadingOverlay = binding.playerContainer.findViewById(R.id.loadingOverlay);
                View switchingAnim = loadingOverlay.findViewById(R.id.switchingAnimation);
                View bufferingSpinner = loadingOverlay.findViewById(R.id.bufferingSpinner);
                View bufferingCircle = loadingOverlay.findViewById(R.id.bufferingCircleAnimation);

                if (playbackState == Player.STATE_READY) {
                    isFirstLoad = false;
                    loadingOverlay.setVisibility(View.GONE);
                    loadingOverlay.setClickable(false);
                    loadingOverlay.setFocusable(false);
                    showControls();
                } else if (playbackState == Player.STATE_BUFFERING) {
                    loadingOverlay.setVisibility(View.VISIBLE);
                    loadingOverlay.setClickable(true);
                    loadingOverlay.setFocusable(true);
                    if (isFirstLoad) {
                        switchingAnim.setVisibility(View.VISIBLE);
                        bufferingCircle.setVisibility(View.GONE);
                    } else {
                        switchingAnim.setVisibility(View.GONE);
                        bufferingCircle.setVisibility(View.VISIBLE);
                    }
                    bufferingSpinner.setVisibility(View.GONE);
                    
                    // CRITICAL: Ensure controller is hidden during animation/buffering
                    binding.plyrController.getRoot().setVisibility(View.GONE);
                    binding.playerLogo.setVisibility(View.GONE);
                    hideControlsHandler.removeCallbacks(hideControlsRunnable);
                    
                    animateLoadingOverlay();
                }
                
                if (playbackState == Player.STATE_READY || playbackState == Player.STATE_BUFFERING) {
                    startProgressUpdate();
                }
            }

            @Override
            public void onIsPlayingChanged(boolean isPlaying) {
                if (isPlaying) {
                    View loadingOverlay = binding.playerContainer.findViewById(R.id.loadingOverlay);
                    if (loadingOverlay != null) loadingOverlay.setVisibility(View.GONE);
                    resetHideControlsTimer();
                } else {
                    showControls();
                    hideControlsHandler.removeCallbacks(hideControlsRunnable);
                }
            }

            @Override
            public void onPlayerError(@NonNull androidx.media3.common.PlaybackException error) {
                String errorDetails = error.getMessage();
                if (error.getCause() != null) {
                    errorDetails += " | Cause: " + error.getCause().getMessage();
                }
                android.util.Log.e("SHAHRIYAR_ERROR", "Playback Error: " + errorDetails, error);
                ToastUtils.showToast(MainActivity.this, "Error: " + error.getErrorCodeName(), true);
                playNextChannel();
            }
        });
    }

    private void animateLoadingOverlay() {
        View overlay = binding.playerContainer.findViewById(R.id.loadingOverlay);
        if (overlay == null || overlay.getVisibility() != View.VISIBLE) return;
        
        View switchingAnim = overlay.findViewById(R.id.switchingAnimation);
        View bufferingCircle = overlay.findViewById(R.id.bufferingCircleAnimation);

        if (switchingAnim != null && switchingAnim.getVisibility() == View.VISIBLE) {
            int[] ids = {R.id.letterS, R.id.letterH, R.id.letterA, R.id.letterH2, 
                        R.id.letterR, R.id.letterI, R.id.letterY, R.id.letterA2, R.id.letterR2};
            
            for (int i = 0; i < ids.length; i++) {
                final View view = overlay.findViewById(ids[i]);
                if (view != null && view.getAnimation() == null) {
                    AlphaAnimation anim = new AlphaAnimation(0.2f, 1.0f);
                    anim.setDuration(800);
                    anim.setStartOffset(i * 150);
                    anim.setRepeatMode(Animation.REVERSE);
                    anim.setRepeatCount(Animation.INFINITE);
                    view.startAnimation(anim);
                }
            }
        }

        if (bufferingCircle != null && bufferingCircle.getVisibility() == View.VISIBLE) {
            int[] circleIds = {R.id.circle_letterS, R.id.circle_letterH, R.id.circle_letterA, R.id.circle_letterH2, 
                               R.id.circle_letterR, R.id.circle_letterI, R.id.circle_letterY, R.id.circle_letterA2, R.id.circle_letterR2};
            
            float radius = 120f;
            for (int i = 0; i < circleIds.length; i++) {
                final View view = overlay.findViewById(circleIds[i]);
                if (view != null) {
                    double angle = Math.toRadians((360.0 / circleIds.length) * i);
                    float x = (float) (Math.cos(angle) * radius);
                    float y = (float) (Math.sin(angle) * radius);
                    view.setTranslationX(x);
                    view.setTranslationY(y);

                    if (view.getAnimation() == null) {
                        AlphaAnimation anim = new AlphaAnimation(0.3f, 1.0f);
                        anim.setDuration(600);
                        anim.setStartOffset(i * 100);
                        anim.setRepeatMode(Animation.REVERSE);
                        anim.setRepeatCount(Animation.INFINITE);
                        view.startAnimation(anim);
                    }
                }
            }
            
            if (bufferingCircle.getAnimation() == null) {
                RotateAnimation rotate = new RotateAnimation(0, 360, 
                        Animation.RELATIVE_TO_SELF, 0.5f, Animation.RELATIVE_TO_SELF, 0.5f);
                rotate.setDuration(3000);
                rotate.setRepeatCount(Animation.INFINITE);
                rotate.setInterpolator(new android.view.animation.LinearInterpolator());
                bufferingCircle.startAnimation(rotate);
            }
        }
    }

    private boolean isProgressUpdating = false;

    private void startProgressUpdate() {
        if (isProgressUpdating) return;
        isProgressUpdating = true;
        
        binding.getRoot().post(new Runnable() {
            @Override
            public void run() {
                if (player != null) {
                    if (player.isPlaying()) {
                        playerUIHelper.updateProgress();
                        View loadingOverlay = binding.playerContainer.findViewById(R.id.loadingOverlay);
                        if (loadingOverlay != null && loadingOverlay.getVisibility() == View.VISIBLE) {
                            loadingOverlay.setVisibility(View.GONE);
                        }
                    }
                    binding.getRoot().postDelayed(this, 1000);
                } else {
                    isProgressUpdating = false;
                }
            }
        });
    }

    private void setupInstallBanner() {
        firebaseUtils.checkUpdate((latestVersion, updateUrl) -> {
            try {
                long currentVersion = getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
                if (latestVersion > currentVersion) {
                    runOnUiThread(() -> {
                        binding.installBanner.getRoot().setVisibility(View.VISIBLE);
                        binding.installBanner.bannerTitle.setText("NEW VERSION AVAILABLE");
                        binding.installBanner.bannerMessage.setText("Version " + latestVersion + " is ready!");
                        binding.installBanner.btnUpdate.setText("Download & Update");
                        
                        binding.installBanner.btnUpdate.setOnClickListener(v -> {
                            binding.installBanner.btnUpdate.setEnabled(false);
                            binding.installBanner.btnUpdate.setText("Downloading...");
                            downloadAndInstallApk(updateUrl);
                        });
                    });
                }
            } catch (Exception ignored) {}
        });

        binding.installBanner.btnCloseBanner.setOnClickListener(v -> {
            binding.installBanner.getRoot().setVisibility(View.GONE);
        });
    }

    private void downloadAndInstallApk(String url) {
        new Thread(() -> {
            try {
                Request request = new Request.Builder().url(url).build();
                Response response = client.newCall(request).execute();
                if (!response.isSuccessful()) throw new IOException("Download failed");

                File apkFile = new File(getExternalFilesDir(null), "update.apk");
                try (InputStream is = response.body().byteStream();
                     FileOutputStream fos = new FileOutputStream(apkFile)) {
                    byte[] buffer = new byte[4096];
                    int read;
                    while ((read = is.read(buffer)) != -1) {
                        fos.write(buffer, 0, read);
                    }
                }

                runOnUiThread(() -> installApk(apkFile));
            } catch (Exception e) {
                runOnUiThread(() -> {
                    ToastUtils.showToast(this, "Update failed: " + e.getMessage(), true);
                    binding.installBanner.btnUpdate.setEnabled(true);
                    binding.installBanner.btnUpdate.setText("Retry Update");
                });
            }
        }).start();
    }

    private void installApk(File file) {
        Uri apkUri = FileProvider.getUriForFile(this, getPackageName() + ".provider", file);
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }

    private void fetchChannels() {
        if (!isNetworkAvailable()) {
            binding.noInternetOverlay.setVisibility(View.VISIBLE);
            return;
        }
        binding.noInternetOverlay.setVisibility(View.GONE);

        // Clear list and show loading state
        adapter.setChannels(new ArrayList<>());
        binding.totalChannelsBadge.setText("0");

        Request request = new Request.Builder()
                .url(M3U_URL)
                .addHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
                .addHeader("Accept", "*/*")
                .addHeader("Connection", "keep-alive")
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                runOnUiThread(() -> {
                    String errorMsg = e.getMessage() != null ? e.getMessage() : "Unknown Error";
                    ToastUtils.showToast(MainActivity.this, "SOURCE ERROR: " + errorMsg, true);
                    // If it's an SSL error, it might be the TV date/time
                    if (errorMsg.contains("SSL") || errorMsg.contains("cert")) {
                        ToastUtils.showToast(MainActivity.this, "Check TV Date & Time Settings", true);
                    }
                });
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (!response.isSuccessful()) {
                    runOnUiThread(() -> ToastUtils.showToast(MainActivity.this, "HTTP ERROR: " + response.code(), true));
                    return;
                }
                
                okhttp3.ResponseBody body = response.body();
                if (body == null) {
                    runOnUiThread(() -> ToastUtils.showToast(MainActivity.this, "EMPTY M3U DATA", true));
                    return;
                }

                String content = body.string();
                // Move parsing to background thread for smoothness
                new Thread(() -> {
                    try {
                        List<Channel> parsedChannels = M3UParser.parse(content);
                        runOnUiThread(() -> {
                            allChannels = parsedChannels;
                            if (allChannels == null || allChannels.isEmpty()) {
                                ToastUtils.showToast(MainActivity.this, "NO CHANNELS FOUND IN M3U", true);
                            } else {
                                adapter.setChannels(allChannels);
                                binding.totalChannelsBadge.setText(String.valueOf(allChannels.size()));
                                
                                if (currentChannelUrl != null) {
                                    for (Channel c : allChannels) {
                                        if (c.getUrl().equals(currentChannelUrl)) {
                                            playChannel(c);
                                            break;
                                        }
                                    }
                                } else {
                                    if (!allChannels.isEmpty()) playChannel(allChannels.get(0));
                                }
                            }
                        });
                    } catch (Exception e) {
                        runOnUiThread(() -> ToastUtils.showToast(MainActivity.this, "PARSING ERROR: " + e.getMessage(), true));
                    }
                }).start();
            }
        });
    }

    private void playChannel(Channel channel) {
        currentChannelUrl = channel.getUrl();
        // Auto-scroll logic
        if (scrollRunnable != null) scrollHandler.removeCallbacks(scrollRunnable);
        scrollRunnable = () -> {
            int pos = -1;
            for (int i = 0; i < adapter.getItemCount(); i++) {
                Object item = adapter.getItem(i);
                if (item instanceof Channel && ((Channel) item).getUrl().equals(channel.getUrl())) {
                    pos = i;
                    break;
                }
            }
            if (pos != -1) {
                binding.channelList.smoothScrollToPosition(pos);
                int finalPos = pos;
                scrollHandler.postDelayed(() -> {
                    LinearLayoutManager layoutManager = (LinearLayoutManager) binding.channelList.getLayoutManager();
                    if (layoutManager != null) layoutManager.scrollToPositionWithOffset(finalPos, 0);
                }, 500);
            }
        };
        scrollHandler.postDelayed(scrollRunnable, 30000);

        String url = channel.getUrl();
        // TS Optimization Logic
        if (url.toLowerCase().endsWith(".ts") && !url.contains("stv.up.railway.app")) {
            url = "https://stv.up.railway.app/stream?url=" + url;
        }

        adapter.setActiveChannel(channel.getUrl());
        binding.nowPlayingFooter.setVisibility(View.VISIBLE);
        binding.npName.setText(channel.getName());
        binding.npCategory.setText(channel.getGroup());

        Glide.with(this)
                .load(channel.getLogo())
                .placeholder(R.drawable.placeholder_logo)
                .into(binding.npLogo);
        
        // Show SHAHRIYAR animation (Switching)
        View loadingOverlay = binding.playerContainer.findViewById(R.id.loadingOverlay);
        View switchingAnim = loadingOverlay.findViewById(R.id.switchingAnimation);
        View bufferingSpinner = loadingOverlay.findViewById(R.id.bufferingSpinner);
        View bufferingCircle = loadingOverlay.findViewById(R.id.bufferingCircleAnimation);
        
        loadingOverlay.setVisibility(View.VISIBLE);
        switchingAnim.setVisibility(View.VISIBLE);
        bufferingSpinner.setVisibility(View.GONE);
        bufferingCircle.setVisibility(View.GONE);
        
        binding.plyrController.getRoot().setVisibility(View.GONE);
        isFirstLoad = true;
        animateLoadingOverlay();

        // Detect Engine Type
        String engine = "HLS";
        if (url.toLowerCase().contains(".mpd") || (channel.getManifestType() != null && channel.getManifestType().equalsIgnoreCase("mpd"))) engine = "DASH";
        else if (url.toLowerCase().contains(".ts") || url.contains("stream?url=")) engine = "TS";
        else if (url.toLowerCase().contains(".mp4")) engine = "MP4";
        else if (url.contains("master.m3u8")) engine = "PROXY";
        
        android.util.Log.d("SHAHRIYAR_PLAY", "Playing: " + channel.getName() + " | URL: " + url);
        if (channel.getHeaders() != null) {
            android.util.Log.d("SHAHRIYAR_PLAY", "Headers: " + channel.getHeaders().toString());
        }

        MediaItem.Builder mediaItemBuilder = new MediaItem.Builder()
                .setUri(url)
                .setMediaId(channel.getId());

        // Handle Manifest Type or URL extension
        String mimeType = null;
        if (channel.getManifestType() != null) {
            String mt = channel.getManifestType().toLowerCase();
            if (mt.equals("mpd")) mimeType = androidx.media3.common.MimeTypes.APPLICATION_MPD;
            else if (mt.equals("m3u8") || mt.equals("hls")) mimeType = androidx.media3.common.MimeTypes.APPLICATION_M3U8;
        }
        
        if (mimeType == null) {
            if (url.toLowerCase().contains(".mpd")) mimeType = androidx.media3.common.MimeTypes.APPLICATION_MPD;
            else if (url.toLowerCase().contains(".m3u8")) mimeType = androidx.media3.common.MimeTypes.APPLICATION_M3U8;
        }
        
        if (mimeType != null) {
            mediaItemBuilder.setMimeType(mimeType);
        }

        // Handle DRM
        if (channel.getDrmScheme() != null && channel.getLicenseUrl() != null) {
            java.util.UUID drmUuid = null;
            if (channel.getDrmScheme().equalsIgnoreCase("clearkey")) {
                drmUuid = androidx.media3.common.C.CLEARKEY_UUID;
            } else if (channel.getDrmScheme().equalsIgnoreCase("widevine")) {
                drmUuid = androidx.media3.common.C.WIDEVINE_UUID;
            }

            if (drmUuid != null) {
                MediaItem.DrmConfiguration.Builder drmBuilder = new MediaItem.DrmConfiguration.Builder(drmUuid);
                
                String license = channel.getLicenseUrl();
                if (license.contains(":") && !license.startsWith("http")) {
                    String dataUri = convertKidKeyToDataUri(license);
                    if (dataUri != null) {
                        drmBuilder.setLicenseUri(Uri.parse(dataUri));
                        android.util.Log.d("SHAHRIYAR_DRM", "ClearKey Local: " + license);
                    }
                } else {
                    drmBuilder.setLicenseUri(Uri.parse(license));
                    android.util.Log.d("SHAHRIYAR_DRM", "License URL: " + license);
                }
                
                drmBuilder.setMultiSession(true);
                
                if (channel.getHeaders() != null && !channel.getHeaders().isEmpty()) {
                    drmBuilder.setLicenseRequestHeaders(channel.getHeaders());
                }
                
                mediaItemBuilder.setDrmConfiguration(drmBuilder.build());
                android.util.Log.d("SHAHRIYAR_DRM", "Applied DRM: " + channel.getDrmScheme() + " for " + channel.getName());
            }
        }

        MediaItem mediaItem = mediaItemBuilder.build();

        // Inject headers per channel (Critical for OTT/Toffee/Protected sources)
        if (channel.getHeaders() != null && !channel.getHeaders().isEmpty()) {
            java.util.Map<String, String> headers = new java.util.HashMap<>(channel.getHeaders());
            String userAgent = headers.remove("User-Agent");
            
            DefaultHttpDataSource.Factory httpDataSourceFactory = new DefaultHttpDataSource.Factory()
                    .setDefaultRequestProperties(headers)
                    .setAllowCrossProtocolRedirects(true);
            
            if (userAgent != null) {
                httpDataSourceFactory.setUserAgent(userAgent);
            }
            
            MediaSource mediaSource = new DefaultMediaSourceFactory(this)
                    .setDataSourceFactory(httpDataSourceFactory)
                    .createMediaSource(mediaItem);
            
            player.setMediaSource(mediaSource);
        } else {
            player.setMediaItem(mediaItem);
        }

        player.prepare();
        player.play();
    }

    private void filterChannels(String query) {
        List<Channel> filtered = new ArrayList<>();
        for (Channel c : allChannels) {
            if (c.getName().toLowerCase().contains(query.toLowerCase()) ||
                c.getGroup().toLowerCase().contains(query.toLowerCase())) {
                filtered.add(c);
            }
        }
        adapter.setChannels(filtered);
    }

    private void playNextChannel() {
        if (allChannels.isEmpty()) return;
        int currentIndex = -1;
        for (int i = 0; i < allChannels.size(); i++) {
            if (allChannels.get(i).getUrl().equals(adapter.getActiveChannelUrl())) {
                currentIndex = i;
                break;
            }
        }
        int nextIndex = (currentIndex + 1) % allChannels.size();
        playChannel(allChannels.get(nextIndex));
    }

    private void playPreviousChannel() {
        if (allChannels.isEmpty()) return;
        int currentIndex = -1;
        for (int i = 0; i < allChannels.size(); i++) {
            if (allChannels.get(i).getUrl().equals(adapter.getActiveChannelUrl())) {
                currentIndex = i;
                break;
            }
        }
        int prevIndex = (currentIndex - 1 + allChannels.size()) % allChannels.size();
        playChannel(allChannels.get(prevIndex));
    }

    @Override
    public void onFullscreenClick() {
        if (binding.sidebar != null) {
            if (isFullscreen) restoreNormalUI();
            else applyFullscreenUI();
        } else {
            if (getResources().getConfiguration().orientation == Configuration.ORIENTATION_PORTRAIT) {
                setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
            } else {
                setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
            }
        }
    }

    private void applyFullscreenUI() {
        isFullscreen = true;
        if (binding.sidebar != null) binding.sidebar.setVisibility(View.GONE);
        binding.header.setVisibility(View.GONE);
        binding.searchBoxContainer.setVisibility(View.GONE);
        binding.nowPlayingFooter.setVisibility(View.GONE);
        if (binding.installBanner != null) binding.installBanner.getRoot().setVisibility(View.GONE);
        binding.channelList.setVisibility(View.GONE);
        if (binding.copyrightContainer != null) binding.copyrightContainer.setVisibility(View.GONE);

        androidx.constraintlayout.widget.ConstraintLayout.LayoutParams params =
                (androidx.constraintlayout.widget.ConstraintLayout.LayoutParams) binding.playerContainer.getLayoutParams();
        params.width = 0;
        params.height = 0;
        params.topToTop = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        params.bottomToBottom = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        params.startToStart = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        params.endToEnd = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        params.topToBottom = -1;
        params.bottomToTop = -1;
        params.startToEnd = -1;
        params.endToStart = -1;
        params.dimensionRatio = null;
        binding.playerContainer.setLayoutParams(params);

        // Modern Immersive Mode
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN);
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            getWindow().getAttributes().layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }

        resetHideControlsTimer();
    }

    private void restoreNormalUI() {
        isFullscreen = false;
        if (binding.sidebar != null) {
            binding.sidebar.setVisibility(View.VISIBLE);
            binding.searchBoxContainer.setVisibility(View.VISIBLE);
        }
        binding.header.setVisibility(View.VISIBLE);
        binding.channelList.setVisibility(View.VISIBLE);
        if (binding.copyrightContainer != null) binding.copyrightContainer.setVisibility(View.VISIBLE);
        
        // Only toggle search container based on content if we are on phone
        if (binding.sidebar == null) {
            if (!binding.searchInput.getText().toString().isEmpty()) {
                binding.searchBoxContainer.setVisibility(View.VISIBLE);
            } else {
                binding.searchBoxContainer.setVisibility(View.GONE);
            }
        }

        if (currentChannelUrl != null) binding.nowPlayingFooter.setVisibility(View.VISIBLE);

        androidx.constraintlayout.widget.ConstraintLayout.LayoutParams params =
                (androidx.constraintlayout.widget.ConstraintLayout.LayoutParams) binding.playerContainer.getLayoutParams();

        if (binding.sidebar != null) {
            params.width = 0;
            params.height = 0;
            params.startToStart = -1;
            params.startToEnd = R.id.sidebar;
            params.endToEnd = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
            params.topToTop = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
            params.bottomToBottom = -1;
            params.bottomToTop = R.id.nowPlayingFooter;
            params.dimensionRatio = null;
        } else {
            params.width = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.MATCH_PARENT;
            params.height = 0;
            params.topToTop = -1;
            params.topToBottom = R.id.searchBoxContainer;
            params.bottomToBottom = -1;
            params.startToStart = -1;
            params.endToEnd = -1;
            params.dimensionRatio = "16:9";
        }
        binding.playerContainer.setLayoutParams(params);

        // Restore System UI
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(true);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.show(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            getWindow().getAttributes().layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_DEFAULT;
        }

        resetHideControlsTimer();
    }

    @Override
    public void onBackPressed() {
        if (isFullscreen) {
            if (binding.sidebar != null) {
                restoreNormalUI();
            } else {
                setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
            }
            return;
        }
        if (System.currentTimeMillis() - lastBackPressedTime < 2000) {
            super.onBackPressed();
            return;
        }
        lastBackPressedTime = System.currentTimeMillis();
        ToastUtils.showToast(this, "Press back again to exit", false);
    }

    @Override
    public void onUserInteraction() {
        if (binding.plyrController.getRoot().getVisibility() == View.VISIBLE) {
            resetHideControlsTimer();
        }
    }

    private void showControls() {
        View loadingOverlay = binding.playerContainer.findViewById(R.id.loadingOverlay);
        if (loadingOverlay != null && loadingOverlay.getVisibility() == View.VISIBLE) return;
        if (binding.plyrController.getRoot().getVisibility() == View.VISIBLE) return;

        binding.plyrController.getRoot().animate().cancel();
        binding.plyrController.getRoot().setAlpha(0f);
        binding.plyrController.getRoot().setVisibility(View.VISIBLE);
        binding.plyrController.getRoot().animate().alpha(1f).setDuration(300).start();
        binding.playerLogo.setVisibility(View.VISIBLE);
        resetHideControlsTimer();
    }

    private void hideControls() {
        binding.plyrController.getRoot().animate().cancel();
        binding.plyrController.getRoot().animate().alpha(0f).setDuration(300).withEndAction(() -> {
            binding.plyrController.getRoot().setVisibility(View.GONE);
            binding.playerLogo.setVisibility(View.GONE);
        }).start();
        hideControlsHandler.removeCallbacks(hideControlsRunnable);
    }

    private void resetHideControlsTimer() {
        hideControlsHandler.removeCallbacks(hideControlsRunnable);
        if (player != null && player.isPlaying()) {
            hideControlsHandler.postDelayed(hideControlsRunnable, CONTROLS_HIDE_TIMEOUT);
        }
    }

    @Override
    public void onSettingsClick() {
        Tracks tracks = player.getCurrentTracks();
        PopupMenu popup = new PopupMenu(this, binding.plyrController.btnSettings);
        
        int trackIndex = 0;
        for (Tracks.Group group : tracks.getGroups()) {
            if (group.getType() == androidx.media3.common.C.TRACK_TYPE_VIDEO) {
                for (int i = 0; i < group.length; i++) {
                    String label = group.getTrackFormat(i).height + "p";
                    MenuItem item = popup.getMenu().add(0, trackIndex, 0, label);
                    int finalI = i;
                    item.setOnMenuItemClickListener(it -> {
                        player.setTrackSelectionParameters(
                                player.getTrackSelectionParameters()
                                        .buildUpon()
                                        .setOverrideForType(new TrackSelectionOverride(group.getMediaTrackGroup(), finalI))
                                        .build());
                        return true;
                    });
                    trackIndex++;
                }
            }
        }
        popup.show();
    }

    private void showVolumeOverlay(float volume) {
        int percent = Math.round(volume * 100);
        ToastUtils.showToast(this, "Volume: " + percent + "%", false);
        // You could also inflate a custom large view here if needed
    }

    @Override
    public boolean dispatchKeyEvent(android.view.KeyEvent event) {
        int keyCode = event.getKeyCode();
        if (keyCode == android.view.KeyEvent.KEYCODE_ENTER || keyCode == android.view.KeyEvent.KEYCODE_DPAD_CENTER) {
            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN) {
                if (event.getRepeatCount() == 0) {
                    event.startTracking();
                } else if (event.isLongPress() && !isFullscreen) {
                    setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
                    return true;
                }
            } else if (event.getAction() == android.view.KeyEvent.ACTION_UP) {
                if (isFullscreen && !event.isCanceled()) {
                    if (player.isPlaying()) player.pause();
                    else player.play();
                    return true;
                }
            }
        }
        
        if (isFullscreen && (keyCode == android.view.KeyEvent.KEYCODE_DPAD_LEFT || keyCode == android.view.KeyEvent.KEYCODE_DPAD_RIGHT)) {
            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN) {
                if (event.getRepeatCount() == 0) event.startTracking();
                else if (event.isLongPress()) {
                    if (player.getVolume() > 0) {
                        player.setVolume(0f);
                        ToastUtils.showToast(this, "Muted", false);
                    } else {
                        player.setVolume(1f);
                        ToastUtils.showToast(this, "Unmuted", false);
                    }
                    return true;
                }
            }
        }

        return super.dispatchKeyEvent(event);
    }

    @Override
    public boolean onKeyDown(int keyCode, android.view.KeyEvent event) {
        if (binding.searchInput.hasFocus()) {
            if (keyCode == android.view.KeyEvent.KEYCODE_BACK) {
                binding.searchInput.clearFocus();
                binding.channelList.requestFocus();
                return true;
            }
            return super.onKeyDown(keyCode, event);
        }

        if (keyCode == android.view.KeyEvent.KEYCODE_ENTER || keyCode == android.view.KeyEvent.KEYCODE_DPAD_CENTER ||
                keyCode == android.view.KeyEvent.KEYCODE_DPAD_UP || keyCode == android.view.KeyEvent.KEYCODE_DPAD_DOWN ||
                keyCode == android.view.KeyEvent.KEYCODE_DPAD_LEFT || keyCode == android.view.KeyEvent.KEYCODE_DPAD_RIGHT) {
            event.startTracking();
        }

        if (isFullscreen) {
            showControls();
            switch (keyCode) {
                case android.view.KeyEvent.KEYCODE_DPAD_LEFT:
                    float volL = Math.max(0, player.getVolume() - 0.05f);
                    player.setVolume(volL);
                    showVolumeOverlay(volL);
                    return true;
                case android.view.KeyEvent.KEYCODE_DPAD_RIGHT:
                    float volR = Math.min(1, player.getVolume() + 0.05f);
                    player.setVolume(volR);
                    showVolumeOverlay(volR);
                    return true;
                case android.view.KeyEvent.KEYCODE_DPAD_UP:
                    playPreviousChannel();
                    return true;
                case android.view.KeyEvent.KEYCODE_DPAD_DOWN:
                    playNextChannel();
                    return true;
                case android.view.KeyEvent.KEYCODE_BACK:
                    if (binding.sidebar != null) {
                        restoreNormalUI();
                    } else {
                        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
                    }
                    return true;
            }
            return super.onKeyDown(keyCode, event);
        }

        // Navigation for Normal Mode
        if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_RIGHT) {
            View focused = getCurrentFocus();
            if (binding.sidebar != null && focused != null && 
                (focused == binding.channelList || focused.getParent() == binding.channelList || focused == binding.searchInput)) {
                showControls();
                binding.plyrController.exoPlayPause.requestFocus();
                return true;
            }
        }

        if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_LEFT) {
            View focused = getCurrentFocus();
            if (focused != null && focused.getParent() != null && focused.getParent().getParent() == binding.plyrController.getRoot()) {
                binding.channelList.requestFocus();
                return true;
            }
        }

        if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_UP || keyCode == android.view.KeyEvent.KEYCODE_DPAD_DOWN) {
            if (event.getRepeatCount() > 0 && event.getRepeatCount() % 10 == 0) {
                if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_UP) playPreviousChannel();
                else playNextChannel();
                return true;
            }
        }

        return super.onKeyDown(keyCode, event);
    }

    @Override
    public void onConfigurationChanged(@NonNull Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        if (newConfig.orientation == Configuration.ORIENTATION_LANDSCAPE) {
            applyFullscreenUI();
        } else {
            restoreNormalUI();
        }
    }

    @Override
    protected void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putString("current_url", currentChannelUrl);
        outState.putBoolean("is_fullscreen", isFullscreen);
        outState.putInt("original_orientation", originalOrientation);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (player != null) {
            wasPlayingBeforePause = player.isPlaying();
            player.pause();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (player != null && wasPlayingBeforePause) {
            player.play();
        }
        
        if (!isNetworkAvailable()) {
            binding.noInternetOverlay.setVisibility(View.VISIBLE);
        } else {
            binding.noInternetOverlay.setVisibility(View.GONE);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        searchHideHandler.removeCallbacks(searchHideRunnable);
        hideControlsHandler.removeCallbacks(hideControlsRunnable);
        if (player != null) {
            player.release();
            player = null;
        }
        firebaseUtils.cleanup();
    }

    private String convertKidKeyToDataUri(String kidKey) {
        try {
            String[] parts = kidKey.split(":");
            if (parts.length != 2) return null;
            
            String kidHex = parts[0].trim();
            String keyHex = parts[1].trim();
            
            String kidB64 = hexToBase64Url(kidHex);
            String keyB64 = hexToBase64Url(keyHex);
            
            String json = "{\"keys\":[{\"kty\":\"oct\",\"k\":\"" + keyB64 + "\",\"kid\":\"" + kidB64 + "\"}],\"type\":\"temporary\"}";
            return "data:application/json;base64," + android.util.Base64.encodeToString(json.getBytes(), android.util.Base64.NO_WRAP);
        } catch (Exception e) {
            return null;
        }
    }

    private String hexToBase64Url(String hex) {
        byte[] data = new byte[hex.length() / 2];
        for (int i = 0; i < data.length; i++) {
            data[i] = (byte) ((Character.digit(hex.charAt(i * 2), 16) << 4)
                                 + Character.digit(hex.charAt(i * 2 + 1), 16));
        }
        return android.util.Base64.encodeToString(data, android.util.Base64.URL_SAFE | android.util.Base64.NO_PADDING | android.util.Base64.NO_WRAP);
    }
}
