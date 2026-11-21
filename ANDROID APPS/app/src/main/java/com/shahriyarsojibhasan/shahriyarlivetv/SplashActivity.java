package com.shahriyarsojibhasan.shahriyarlivetv;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import androidx.appcompat.app.AppCompatActivity;
import androidx.media3.common.util.UnstableApi;

@UnstableApi
public class SplashActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        animateLoading();

        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            startActivity(new Intent(SplashActivity.this, MainActivity.class));
            finish();
        }, 3000);
    }

    private void animateLoading() {
        int[] ids = {R.id.letterS, R.id.letterH, R.id.letterA, R.id.letterH2, 
                    R.id.letterR, R.id.letterI, R.id.letterY, R.id.letterA2, R.id.letterR2};
        
        for (int i = 0; i < ids.length; i++) {
            final View view = findViewById(ids[i]);
            if (view != null) {
                AlphaAnimation anim = new AlphaAnimation(0.2f, 1.0f);
                anim.setDuration(800);
                anim.setStartOffset(i * 150); // Increased offset for better visual wave
                anim.setRepeatMode(Animation.REVERSE);
                anim.setRepeatCount(Animation.INFINITE);
                view.startAnimation(anim);
            }
        }
    }
}
